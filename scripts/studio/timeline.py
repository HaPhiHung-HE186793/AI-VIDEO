"""Tính timeline dựng phim từ manifest.

Quy tắc:
- Audio và video của 1 shot luôn dùng CÙNG cửa sổ [in, out] → không thể lệch tiếng/hình.
- Ưu tiên điểm cắt: edit_in/edit_out thủ công > độ dài lời dẫn ngoài (voiceover) > vùng thoại ước lượng > cả clip.
- Chuyển cảnh mặc định là hard cut; dissolve chỉ khi shot đặt `transition_out: "dissolve"`.
- Shot nối liền cùng cảnh (INTRA_SCENE_CONTINUE / extend): tìm frame của shot A khớp nhất với frame đầu shot B
  để cắt, shot B bắt đầu từ 0.
"""

from pathlib import Path

from . import audio as au
from . import beats as bt
from . import manifest as mf
from . import media

CUT, DISSOLVE = "cut", "dissolve"


def _find_seam(clip_a: Path, t_min: float, clip_b: Path, b_in: float = 0.0, t_max: float = None) -> tuple:
    """Thời điểm trong A (t_min ≤ t ≤ t_max) có frame giống frame đầu của B nhất. Trả về (t_cut, l1_diff)."""
    import numpy as np

    cv2 = media.cv2_module()
    fb, _ = media.read_frame_at(clip_b, b_in)
    gb = cv2.cvtColor(cv2.resize(fb, (320, 180)), cv2.COLOR_BGR2GRAY).astype(np.int16)
    fps, frames = media.read_gray_frames(clip_a)
    start = max(0, int(t_min * fps))
    stop = min(len(frames), int(t_max * fps)) if t_max is not None else len(frames)
    if stop <= start:
        stop = len(frames)
    best_i, best_d = stop - 1, 1e9
    for i in range(start, stop):
        d = float(np.mean(np.abs(frames[i].astype(np.int16) - gb)))
        if d < best_d:
            best_i, best_d = i, d
    # Cắt SAU frame khớp nhất để frame đó là frame cuối của A.
    return round((best_i + 1) / fps, 3), round(best_d, 2)


def _is_continuation(prev: dict, cur: dict) -> bool:
    return prev.get("transition_to_next") == "INTRA_SCENE_CONTINUE" or (
        cur.get("generation_mode") == "extend" and cur.get("extends") == prev.get("shot_id")
    )


def _is_auto_edit(s: dict) -> bool:
    """True nếu edit_in/edit_out trên shot là kết quả tự động từ `auto-select` (chưa bị đạo diễn khóa/sửa tay)."""
    if s.get("lock_edit"):
        return False
    auto = s.get("auto_selection")
    if not isinstance(auto, dict) or ("edit_in" not in auto and "edit_out" not in auto):
        return False
    return s.get("edit_in") == auto.get("edit_in") and s.get("edit_out") == auto.get("edit_out")


def _fit_in_window(w0: float, w1: float, need: float) -> tuple:
    """Đặt đoạn dài `need` vào giữa cửa sổ sạch [w0, w1]."""
    length = min(max(0.0, w1 - w0), need)
    tin = round(w0 + (w1 - w0 - length) / 2, 2)
    return tin, round(tin + length, 2)


