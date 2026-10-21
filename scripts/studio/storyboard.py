import re
"""Cổng duyệt storyboard (0 credit): người dùng duyệt ảnh mở đầu + lời dẫn theo beat TRƯỚC khi tạo video.

`storyboard` xuất output/storyboard.html (+ ảnh tổng hợp .jpg) và ghi manifest["storyboard"] = {status, hash}.
`storyboard-approve` đặt status=approved với hash nội dung hiện tại. Sửa beat/shot sau khi duyệt → hash đổi →
flow-generate --kind video bị chặn tới khi duyệt lại.
"""

import hashlib
import html
import json
import os
from datetime import datetime
from pathlib import Path

from . import beats as bt
from . import manifest as mf
from . import media

HASH_FIELDS = ("beat", "order", "camera", "action", "subjects", "first_frame_path", "last_frame_path", "generation_mode", "veo_prompt")


def content_hash(project: dict) -> str:
    beats = [{k: b.get(k) for k in ("beat_id", "order", "narration", "j_cut_sec")} for b in bt.ordered_beats(project)]
    shots = [{k: s.get(k) for k in HASH_FIELDS} for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    return hashlib.sha256(json.dumps([beats, shots], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def approval_state(project: dict) -> dict:
    sb = project.get("storyboard") or {}
    current = content_hash(project)
    return {"status": sb.get("status", "none"), "approved_hash": sb.get("approved_hash"), "current_hash": current,
            "valid": sb.get("status") == "approved" and sb.get("approved_hash") == current}


def _frame_for(proj: Path, s: dict) -> list:
    paths = []
    if s.get("first_frame_path") and (proj / s["first_frame_path"]).exists():
        paths.append(proj / s["first_frame_path"])
    if s.get("last_frame_path") and (proj / s["last_frame_path"]).exists():
        lp = proj / s["last_frame_path"]
        if lp not in paths:
            paths.append(lp)
    for c in s.get("frame_candidates", []):
        p = proj / c["path"]
        if p.exists() and p not in paths:
            paths.append(p)
    return paths[:3]


def groups(project: dict) -> list:
    """[(beat | None, [shots])] theo thứ tự xuất hiện; shot không thuộc beat thành nhóm riêng."""
    beats = bt.beats_by_id(project)
    out, cur = [], None
    for s in mf.ordered_shots(project):
        if s.get("exclude_from_edit"):
            continue
        b = beats.get(s.get("beat"))
        key = b["beat_id"] if b else f"_{s['shot_id']}"
        if not cur or cur[0] != key:
            cur = (key, b, [])
            out.append(cur)
        cur[2].append(s)
    return [(b, shots) for _, b, shots in out]


def build(proj: Path, project: dict, cfg: dict, credits_per_shot: int) -> dict:
    proj = Path(proj)
    mf.resolve_chained_keyframes(project, proj)
    out_dir = proj / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "storyboard.html"
    rel = lambda p: os.path.relpath(p, out_dir).replace("\\", "/")  # noqa: E731
    rows, n_shots, missing = [], 0, []
    for b, shots in groups(project):
        title = (f"{b['beat_id']} · {html.escape(b.get('purpose', ''))}" if b else f"{shots[0]['shot_id']} (không thuộc beat)")
        narration = (b.get("narration") if b else mf.shot_audio(shots[0]).get("line")) or ""
        jcut = f" · J-cut {b['j_cut_sec']}s" if b and b.get("j_cut_sec") else ""
        cells = []
        for s in shots:
            n_shots += 1
            frames = _frame_for(proj, s)
            if not frames and s.get("generation_mode") in ("first_frame", "first_last"):
                missing.append(s["shot_id"])
            imgs = "".join(f'<img src="{rel(f)}" alt="{s["shot_id"]}">' for f in frames) or '<div class="noimg">chưa có frame</div>'
            cells.append(f'<div class="shot"><div class="imgs">{imgs}</div><b>{s["shot_id"]}</b> · {html.escape(s.get("camera", ""))}'
                         f'<p>{html.escape(s.get("action", ""))}</p></div>')
        rows.append(f'<section><h2>{title}{jcut}</h2><blockquote>{html.escape(narration)}</blockquote>'
                    f'<div class="row">{"".join(cells)}</div></section>')
    state = approval_state(project)
    to_make = [s for _, ss in groups(project) for s in ss if not s.get("selected_take")]
    est = len(to_make) * credits_per_shot  # shot đã có take được chọn (dùng lại) không tốn thêm
    doc = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard</title><style>
:root{{--bg:#fff;--fg:#1a1a1a;--muted:#666;--card:#f4f4f2}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141414;--fg:#eee;--muted:#999;--card:#1f1f1f}}}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:16px;max-width:1200px;margin:auto}}
section{{background:var(--card);border-radius:10px;padding:12px 16px;margin:14px 0}}
h2{{font-size:16px;margin:4px 0}} blockquote{{margin:6px 0 10px;font-style:italic;color:var(--muted)}}
.row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.shot img{{width:100%;border-radius:6px;display:block;margin-bottom:4px}} .shot p{{margin:4px 0;font-size:13px;color:var(--muted)}}
.noimg{{height:140px;display:grid;place-items:center;border:1px dashed var(--muted);border-radius:6px;color:var(--muted)}}
</style></head><body>
<h1>Storyboard — {html.escape(project.get('project_name', proj.name))}</h1>
<p>{len(rows)} nhịp · {n_shots} shot ({len(to_make)} cần tạo mới) · ước tính video: <b>{est} credit</b> · trạng thái: <b>{state['status']}</b>
 · tạo lúc {datetime.now():%Y-%m-%d %H:%M}</p>
{''.join(rows)}
</body></html>"""
    page.write_text(doc, encoding="utf-8")
    sheet = _contact(proj, project, out_dir / "storyboard.jpg")
    project["storyboard"] = {**(project.get("storyboard") or {}), "status": "approved" if state["valid"] else "pending",
                             "built_hash": state["current_hash"], "built_at": datetime.now().isoformat(timespec="seconds")}
    return {"html": str(page), "contact_sheet": str(sheet) if sheet else None, "beats": len(rows), "shots": n_shots,
            "shots_to_generate": [s["shot_id"] for s in to_make],
            "estimated_video_credits": est, "missing_frames": missing, "approval": approval_state(project)}


def _contact(proj: Path, project: dict, out: Path):
    """Ảnh tổng hợp: mỗi hàng 1 beat (frame đầu từng shot + nhãn) — để agent/người xem nhanh."""
    import numpy as np

    cv2 = media.cv2_module()
    rows = []
    for b, shots in groups(project):
        cells = []
        for s in shots:
            fr = _frame_for(proj, s)
            im = cv2.imread(str(fr[0])) if fr else None
            im = cv2.resize(im, (384, 216)) if im is not None else np.full((216, 384, 3), 40, np.uint8)
            label = f"{b['beat_id'] if b else ''} {s['shot_id']}".strip()
            cv2.rectangle(im, (0, 0), (12 + 11 * len(label), 26), (0, 0, 0), -1)
            cv2.putText(im, label, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
            cells.append(im)
        while len(cells) < 4:
            cells.append(np.zeros((216, 384, 3), np.uint8))
        rows.append(np.hstack(cells[:4]))
    if not rows:
        return None
    cv2.imwrite(str(out), np.vstack(rows), [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return out



def default_grid_panels(project: dict, rows: int = 3, cols: int = 3) -> list:
    """Tr? v? danh s?ch rows*cols ? (panel) theo th? t? th?i gian c?a k?ch b?n ?? v? trong 1 ?nh Storyboard Grid."""
    n_panels = rows * cols
    custom = (project.get("storyboard_grid") or {}).get("panels") or []
    if len(custom) == n_panels:
        out = []
        for idx, item in enumerate(custom, 1):
            out.append({
                "index": idx,
                "row": (idx - 1) // cols + 1,
                "col": (idx - 1) % cols + 1,
                "title": item.get("title") or f"Panel {idx}",
                "description": item.get("description") or "",
                "targets": item.get("targets") or [],
            })
        return out

    shots = [s for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    if not shots:
        return []
    moments = []
    for s in shots:
        cam = (s.get("camera") or s.get("camera_shot") or "").strip().rstrip(".")
        s_act = (s.get("start_action") or s.get("action") or "").strip().rstrip(".")
        e_act = (s.get("end_action") or "").strip().rstrip(".")
        moments.append({
            "shot_id": s["shot_id"],
            "slot": "start",
            "title": f"{s['shot_id']} START",
            "description": f"{cam}; {s_act}" if cam else s_act,
        })
        if e_act and e_act.lower() != s_act.lower():
            moments.append({
                "shot_id": s["shot_id"],
                "slot": "end",
                "title": f"{s['shot_id']} END",
                "description": f"{cam}; {e_act}" if cam else e_act,
            })
    if len(moments) <= n_panels:
        while len(moments) < n_panels:
            moments.append(dict(moments[-1]))
        chosen = [[m] for m in moments[:n_panels]]
    else:
        chosen = [[] for _ in range(n_panels)]
        for i, m_item in enumerate(moments):
            bucket = min(n_panels - 1, int(i * n_panels / len(moments)))
            chosen[bucket].append(m_item)
    panels = []
    for idx, group in enumerate(chosen, 1):
        rep = group[0] if group else moments[-1]
        panels.append({
            "index": idx,
            "row": (idx - 1) // cols + 1,
            "col": (idx - 1) % cols + 1,
            "title": rep["title"],
            "description": rep["description"],
            "targets": [{"shot": g["shot_id"], "slot": g["slot"]} for g in group],
        })
    return panels


def _detect_grid_splits(gray, count: int, axis: int) -> list:
    """D? ???ng k? ph?n c?ch (divider line) gi?a c?c ? theo ph??ng ngang (axis=0) ho?c d?c (axis=1)."""
    import numpy as np

    total = gray.shape[axis]
    splits = [0]
    band = max(4, int(total * 0.038))
    for k in range(1, count):
        ideal = int(round(total * k / count))
        lo, hi = max(1, ideal - band), min(total - 2, ideal + band)
        best_pos, best_score = ideal, float("inf")
        for pos in range(lo, hi + 1):
            line = gray[pos, :] if axis == 0 else gray[:, pos]
            # ???ng k? ph?n c?ch th??ng t?i ??u (std th?p + luma th?p) ho?c tr?ng ??u (std th?p)
            std_v = float(np.std(line))
            mean_v = float(np.mean(line))
            dark_bonus = mean_v * 0.35 if mean_v < 60 else (255.0 - mean_v) * 0.35 if mean_v > 210 else 45.0
            dist_pen = abs(pos - ideal) * 0.15
            score = std_v + dark_bonus + dist_pen
            if score < best_score:
                best_score, best_pos = score, pos
        splits.append(best_pos)
    splits.append(total)
    return splits


def _clean_and_upscale_cell(cell_bgr, aspect: str = "16:9", luma_thresh: int = 28):
    """C?t b? vi?n ?en/tr?ng c?n s?t quanh ? v? ph?ng n?t Lanczos4 l?n chu?n Full HD (1920x1080 ho?c 1080x1920)."""
    import numpy as np

    cv2 = media.cv2_module()
    h, w = cell_bgr.shape[:2]
    # 1. C?t l?m nh? 1.2% m?i c?nh ?? lo?i ho?n to?n ???ng k? ph?n c?ch
    px, py = max(2, int(round(w * 0.012))), max(2, int(round(h * 0.012)))
    if w > 4 * px and h > 4 * py:
        cell_bgr = cell_bgr[py : h - py, px : w - px]

    # 2. Qu?t 4 c?nh n?u v?n c?n vi?n ?en ho?c tr?ng ??ng nh?t
    gray = cv2.cvtColor(cell_bgr, cv2.COLOR_BGR2GRAY)
    ch, cw = gray.shape[:2]
    max_trim_y, max_trim_x = int(ch * 0.08), int(cw * 0.08)

    def _is_border_line(arr):
        m, s = float(np.mean(arr)), float(np.std(arr))
        return (m < luma_thresh and s < 18.0) or (m > 240.0 and s < 12.0)

    top = 0
    while top < max_trim_y and _is_border_line(gray[top, :]):
        top += 1
    bot = ch
    while ch - bot < max_trim_y and bot > top + 32 and _is_border_line(gray[bot - 1, :]):
        bot -= 1
    left = 0
    while left < max_trim_x and _is_border_line(gray[:, left]):
        left += 1
    right = cw
    while cw - right < max_trim_x and right > left + 32 and _is_border_line(gray[:, right - 1]):
        right -= 1
    cell_bgr = cell_bgr[top:bot, left:right]

    # 3. C?n ch?nh ??ng t? l? 16:9 ho?c 9:16 v? n?ng c?p Lanczos4 + Unsharp Mask nh?
    target_w, target_h = (1080, 1920) if aspect == "9:16" else (1920, 1080)
    target_ratio = target_w / target_h
    ch, cw = cell_bgr.shape[:2]
    cur_ratio = cw / max(1, ch)
    if abs(cur_ratio - target_ratio) > 0.015:
        if cur_ratio > target_ratio:
            new_w = int(round(ch * target_ratio))
            x0 = (cw - new_w) // 2
            cell_bgr = cell_bgr[:, x0 : x0 + new_w]
        else:
            new_h = int(round(cw / target_ratio))
            y0 = (ch - new_h) // 2
            cell_bgr = cell_bgr[y0 : y0 + new_h, :]

    up = cv2.resize(cell_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(up, (0, 0), 1.1)
    sharp = cv2.addWeighted(up, 1.16, blur, -0.16, 0)
    return sharp


def slice_storyboard_grid(
    grid_path: Path,
    proj: Path,
    project: dict,
    rows: int = 3,
    cols: int = 3,
    apply_to_shots: bool = True,
    letterbox_luma: int = 26,
) -> dict:
    """T? ??ng c?t 1 ?nh Storyboard Grid (RxC) th?nh c?c frame 16:9/9:16 s?ch + xu?t b?n Storyboard Sheet c? nh?n."""
    import shutil
    import numpy as np

    cv2 = media.cv2_module()
    grid_path = Path(grid_path)
    proj = Path(proj)
    im = cv2.imread(str(grid_path))
    if im is None:
        raise media.MediaError(f"Kh?ng ??c ???c ?nh Storyboard Grid: {grid_path}")

    aspect = project.get("aspect_ratio", "16:9")
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    y_splits = _detect_grid_splits(gray, rows, axis=0)
    x_splits = _detect_grid_splits(gray, cols, axis=1)

    panels = default_grid_panels(project, rows=rows, cols=cols)
    panels_dir = proj / "assets" / "frames" / "grid_panels"
    panels_dir.mkdir(parents=True, exist_ok=True)
    cand_dir = proj / "assets" / "frames" / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)

    # T?o b?n annotated (c? nh?n #1..#N) k?ch th??c l?n ?? ng??i d?ng duy?t tr?c quan tr?n 1 ?nh
    sheet_w, sheet_h = (1620, 2880) if aspect == "9:16" else (2880, 1620)
    annotated = cv2.resize(im, (sheet_w, sheet_h), interpolation=cv2.INTER_LANCZOS4)
    sx, sy = sheet_w / im.shape[1], sheet_h / im.shape[0]

    sliced_info = []
    for p in panels:
        idx = p["index"]
        r = p["row"] - 1
        c = p["col"] - 1
        y0, y1 = y_splits[r], y_splits[r + 1]
        x0, x1 = x_splits[c], x_splits[c + 1]
        cell = im[y0:y1, x0:x1]
        clean_panel = _clean_and_upscale_cell(cell, aspect=aspect, luma_thresh=letterbox_luma)
        panel_file = panels_dir / f"PANEL_{idx:02d}.jpg"
        cv2.imwrite(str(panel_file), clean_panel, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        panel_sha = media.sha256_file(panel_file)

        # V? nh?n l?n b?n annotated_sheet
        ax0, ay0 = int(round(x0 * sx)), int(round(y0 * sy))
        badge_txt = re.sub(r"[^\x20-\x7E]+", "-", f"#{idx} {p.get('title', '')}").strip()
        bw = min(int((x1 - x0) * sx) - 16, 18 + 13 * len(badge_txt))
        overlay = annotated.copy()
        cv2.rectangle(overlay, (ax0 + 10, ay0 + 10), (ax0 + 10 + bw, ay0 + 46), (12, 16, 22), -1)
        cv2.addWeighted(overlay, 0.78, annotated, 0.22, 0, annotated)
        cv2.putText(annotated, badge_txt, (ax0 + 18, ay0 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (0, 230, 255), 2, cv2.LINE_AA)

        applied_targets = []
        if apply_to_shots:
            for t in p.get("targets", []):
                sid, slot = t["shot"], t.get("slot", "start")
                s = mf.find_shot(project, sid)
                if not s:
                    continue
                if slot == "start" and s.get("chain_from_prev"):
                    continue
                uid_prefix = mf.keyframe_uid(project, sid, slot)
                cand_key = "last_frame_candidates" if slot == "end" else "frame_candidates"
                path_key = "last_frame_path" if slot == "end" else "first_frame_path"
                cands = s.setdefault(cand_key, [])
                if not any(x.get("sha256") == panel_sha for x in cands):
                    dst_cand = cand_dir / f"{uid_prefix}_grid_p{idx:02d}.jpg"
                    shutil.copy2(panel_file, dst_cand)
                    cands.append({
                        "path": os.path.relpath(dst_cand, proj).replace("\\", "/"),
                        "sha256": panel_sha,
                        "uid": uid_prefix,
                        "from_storyboard_grid": idx,
                    })
                canonical = proj / mf.keyframe_rel_path(project, sid, slot, ".jpg")
                canonical.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(panel_file, canonical)
                s[path_key] = os.path.relpath(canonical, proj).replace("\\", "/")
                applied_targets.append(f"{sid}:{slot}")

        sliced_info.append({
            "panel": idx,
            "row": p["row"],
            "col": p["col"],
            "title": p.get("title", ""),
            "path": os.path.relpath(panel_file, proj).replace("\\", "/"),
            "applied_to": applied_targets,
        })

    if apply_to_shots:
        mf.resolve_chained_keyframes(project, proj)

    out_dir = proj / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_out = out_dir / "storyboard_sheet.jpg"
    cv2.imwrite(str(sheet_out), annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    sb_grid = project.setdefault("storyboard_grid", {})
    sb_grid["rows"] = rows
    sb_grid["cols"] = cols
    sb_grid["raw_grid_path"] = os.path.relpath(grid_path, proj).replace("\\", "/")
    sb_grid["annotated_sheet_path"] = os.path.relpath(sheet_out, proj).replace("\\", "/")
    sb_grid["sliced_panels"] = sliced_info
    return {
        "raw_grid": sb_grid["raw_grid_path"],
        "annotated_sheet": sb_grid["annotated_sheet_path"],
        "rows": rows,
        "cols": cols,
        "panels": sliced_info,
    }
