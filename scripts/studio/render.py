"""Render bản dựng cuối bằng ffmpeg: ghép hình theo timeline, mix âm thanh 3 lớp, loudnorm, phụ đề, 16:9/9:16."""

import os
import re
from pathlib import Path

from . import media
from .timeline import DISSOLVE, subtitle_cues, total_duration

FORMATS = {
    "landscape": {"suffix": "", "aspect": (16, 9)},
    "vertical": {"suffix": "_9x16", "aspect": (9, 16)},
}


def target_size(fmt: str, cfg: dict) -> tuple:
    w, h = cfg["output"]["width"], cfg["output"]["height"]
    long_side, short_side = max(w, h), min(w, h)
    return (long_side, short_side) if fmt == "landscape" else (short_side, long_side)


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split_text(text: str, max_chars: int) -> list:
    """Chia câu dài thành các cue ≤ 2 dòng × max_chars."""
    words, chunks, cur = text.split(), [], ""
    limit = max_chars * 2
    for w in words:
        if cur and len(cur) + 1 + len(w) > limit:
            chunks.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def _wrap(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    words = text.split()
    best, best_diff = text, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        diff = abs(len(a) - len(b))
        if diff < best_diff:
            best, best_diff = f"{a}\n{b}", diff
    return best


def write_srt(segs: list, out_path: Path, cfg: dict, fmt: str = "landscape") -> int:
    sub = cfg["subtitles"]
    max_chars = sub["max_chars_per_line"] if fmt == "landscape" else sub["max_chars_per_line_vertical"]
    lines, n = [], 0
    for start, end, text in subtitle_cues(segs):
        chunks = _split_text(text, max_chars)
        total_chars = sum(len(c) for c in chunks)
        t = start
        for c in chunks:
            d = (end - start) * len(c) / total_chars
            n += 1
            lines += [str(n), f"{_srt_time(t)} --> {_srt_time(t + d)}", _wrap(c, max_chars), ""]
            t += d
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return n


def _shake_And_grain_suffix(seg: dict, w: int, h: int) -> str:
    """Hiệu ứng rung máy vật lý tại điểm va chạm (Impact Camera Shake) + hạt phim 35mm IMAX cho cảnh hành động."""
    shot = seg.get("shot") or {}
    shake = shot.get("camera_shake")
    grain = shot.get("film_grain")
    fx = ""
    if shake:
        cfg_s = shake if isinstance(shake, dict) else {}
        amp = float(cfg_s.get("amp", 14.0))
        t_imp = float(cfg_s.get("at", round(seg["duration"] * 0.42, 2)))
        sw = int(round(w * 1.045))
        sh = int(round(h * 1.045))
        # Dao động tắt dần tại t_imp + rung bước chân nhẹ
        dx = f"({amp:.1f}*sin(2*PI*19*t)*exp(-6.0*abs(t-{t_imp:.2f}))+2.5*sin(2*PI*1.3*t))"
        dy = f"({amp * 1.25:.1f}*cos(2*PI*23*t)*exp(-6.0*abs(t-{t_imp:.2f}))+2.5*cos(2*PI*1.7*t))"
        fx += f",scale={sw}:{sh}:flags=lanczos,crop={w}:{h}:'(iw-ow)/2+{dx}':'(ih-oh)/2+{dy}'"
    if grain:
        strength = int(grain) if isinstance(grain, (int, float)) and not isinstance(grain, bool) else 3
        fx += f",unsharp=5:5:0.35:5:5:0.0,noise=alls={strength}:allf=t+u"
    return fx


def _video_chain(i: int, seg: dict, w: int, h: int, fps: int, fit: str) -> str:
    d = seg["duration"]
    head = (f"[{i}:v]trim=start={seg['tin']:.4f},setpts=PTS-STARTPTS,fps={fps},"
            f"tpad=stop_mode=clone:stop_duration=0.5,trim=duration={d:.4f},setpts=PTS-STARTPTS,fps={fps}")
    post_fx = _shake_And_grain_suffix(seg, w, h)
    if fit == "crop":
        # crop_focus_x: 0 = giữ mép trái, 0.5 = giữa, 1 = mép phải (đặt theo vị trí chủ thể từng shot)
        fx = min(1.0, max(0.0, float(seg.get("shot", {}).get("crop_focus_x", 0.5))))
        body = (f",scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={w}:{h}:(iw-{w})*{fx:.3f}:(ih-{h})/2{post_fx}")
        return f"{head}{body},setsar=1,format=yuv420p[v{i}]"
    if fit == "blur":
        return (f"{head},split=2[bg{i}][fg{i}];"
                f"[bg{i}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[bgb{i}];"
                f"[fg{i}]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[fgs{i}];"
                f"[bgb{i}][fgs{i}]overlay=(W-w)/2:(H-h)/2{post_fx},setsar=1,format=yuv420p[v{i}]")
    body = (f",scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black{post_fx}")
    return f"{head}{body},setsar=1,format=yuv420p[v{i}]"


def _shot_has_clipping(shot: dict) -> bool:
    """True nếu QA kỹ thuật phát hiện AUDIO_CLIPPING trên shot hoặc trên take đã chọn."""
    if not isinstance(shot, dict):
        return False
    findings = list((shot.get("qa") or {}).get("technical", {}).get("findings", []))
    sel = shot.get("selected_take")
    for t in shot.get("takes", []):
        if sel is None or t.get("take") == sel:
            findings += (t.get("qa") or {}).get("technical", {}).get("findings", [])
    return any(f.get("code") == "AUDIO_CLIPPING" for f in findings)


def _audio_chain(i: int, seg: dict) -> str:
    d = seg["duration"]
    if not seg["has_audio"]:
        return f"anullsrc=r=48000:cl=stereo,atrim=0:{d:.4f}[a{i}]"
    shot = seg.get("shot") or {}
    sanitize = ""
    if _shot_has_clipping(shot):
        # Giảm đỉnh rè (0 dBFS) của audio Veo và lọc bớt hài cao gắt trước khi trộn.
        sanitize = ",volume=-4.5dB,lowpass=f=7500"
    return (f"[{i}:a]atrim=start={seg['tin']:.4f},asetpts=PTS-STARTPTS,"
            f"aformat=sample_rates=48000:channel_layouts=stereo{sanitize},apad,atrim=0:{d:.4f}[a{i}]")


def _join(segs: list, filters: list, fps: int) -> tuple:
    """Ghép các shot: chuỗi hard-cut gom bằng 1 concat, giữa các chuỗi dùng xfade/acrossfade."""
    runs, cur = [], [0]
    for i in range(1, len(segs)):
        if segs[i - 1]["transition_out"] == DISSOLVE:
            runs.append(cur)
            cur = [i]
        else:
            cur.append(i)
    runs.append(cur)

    run_labels = []
    for r_idx, run in enumerate(runs):
        if len(run) == 1:
            run_labels.append((f"[v{run[0]}]", f"[a{run[0]}]", segs[run[0]]["duration"]))
            continue
        pads = "".join(f"[v{i}][a{i}]" for i in run)
        filters.append(f"{pads}concat=n={len(run)}:v=1:a=1[rvc{r_idx}][ra{r_idx}]")
        filters.append(f"[rvc{r_idx}]fps={fps}[rv{r_idx}]")  # concat đổi timebase; xfade cần CFR + cùng timebase
        run_labels.append((f"[rv{r_idx}]", f"[ra{r_idx}]", sum(segs[i]["duration"] for i in run)))

    v, a, length = run_labels[0]
    for k in range(1, len(runs)):
        first = runs[k][0]
        t = segs[first]["transition_in_sec"]
        nv, na, nlen = run_labels[k]
        filters.append(f"{v}{nv}xfade=transition=fade:duration={t:.3f}:offset={length - t:.4f}[jv{k}]")
        filters.append(f"{a}{na}acrossfade=d={t:.3f}:c1=tri:c2=tri[ja{k}]")
        v, a, length = f"[jv{k}]", f"[ja{k}]", length + nlen - t
    return v, a, length


def _escape_filter_path(p: str) -> str:
    return p.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def render(segs: list, out_path: Path, cfg: dict, fmt: str = "landscape", fit: str = None,
           music: Path = None, srt: Path = None, burn_subs: bool = False, lut: Path = None) -> dict:
    if not segs:
        raise media.MediaError("Timeline rỗng — chưa có clip nào đủ điều kiện dựng.")
    out_cfg, mix_cfg = cfg["output"], cfg["audio_mix"]
    w, h = target_size(fmt, cfg)
    fps = out_cfg["fps"]
    if fit is None:
        fit = "pad" if fmt == "landscape" else "crop"

    inputs, filters = [], []
    for i, seg in enumerate(segs):
        inputs += ["-i", str(seg["clip"])]
        filters.append(_video_chain(i, seg, w, h, fps, fit))
        filters.append(_audio_chain(i, seg))
    vcat, acat, length = _join(segs, filters, fps)
    total = total_duration(segs)

    # --- Lớp âm thanh: production (Veo) + lời dẫn + nhạc ---
    next_in = len(segs)
    vo_labels = []
    for seg in segs:
        if seg["vo_path"]:
            inputs += ["-i", str(seg["vo_path"])]
            ms = max(0, int(round((seg["timeline_start"] + seg["vo_offset"]) * 1000)))
            lbl = f"[vo{len(vo_labels)}]"
            filters.append(f"[{next_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}{lbl}")
            vo_labels.append(lbl)
            next_in += 1

    mix_inputs = []
    if vo_labels:
        filters.append(f"{acat}volume={mix_cfg['production_gain_db_with_vo']}dB[prod]")
        mix_inputs.append("[prod]")
        if len(vo_labels) == 1:
            filters.append(f"{vo_labels[0]}anull[vomix]")
        else:
            filters.append(f"{''.join(vo_labels)}amix=inputs={len(vo_labels)}:normalize=0:duration=longest[vomix]")
    else:
        mix_inputs.append(acat)

    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        filters.append(f"[{next_in}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{total:.3f},"
                       f"volume={mix_cfg['music_gain_db']}dB[mus]")
        next_in += 1
        if vo_labels and mix_cfg["duck_music_under_vo"]:
            filters.append("[vomix]asplit=2[vo_main][vo_sc]")
            filters.append("[mus][vo_sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[musd]")
            mix_inputs += ["[vo_main]", "[musd]"]
        else:
            if vo_labels:
                mix_inputs.append("[vomix]")
            mix_inputs.append("[mus]")
    elif vo_labels:
        mix_inputs.append("[vomix]")

    # loudnorm 1 lượt không chặn được đỉnh khi trộn nhiều lớp → limiter phía sau giữ true peak dưới ngưỡng.
    # Ngưỡng thấp hơn mục tiêu 1,5 dB để chừa chỗ cho đỉnh liên mẫu và độ vọt của bộ mã hóa AAC.
    limit = 10 ** ((out_cfg["true_peak_db"] - 1.5) / 20)
    # Nén nhẹ trước (giảm đỉnh gắt của SFX như bước chân/tiếng gầm) → loudnorm đạt mục tiêu mà không phải gọt đỉnh mạnh.
    loud = (f"acompressor=threshold=0.1:ratio=3:attack=5:release=150:knee=4:makeup=1,"
            f"loudnorm=I={out_cfg['loudness_lufs']}:TP={out_cfg['true_peak_db']}:LRA=9,aresample=48000,"
            f"alimiter=limit={limit:.4f}:attack=3:release=80:level=disabled")
    ed = cfg.get("editorial", {})
    afin, afout = float(ed.get("start_fade_sec", 0) or 0), float(ed.get("end_fade_sec", 0) or 0)
    afade = (f",afade=t=in:st=0:d={afin:.2f}" if afin > 0 else "") +             (f",afade=t=out:st={max(0.0, total - afout):.3f}:d={afout:.2f}" if afout > 0 else "")
    if len(mix_inputs) == 1:
        filters.append(f"{mix_inputs[0]}{loud},aresample=48000,atrim=0:{total:.3f}{afade}[aout]")
    else:
        filters.append(f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:normalize=0:duration=first,"
                       f"{loud},aresample=48000,atrim=0:{total:.3f}{afade}[aout]")

    # --- Hậu kỳ hình: LUT + phụ đề ---
    vpost = vcat
    if lut:
        filters.append(f"{vpost}lut3d=file='{_escape_filter_path(str(Path(lut).resolve()))}'[vlut]")
        vpost = "[vlut]"
    if burn_subs and srt and srt.exists() and srt.stat().st_size > 0:
        sub_cfg = cfg["subtitles"]
        size = sub_cfg["font_size"] if fmt == "landscape" else sub_cfg["font_size_vertical"]
        margin = 28 if fmt == "landscape" else 70  # khung dọc: tránh vùng nút/caption của TikTok/Shorts
        style = f"FontName={sub_cfg['font']},FontSize={size},Outline=2,Shadow=0,BorderStyle=1,MarginV={margin}"
        filters.append(f"{vpost}subtitles={srt.name}:force_style='{style}'[vsub]")
        vpost = "[vsub]"
    ed = cfg.get("editorial", {})
    fin, fout = float(ed.get("start_fade_sec", 0) or 0), float(ed.get("end_fade_sec", 0) or 0)
    if fin > 0 or fout > 0:
        parts = ([f"fade=t=in:st=0:d={fin:.2f}"] if fin > 0 else []) +                 ([f"fade=t=out:st={max(0.0, total - fout):.3f}:d={fout:.2f}"] if fout > 0 else [])
        filters.append(f"{vpost}{','.join(parts)}[vfade]")
        vpost = "[vfade]"
    filters.append(f"{vpost}null[vout]")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph = out_path.parent / f"filtergraph{FORMATS[fmt]['suffix']}.txt"
    graph.write_text(";\n".join(filters), encoding="utf-8")

    if media.has_nvenc():
        vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0", "-profile:v", "high"]
    else:
        vcodec = ["-c:v", "libx264", "-preset", "medium", "-crf", str(out_cfg["crf"]), "-profile:v", "high"]

    media.run_ffmpeg(
        [*inputs, "-filter_complex_script", graph.name, "-map", "[vout]", "-map", "[aout]",
         *vcodec, "-pix_fmt", "yuv420p", "-r", str(fps),
         "-c:a", "aac", "-b:a", out_cfg["audio_bitrate"], "-ar", "48000",
         "-movflags", "+faststart", os.path.relpath(out_path, out_path.parent)],
        cwd=out_path.parent,
    )
    loud_info = enforce_true_peak(out_path, out_cfg["true_peak_db"], out_cfg["audio_bitrate"])
    return {"path": str(out_path), "size": f"{w}x{h}", "fit": fit, "duration_planned": total,
            "loudness_lufs": loud_info["lufs"], "true_peak_db": loud_info["true_peak_db"],
            "encoder": vcodec[1], "voiceover_tracks": len(vo_labels), "music": bool(music),
            "subtitles_burned": bool(burn_subs and srt and srt.exists())}


def measure_loudness(path: Path) -> dict:
    """Đo EBU R128 trên file đã mã hóa: integrated LUFS + true peak (dBTP)."""
    import subprocess

    res = subprocess.run([media.ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(path), "-vn",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    txt = res.stderr.decode("utf-8", "replace")
    summary = txt[txt.rfind("Summary:"):]
    i = re.search(r"I:\s*(-?[\d.]+) LUFS", summary)
    pk = re.search(r"Peak:\s*(-?[\d.]+|-inf) dBFS", summary)
    return {"lufs": float(i.group(1)) if i else None,
            "true_peak_db": float(pk.group(1)) if pk and pk.group(1) != "-inf" else None}


def enforce_true_peak(path: Path, target_db: float, bitrate: str, tries: int = 2) -> dict:
    """Nếu true peak sau mã hóa AAC vượt ngưỡng: hạ âm lượng đúng phần dư (giữ nguyên hình), đo lại."""
    m = measure_loudness(path)
    for _ in range(tries):
        if m["true_peak_db"] is None or m["true_peak_db"] <= target_db:
            break
        gain = target_db - m["true_peak_db"] - 0.3
        tmp = path.with_name(path.stem + "._tp.mp4")
        media.run_ffmpeg(["-i", str(path), "-map", "0", "-c:v", "copy", "-af", f"volume={gain:.2f}dB",
                          "-c:a", "aac", "-b:a", bitrate, "-ar", "48000", "-movflags", "+faststart", str(tmp)])
        tmp.replace(path)
        m = measure_loudness(path)
    return m


def output_name(base: str, fmt: str) -> str:
    stem = re.sub(r"\.mp4$", "", base)
    return f"{stem}{FORMATS[fmt]['suffix']}.mp4"