def compute(proj_dir: Path, project: dict, cfg: dict, include_pending: bool = False) -> list:
    ed = cfg["editorial"]
    fps = cfg["output"]["fps"]
    segs = []
    for s in mf.ordered_shots(project):
        clip = mf.clip_path(proj_dir, s)
        if not clip.exists() or s.get("exclude_from_edit"):
            continue
        if not include_pending and s.get("status") == mf.STATUS_QA_FAIL and not s.get("force_include"):
            continue
        info = media.probe(clip)
        dur = info["duration"]
        audio = mf.shot_audio(s)
        seg = {"shot_id": s["shot_id"], "clip": clip, "has_audio": info["has_audio"], "clip_duration": dur,
               "vo_path": None, "vo_offset": 0.0, "vo_duration": 0.0, "speech": None, "notes": [],
               "subtitle": audio.get("line", "") if audio["mode"] != "sfx_only" and s.get("subtitle", True) else ""}

        vo_rel = s.get("voiceover_path")
        vo = proj_dir / vo_rel if vo_rel else None
        has_vo = audio["mode"] == "voiceover_external" and vo and vo.exists()
        if has_vo:
            # Lời dẫn luôn được đặt lên shot, kể cả khi đạo diễn chỉnh tay cửa sổ hình (edit_in/edit_out).
            vo_dur = au.wav_duration(vo)
            seg.update(vo_path=vo, vo_offset=float(s.get("vo_offset", ed["vo_pre_roll_sec"])), vo_duration=vo_dur)

        auto_edit = _is_auto_edit(s)
        win = (s.get("auto_selection") or {}).get("window") if auto_edit else None
        w0 = max(0.0, float(win[0])) if win else 0.0
        w1 = min(dur, float(win[1])) if win else dur
        seg["clean_window"] = (w0, w1)

        if ("edit_in" in s or "edit_out" in s) and not auto_edit:
            tin, tout, source = float(s.get("edit_in", 0.0)), float(s.get("edit_out", dur)), "manual"
            if has_vo and seg["vo_offset"] + seg["vo_duration"] > tout - tin + 0.01:
                seg["notes"].append(f"Lời dẫn ({seg['vo_duration']:.2f}s) dài hơn cửa sổ hình {tout - tin:.2f}s — lời sẽ tràn sang shot sau.")
        elif has_vo:
            need = seg["vo_offset"] + seg["vo_duration"] + ed["vo_post_roll_sec"]
            if auto_edit:
                tin, tout = _fit_in_window(w0, w1, need)
            else:
                tin, tout = 0.0, min(dur, need)
            if need > (w1 - w0 if auto_edit else dur) + 0.01:
                seg["notes"].append(f"Lời dẫn ({seg['vo_duration']:.2f}s) dài hơn phần hình còn lại — rút gọn câu hoặc Extend clip.")
            source = "voiceover"
        elif audio["mode"] in ("veo_dialogue", "veo_narration"):
            sw = au.speech_window(clip)
            seg["speech"] = sw
            tin = max(w0, sw["start"] - ed["speech_pad_head_sec"]) if segs else w0
            tout = min(w1, sw["end"] + ed["speech_pad_tail_sec"])
            source = "speech" if sw["reliable"] else "speech_unreliable"
            if not sw["reliable"]:
                if auto_edit:
                    tin, tout = float(s.get("edit_in", w0)), float(s.get("edit_out", w1))
                seg["notes"].append("Không tách rõ thoại khỏi nền — nên đặt edit_in/edit_out thủ công.")
        elif s.get("beat") in bt.beats_by_id(project):
            share = bt.shot_need(proj_dir, project, s, cfg)
            if auto_edit and (float(s.get("edit_out", w1)) - float(s.get("edit_in", w0))) >= share - 0.02:
                tin, tout = float(s.get("edit_in", w0)), float(s.get("edit_out", w1))
            else:
                tin, tout = _fit_in_window(w0, w1, share)
            source = "beat_share"
        elif auto_edit:
            tin, tout, source = float(s.get("edit_in", w0)), float(s.get("edit_out", w1)), "auto"
        else:
            tin, tout, source = float(s.get("edit_in", 0.0)), dur, "full"

        tin, tout = max(0.0, min(tin, dur)), max(0.0, min(tout, dur))
        if tout - tin < ed["min_shot_sec"]:
            tout = min(dur, tin + ed["min_shot_sec"])
        seg.update(tin=tin, tout=tout, source=source)

        trans = (s.get("transition_out") or ed["default_transition"]).lower()
        seg["transition_out"] = DISSOLVE if trans in (DISSOLVE, "fade", "xfade") else CUT
        seg["shot"] = s
        segs.append(seg)

    # Nối liền cùng cảnh: cắt A tại frame khớp với frame đầu B (chỉ bỏ qua khi đạo diễn khóa manual).
    for a, b in zip(segs, segs[1:]):
        if not _is_continuation(a["shot"], b["shot"]):
            continue
        a["transition_out"] = CUT
        if a["source"] == "manual":
            continue
        b_in = b["tin"] if b["source"] in ("manual", "auto") else 0.0
        min_end = a["tin"] + ed["min_shot_sec"]
        if a["vo_path"]:
            min_end = max(min_end, a["tin"] + a["vo_offset"] + a["vo_duration"])
        if a["source"] == "beat_share" or b["shot"].get("chain_from_prev"):
            min_end = max(min_end, a["tout"] - 0.65)
        w1 = a.get("clean_window", (0.0, a["clip_duration"]))[1]
        if min_end >= w1 - 0.05:
            continue
        best_cut, best_bin, best_l1 = a["tout"], b_in, 1e9
        b_candidates = [b_in] if b["source"] == "manual" else [0.0, 0.12, 0.24, 0.36]
        for cand_bin in b_candidates:
            if b["tout"] - cand_bin < ed["min_shot_sec"]:
                continue
            tc, l1_val = _find_seam(a["clip"], min_end, b["clip"], cand_bin, t_max=w1)
            if l1_val < best_l1:
                best_cut, best_bin, best_l1 = tc, cand_bin, l1_val
        b["tin"] = best_bin
        t_cut, l1 = best_cut, best_l1
        a["tout"], a["seam_l1"] = best_cut, best_l1
        if l1 > ed["seam_max_l1"]:
            a["notes"].append(f"Điểm nối với {b['shot_id']} lệch (L1={l1} > {ed['seam_max_l1']}) — dùng Extend thay vì nối bằng 1 frame tĩnh.")
        if a["speech"] and t_cut < a["speech"]["end"] - 0.1:
            a["notes"].append(f"Cắt nối ở {t_cut}s trước khi hết thoại ({a['speech']['end']}s).")

    # Làm tròn theo frame và tính vị trí trên timeline.
    if project.get("epic_multi_coverage"):
        target_dur = float((project.get("plan") or {}).get("target_duration_sec") or 0.0)
        base_total = sum(max(0.0, s["tout"] - s["tin"]) for s in segs)
        if target_dur > base_total + 15.0 and len(segs) >= 4:
            segs = _expand_epic_battle_timeline(proj_dir, project, cfg, segs, target_dur)

    t = 0.0
    for i, seg in enumerate(segs):
        seg["duration"] = round(round((seg["tout"] - seg["tin"]) * fps) / fps, 4)
        prev = segs[i - 1] if i else None
        overlap = 0.0
        if prev and prev["transition_out"] == DISSOLVE:
            overlap = round(min(ed["dissolve_sec"], prev["duration"] / 3, seg["duration"] / 3), 3)
        seg["transition_in_sec"] = overlap
        seg["timeline_start"] = round(t - overlap, 4)
        t = seg["timeline_start"] + seg["duration"]
    _attach_beat_voiceovers(proj_dir, project, cfg, segs)
    return segs


