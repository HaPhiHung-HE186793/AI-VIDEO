"""Xuất Timeline sang các phần mềm dựng phim chuyên nghiệp (NLE Export):
- Final Cut Pro / DaVinci Resolve / Premiere Pro / CapCut PC (`.fcpxml` v1.9)
- Avid / Premiere / DaVinci CMX 3600 Edit Decision List (`.edl`)
- CapCut / Jianying Draft JSON (`capcut_draft_content.json`)
"""

import json
import uuid
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from .timeline import DISSOLVE, subtitle_cues, total_duration


def _sec_to_fcpxml_rational(sec: float, fps: int = 24) -> str:
    """Đổi giây sang phân số căn chỉnh theo frame chuẩn FCPXML (vd: '120/24s' hoặc '0s')."""
    frames = int(round(max(0.0, float(sec or 0.0)) * fps))
    if frames == 0:
        return "0s"
    return f"{frames}/{fps}s"


def _sec_to_smpte(sec: float, fps: int = 24) -> str:
    """Đổi giây sang mã thời gian SMPTE HH:MM:SS:FF cho chuẩn CMX 3600 EDL."""
    total_frames = max(0, int(round(float(sec or 0.0) * fps)))
    ff = total_frames % fps
    total_seconds = total_frames // fps
    ss = total_seconds % 60
    mm = (total_seconds // 60) % 60
    hh = total_seconds // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def _file_uri(path: Path) -> str:
    try:
        return Path(path).resolve().as_uri()
    except Exception:  # noqa: BLE001
        posix = str(Path(path).resolve()).replace("\\", "/")
        return f"file:///{posix.lstrip('/')}"


def export_fcpxml(
    segs: list,
    out_path: Path,
    project: dict,
    cfg: dict,
    fmt: str = "landscape",
    music: Path = None,
) -> Path:
    """Xuất file `.fcpxml` (FCPXML v1.9) tương thích DaVinci Resolve, Premiere Pro, Final Cut Pro, CapCut PC."""
    out_cfg = cfg["output"]
    fps = int(out_cfg.get("fps", 24) or 24)
    w, h = int(out_cfg.get("width", 1920)), int(out_cfg.get("height", 1080))
    if fmt == "vertical":
        w, h = min(w, h), max(w, h)
    else:
        w, h = max(w, h), min(w, h)

    total_sec = total_duration(segs)
    proj_name = project.get("project_name") or project.get("project_slug") or "AI_Video_Project"

    resources = [
        f'    <format id="r1" name="FFVideoFormat{h}p{fps}" frameDuration="1/{fps}s" width="{w}" height="{h}" colorSpace="1-1-1 (Rec. 709)"/>'
    ]
    asset_map = {}
    next_res_idx = 2

    def register_asset(fpath: Path, *, has_video: bool, has_audio: bool, dur_sec: float, label: str) -> str:
        nonlocal next_res_idx
        key = str(Path(fpath).resolve())
        if key in asset_map:
            return asset_map[key]
        rid = f"r{next_res_idx}"
        next_res_idx += 1
        asset_map[key] = rid
        uri = _file_uri(fpath)
        dur_str = _sec_to_fcpxml_rational(max(dur_sec, 1.0), fps)
        hv = "1" if has_video else "0"
        ha = "1" if has_audio else "0"
        fmt_attr = ' format="r1"' if has_video else ""
        resources.append(
            f'    <asset id="{rid}" name={quoteattr(label)} src={quoteattr(uri)} start="0s" '
            f'duration="{dur_str}" hasVideo="{hv}" hasAudio="{ha}"{fmt_attr} audioSources="1" audioChannels="2" audioRate="48000"/>'
        )
        return rid

    for seg in segs:
        register_asset(
            seg["clip"],
            has_video=True,
            has_audio=bool(seg.get("has_audio", True)),
            dur_sec=float(seg.get("clip_duration") or seg.get("duration") or 8.0),
            label=seg["shot_id"],
        )
        if seg.get("vo_path"):
            register_asset(
                seg["vo_path"],
                has_video=False,
                has_audio=True,
                dur_sec=float(seg.get("vo_duration") or 5.0),
                label=f"VO_{seg.get('beat_id') or seg['shot_id']}",
            )

    music_rid = None
    if music and Path(music).exists():
        music_rid = register_asset(
            Path(music),
            has_video=False,
            has_audio=True,
            dur_sec=max(total_sec, 10.0),
            label=f"Music_{Path(music).stem}",
        )

    spine_items = []
    for idx, seg in enumerate(segs):
        vid_rid = asset_map[str(Path(seg["clip"]).resolve())]
        offset_str = _sec_to_fcpxml_rational(seg["timeline_start"], fps)
        start_str = _sec_to_fcpxml_rational(seg["tin"], fps)
        dur_str = _sec_to_fcpxml_rational(seg["duration"], fps)
        children = []

        # Lane 1: Lời dẫn ngoài (Voiceover) hỗ trợ cả J-cut (offset âm) và L-cut (kéo dài qua nhiều shot)
        if seg.get("vo_path"):
            vo_rid = asset_map[str(Path(seg["vo_path"]).resolve())]
            vo_attach_sec = max(0.0, float(seg["tin"]) + float(seg.get("vo_offset", 0.0)))
            vo_offset_str = _sec_to_fcpxml_rational(vo_attach_sec, fps)
            vo_dur_str = _sec_to_fcpxml_rational(seg.get("vo_duration", seg["duration"]), fps)
            vo_name = f"VO_{seg.get('beat_id') or seg['shot_id']}"
            children.append(
                f'              <asset-clip name={quoteattr(vo_name)} lane="1" offset="{vo_offset_str}" '
                f'ref="{vo_rid}" start="0s" duration="{vo_dur_str}" audioRole="dialogue"/>'
            )

        # Lane -1: Nhạc nền (Background Score) gắn vào shot mở đầu và trải suốt thời lượng phim
        if idx == 0 and music_rid:
            mus_dur_str = _sec_to_fcpxml_rational(total_sec, fps)
            children.append(
                f'              <asset-clip name="Background_Score" lane="-1" offset="{start_str}" '
                f'ref="{music_rid}" start="0s" duration="{mus_dur_str}" audioRole="music"/>'
            )

        if children:
            spine_items.append(
                f'            <asset-clip name={quoteattr(seg["shot_id"])} offset="{offset_str}" ref="{vid_rid}" '
                f'start="{start_str}" duration="{dur_str}" format="r1">\n'
                + "\n".join(children)
                + "\n            </asset-clip>"
            )
        else:
            spine_items.append(
                f'            <asset-clip name={quoteattr(seg["shot_id"])} offset="{offset_str}" ref="{vid_rid}" '
                f'start="{start_str}" duration="{dur_str}" format="r1"/>'
            )

        if seg.get("transition_out") == DISSOLVE and idx < len(segs) - 1:
            t_sec = float(segs[idx + 1].get("transition_in_sec") or 0.5)
            t_dur_str = _sec_to_fcpxml_rational(t_sec, fps)
            t_off_str = _sec_to_fcpxml_rational(seg["timeline_start"] + seg["duration"] - t_sec, fps)
            spine_items.append(
                f'            <transition name="Cross Dissolve" offset="{t_off_str}" duration="{t_dur_str}"/>'
            )

    seq_dur_str = _sec_to_fcpxml_rational(total_sec, fps)
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!DOCTYPE fcpxml>",
        '<fcpxml version="1.9">',
        "  <resources>",
        *resources,
        "  </resources>",
        "  <library>",
        f'    <event name={quoteattr(proj_name)}>',
        f'      <project name={quoteattr(f"{proj_name}_{fmt}")}>',
        f'        <sequence format="r1" duration="{seq_dur_str}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">',
        "          <spine>",
        *spine_items,
        "          </spine>",
        "        </sequence>",
        "      </project>",
        "    </event>",
        "  </library>",
        "</fcpxml>",
    ]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(xml_lines) + "\n", encoding="utf-8")
    return out_path