def _expand_epic_battle_timeline(proj_dir: Path, project: dict, cfg: dict, base_segs: list, target_dur: float) -> list:
    """Dựng phim hành động đa góc máy 5 hồi (5-Act Multi-Coverage Hollywood Editorial Engine) đạt chuẩn thời lượng `target_dur` (vd. 300s).

    - Khai thác toàn bộ các take sạch (`take 1`, `take 2`) của từng shot và chia thành 3 pha thời gian (`head`, `mid`, `tail`)
      nằm gọn trong cửa sổ sạch 100% (`clean_windows` né cả lỗi `major` và `minor`).
    - Luân phiên 6 chế độ tiêu cự quang học (`crop_mode`): `wide_master`, `visceral_jaw_clamp_85mm`, `cu_left_85mm`,
      `cu_right_85mm`, `foot_tremor_ground`, `ots_dirty_frame` để không bao giờ lặp lại 2 góc máy giống nhau liên tiếp.
    """
    from . import takes as tk_mod

    fps = cfg["output"]["fps"]
    n_cuts = max(len(base_segs), int(round(target_dur / 4.2857)))
    target_frames_total = int(round(target_dur * fps))
    base_frames_per_cut = target_frames_total // n_cuts
    rem_frames = target_frames_total - (base_frames_per_cut * n_cuts)

    # Chuẩn bị danh sách (clip_path, w0, w1) sạch lỗi cho mỗi base_seg
    seg_variants = {}
    for bseg in base_segs:
        s = bseg["shot"]
        sid = bseg["shot_id"]
        variants = []
        for t_obj in s.get("takes", []):
            p = proj_dir / t_obj.get("path", "")
            if not p.exists():
                continue
            q = t_obj.get("qa") or {}
            if (q.get("technical") or {}).get("verdict") == "fail":
                continue
            dur = float(q.get("duration") or bseg["clip_duration"] or 8.0)
            defs = ((q.get("vision") or {}).get("defects")) or []
            strict_w = tk_mod.clean_windows(dur, defs, severities=("major", "minor"), pad=0.20)
            best_w = max(strict_w, key=lambda w: w[1] - w[0], default=None)
            if not best_w or (best_w[1] - best_w[0]) < 3.2:
                maj_w = tk_mod.clean_windows(dur, defs, severities=("major",), pad=0.25)
                best_w = max(maj_w, key=lambda w: w[1] - w[0], default=(0.0, dur))
            if best_w[1] - best_w[0] >= 3.0:
                variants.append((p, float(best_w[0]), float(best_w[1]), dur))
        if not variants:
            w0, w1 = bseg.get("clean_window", (0.0, bseg["clip_duration"]))
            variants.append((bseg["clip"], float(w0), float(w1), float(bseg["clip_duration"])))
        seg_variants[sid] = variants

    # Phân nhóm shot theo 5 Hồi kịch tính (Act I..V) + nhóm cutaway đặc tả (Macro/ECU/JawClamp/Knockdown)
    n_base = len(base_segs)
    cutaway_segs = [
        b for b in base_segs
        if (b["shot"].get("coverage_role") or "") in (
            "foot_tremor_macro", "eye_snarl_ecu", "visceral_jaw_clamp_cu", "asymmetric_knockdown"
        )
    ]
    coverage_cycle = [
        ("wide_master", "wide_two_shot"),
        ("visceral_jaw_clamp_85mm", "visceral_jaw_clamp_cu"),
        ("cu_left_85mm", "eye_snarl_ecu"),
        ("foot_tremor_ground", "foot_tremor_macro"),
        ("cu_right_85mm", "eye_snarl_ecu"),
        ("ots_dirty_frame", "environmental_destruction"),
    ]

    expanded = []
    use_counts = {b["shot_id"]: 0 for b in base_segs}
    prev_sid = None

    for c_idx in range(n_cuts):
        frames_here = base_frames_per_cut + (1 if c_idx < rem_frames else 0)
        cut_dur = round(frames_here / fps, 4)

        if c_idx == n_cuts - 1:
            chosen = base_segs[-1]
        else:
            act_idx = min(4, int((c_idx / n_cuts) * 5))
            # Cửa sổ trượt theo hồi (Act 0 -> đầu phim, Act 4 -> cuối phim)
            start_i = max(0, int(round((act_idx / 5.0) * max(1, n_base - 3))))
            end_i = min(n_base, start_i + max(5, n_base // 2))
            act_pool = list(base_segs[start_i:end_i])
            for cw in cutaway_segs:
                if cw not in act_pool:
                    act_pool.append(cw)
            if not act_pool:
                act_pool = list(base_segs)
            # Ưu tiên shot ít xuất hiện nhất trong pool và khác với shot liền trước
            candidates = [b for b in act_pool if b["shot_id"] != prev_sid] or act_pool
            candidates.sort(key=lambda b: (use_counts[b["shot_id"]], (act_pool.index(b) + c_idx) % len(act_pool)))
            chosen = candidates[c_idx % min(3, len(candidates))]

        sid = chosen["shot_id"]
        prev_sid = sid
        u_idx = use_counts[sid]
        use_counts[sid] += 1

        variants = seg_variants[sid]
        clip_p, w0, w1, clip_dur = variants[u_idx % len(variants)]
        avail = max(0.1, w1 - w0)
        eff_dur = min(cut_dur, avail)

        # Chọn pha thời gian (head / mid / tail) trong cửa sổ sạch
        is_finale_shot = (sid == base_segs[-1]["shot_id"])
        phase_mode = 2 if (is_finale_shot and c_idx == n_cuts - 1) else ((u_idx // len(variants)) % 3)
        if avail <= eff_dur + 0.30:
            tin = w0
        elif phase_mode == 0:
            tin = min(w1 - eff_dur, w0 + 0.15)
        elif phase_mode == 1:
            tin = w0 + (avail - eff_dur) * 0.5
        else:
            tin = max(w0, w1 - eff_dur - 0.15)
        tin = round(max(0.0, tin), 4)
        tout = round(tin + cut_dur, 4)

        native_role = chosen["shot"].get("coverage_role") or ""
        if c_idx == n_cuts - 1:
            crop_mode, cov_role = "wide_master", "abyss_standoff_wide"
        elif native_role and u_idx < 2:
            crop_mode, cov_role = "wide_master", native_role
        else:
            crop_mode, cov_role = coverage_cycle[(c_idx + u_idx) % len(coverage_cycle)]

        new_seg = dict(chosen)
        new_seg.update(
            clip=clip_p,
            clip_duration=clip_dur,
            tin=tin,
            tout=tout,
            duration=cut_dur,
            transition_out=CUT,
            crop_mode=crop_mode,
            coverage_role=cov_role,
            act=min(5, int((c_idx / n_cuts) * 5) + 1),
            source=f"epic_act{min(5, int((c_idx / n_cuts) * 5) + 1)}_{crop_mode}",
            notes=[],
        )
        expanded.append(new_seg)
    return expanded


def _attach_beat_voiceovers(proj_dir: Path, project: dict, cfg: dict, segs: list) -> None:
    """Gắn lời dẫn của mỗi beat vào shot đầu beat; lời chạy xuyên các shot của beat (L-cut), có thể vào sớm (J-cut)."""
    beats = bt.beats_by_id(project)
    if not beats:
        return
    for b_id, beat in beats.items():
        members = [s for s in segs if s["shot"].get("beat") == b_id]
        vo = bt.beat_vo(proj_dir, beat)
        if not members or not vo:
            continue
        for s in members:
            s["subtitle"] = ""  # phụ đề theo câu của beat, không theo shot
        first = members[0]
        first.update(vo_path=vo, vo_offset=bt.vo_offset(beat, cfg), vo_duration=au.wav_duration(vo), vo_span=True,
                     subtitle=beat.get("narration", ""), beat_id=b_id)
        picture = members[-1]["timeline_start"] + members[-1]["duration"] - first["timeline_start"]
        need = first["vo_offset"] + first["vo_duration"] + cfg["editorial"]["vo_post_roll_sec"]
        if need > picture + 0.05:
            first["notes"].append(f"Beat {b_id}: lời dẫn cần {need:.2f}s nhưng hình của beat chỉ {picture:.2f}s.")
    # Lời các beat không được chồng nhau (J-cut quá sâu / beat trước quá dài).
    spans = sorted((s["timeline_start"] + s["vo_offset"], s["timeline_start"] + s["vo_offset"] + s["vo_duration"], s)
                   for s in segs if s.get("vo_path"))
    for (a0, a1, sa), (b0, b1, sb) in zip(spans, spans[1:]):
        if b0 < a1 - 0.02:
            sb["notes"].append(f"Lời dẫn chồng lên lời của {sa['shot_id']} {a1 - b0:.2f}s — giảm j_cut_sec hoặc kéo dài hình.")


def total_duration(segs: list) -> float:
    return round(segs[-1]["timeline_start"] + segs[-1]["duration"], 3) if segs else 0.0


def subtitle_cues(segs: list) -> list:
    """(start, end, text) trên timeline."""
    cues = []
    for seg in segs:
        text = (seg.get("subtitle") or "").strip()
        if not text:
            continue
        start, end = seg["timeline_start"], seg["timeline_start"] + seg["duration"]
        if seg["vo_path"]:
            start = max(0.0, seg["timeline_start"] + seg["vo_offset"])
            # lời của beat chạy qua nhiều shot → phụ đề không bị cắt ở cuối shot đầu
            end = start + seg["vo_duration"] if seg.get("vo_span") else min(end, start + seg["vo_duration"])
        elif seg["speech"] and seg["speech"]["reliable"]:
            start = seg["timeline_start"] + max(0.0, seg["speech"]["start"] - seg["tin"])
            end = seg["timeline_start"] + max(0.0, min(seg["speech"]["end"], seg["tout"]) - seg["tin"])
        if end - start > 0.3:
            cues.append((round(start, 3), round(end, 3), text))
    return cues


def to_json(segs: list) -> list:
    keys = ("shot_id", "beat_id", "act", "coverage_role", "crop_mode", "source", "tin", "tout", "duration",
            "timeline_start", "transition_in_sec", "transition_out", "vo_offset", "vo_duration", "seam_l1", "notes")
    out = []
    for s in segs:
        row = {k: s.get(k) for k in keys if s.get(k) is not None}
        row["clip"] = str(s["clip"])
        if s.get("vo_path"):
            row["voiceover"] = str(s["vo_path"])
        out.append(row)
    return out