def export_edl(segs: list, out_path: Path, project: dict, cfg: dict) -> Path:
    """Xuất file `.edl` (CMX 3600 Edit Decision List) chuẩn công nghiệp cho DaVinci Resolve / Premiere / Avid."""
    fps = int(cfg["output"].get("fps", 24) or 24)
    title = (project.get("project_slug") or project.get("project_name") or "AI_VIDEO").upper()[:40]
    lines = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]

    for idx, seg in enumerate(segs, start=1):
        reel = f"SHOT{idx:04d}"[:8]
        src_in = _sec_to_smpte(seg["tin"], fps)
        src_out = _sec_to_smpte(seg["tout"], fps)
        rec_in = _sec_to_smpte(seg["timeline_start"], fps)
        rec_out = _sec_to_smpte(seg["timeline_start"] + seg["duration"], fps)
        lines.append(f"{idx:03d}  {reel:<8} V     C        {src_in} {src_out} {rec_in} {rec_out}")
        lines.append(f"* FROM CLIP NAME: {Path(seg['clip']).name}")
        lines.append(f"* SHOT ID: {seg['shot_id']} (SOURCE: {seg.get('source', 'auto')})")
        if seg.get("vo_path"):
            vo_start = max(0.0, seg["timeline_start"] + float(seg.get("vo_offset", 0.0)))
            vo_end = vo_start + float(seg.get("vo_duration", 0.0))
            lines.append(
                f"* VOICEOVER TRACK: {Path(seg['vo_path']).name} [{_sec_to_smpte(vo_start, fps)} -> {_sec_to_smpte(vo_end, fps)}]"
            )
        lines.append("")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def export_capcut_draft(
    segs: list,
    out_path: Path,
    project: dict,
    cfg: dict,
    fmt: str = "landscape",
    music: Path = None,
) -> Path:
    """Xuất file `capcut_draft_content.json` theo cấu trúc microsecond (1s = 1,000,000 us) của CapCut / Jianying."""
    out_cfg = cfg["output"]
    fps = int(out_cfg.get("fps", 24) or 24)
    w, h = int(out_cfg.get("width", 1920)), int(out_cfg.get("height", 1080))
    if fmt == "vertical":
        w, h = min(w, h), max(w, h)
    else:
        w, h = max(w, h), min(w, h)

    def us(sec: float) -> int:
        return int(round(max(0.0, float(sec or 0.0)) * 1_000_000))

    def uid(seed: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{project.get('project_slug', 'proj')}:{seed}")).upper()

    videos_mat, audios_mat, texts_mat = [], [], []
    video_segs, vo_segs, music_segs, text_segs = [], [], [], []

    for idx, seg in enumerate(segs):
        vid_id = uid(f"vid_mat_{idx}_{seg['shot_id']}")
        videos_mat.append({
            "id": vid_id,
            "type": "video",
            "path": str(Path(seg["clip"]).resolve()),
            "material_name": Path(seg["clip"]).name,
            "duration": us(seg.get("clip_duration") or seg["duration"]),
            "width": w,
            "height": h,
        })
        video_segs.append({
            "id": uid(f"vid_seg_{idx}_{seg['shot_id']}"),
            "material_id": vid_id,
            "source_timerange": {"start": us(seg["tin"]), "duration": us(seg["duration"])},
            "target_timerange": {"start": us(seg["timeline_start"]), "duration": us(seg["duration"])},
            "shot_id": seg["shot_id"],
        })

        if seg.get("vo_path"):
            vo_id = uid(f"vo_mat_{idx}_{seg['shot_id']}")
            vo_dur = float(seg.get("vo_duration") or seg["duration"])
            vo_start = max(0.0, float(seg["timeline_start"]) + float(seg.get("vo_offset", 0.0)))
            audios_mat.append({
                "id": vo_id,
                "type": "voiceover",
                "path": str(Path(seg["vo_path"]).resolve()),
                "name": Path(seg["vo_path"]).name,
                "duration": us(vo_dur),
            })
            vo_segs.append({
                "id": uid(f"vo_seg_{idx}_{seg['shot_id']}"),
                "material_id": vo_id,
                "source_timerange": {"start": 0, "duration": us(vo_dur)},
                "target_timerange": {"start": us(vo_start), "duration": us(vo_dur)},
            })

    total_sec = total_duration(segs)
    if music and Path(music).exists():
        mus_id = uid("bgm_score")
        audios_mat.append({
            "id": mus_id,
            "type": "music",
            "path": str(Path(music).resolve()),
            "name": Path(music).name,
            "duration": us(total_sec),
        })
        music_segs.append({
            "id": uid("bgm_seg_0"),
            "material_id": mus_id,
            "source_timerange": {"start": 0, "duration": us(total_sec)},
            "target_timerange": {"start": 0, "duration": us(total_sec)},
        })

    for c_idx, (c_start, c_end, c_text) in enumerate(subtitle_cues(segs)):
        txt_id = uid(f"sub_mat_{c_idx}")
        texts_mat.append({"id": txt_id, "type": "subtitle", "content": escape(c_text)})
        text_segs.append({
            "id": uid(f"sub_seg_{c_idx}"),
            "material_id": txt_id,
            "target_timerange": {"start": us(c_start), "duration": us(c_end - c_start)},
        })

    draft = {
        "canvas_config": {"width": w, "height": h, "ratio": "9:16" if fmt == "vertical" else "16:9"},
        "fps": fps,
        "duration": us(total_sec),
        "name": project.get("project_name") or project.get("project_slug") or "AI_Video_Draft",
        "materials": {"videos": videos_mat, "audios": audios_mat, "texts": texts_mat},
        "tracks": [
            {"type": "video", "name": "V1_Main_Spine", "segments": video_segs},
            {"type": "audio", "name": "A1_Voiceover", "segments": vo_segs},
            {"type": "audio", "name": "A2_Background_Score", "segments": music_segs},
            {"type": "text", "name": "T1_Subtitles", "segments": text_segs},
        ],
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def export_all_nle(
    segs: list,
    outdir: Path,
    project: dict,
    cfg: dict,
    fmt: str = "landscape",
    music: Path = None,
) -> dict:
    """Xuất đồng thời 3 định dạng bàn giao hậu kỳ: `.fcpxml`, `.edl` và `capcut_draft_content.json`."""
    outdir = Path(outdir)
    suffix = "_9x16" if fmt == "vertical" else ""
    fcpxml_path = export_fcpxml(segs, outdir / f"timeline{suffix}.fcpxml", project, cfg, fmt=fmt, music=music)
    edl_path = export_edl(segs, outdir / f"timeline{suffix}.edl", project, cfg)
    capcut_path = export_capcut_draft(
        segs, outdir / f"capcut_draft_content{suffix}.json", project, cfg, fmt=fmt, music=music
    )
    return {
        "fcpxml": str(fcpxml_path),
        "edl": str(edl_path),
        "capcut_draft": str(capcut_path),
    }
