"""Nhịp truyện (beat): đơn vị kể chuyện gồm 2–3 shot (toàn / cận / phản ứng) dùng chung MỘT câu lời dẫn.

manifest["beats"] = [{
    "beat_id": "b01", "order": 1, "purpose": "hook",           # hook | escalation | climax | cliffhanger | ...
    "narration": "Before sunrise, ...",                         # lời dẫn của cả beat (trải qua nhiều shot)
    "j_cut_sec": 0.0,       # >0: lời của beat vào SỚM hơn hình (J-cut) — nghe trước khi thấy
    "vo_offset": 0.3,       # lời bắt đầu sau khi hình đầu beat xuất hiện bao lâu (mặc định vo_pre_roll_sec)
    "voiceover_path": "assets/audio/vo/beat_b01.wav"            # do lệnh `voiceover` tạo
}]
shot["beat"] = "b01"  — shot thuộc beat; thứ tự shot trong beat theo shot["order"].

L-cut xảy ra tự nhiên khi lời của beat dài hơn shot đầu: lời tiếp tục chạy qua các shot sau của beat.
"""

from pathlib import Path

from . import audio as au
from . import manifest as mf


def beats_by_id(project: dict) -> dict:
    return {b["beat_id"]: b for b in project.get("beats", []) if b.get("beat_id")}


def ordered_beats(project: dict) -> list:
    return sorted(project.get("beats", []), key=lambda b: (b.get("order", 0), b.get("beat_id", "")))


def shots_in_beat(project: dict, beat_id: str) -> list:
    return [s for s in mf.ordered_shots(project) if s.get("beat") == beat_id and not s.get("exclude_from_edit")]


def beat_vo(proj: Path, beat: dict):
    p = beat.get("voiceover_path")
    return Path(proj) / p if p and (Path(proj) / p).exists() else None


def vo_offset(beat: dict, cfg: dict) -> float:
    """Vị trí lời so với đầu hình của shot đầu beat (âm = J-cut, lời vào trước hình)."""
    return float(beat.get("vo_offset", cfg["editorial"]["vo_pre_roll_sec"])) - float(beat.get("j_cut_sec", 0.0))


def beat_total_need(proj: Path, beat: dict, cfg: dict) -> float:
    """Tổng thời lượng hình beat cần để chứa trọn lời dẫn (+ khoảng thở sau lời)."""
    vo = beat_vo(proj, beat)
    if not vo:
        return 0.0
    return max(0.0, vo_offset(beat, cfg)) + au.wav_duration(vo) + cfg["editorial"]["vo_post_roll_sec"]


def shot_need(proj: Path, project: dict, shot: dict, cfg: dict) -> float:
    """Thời lượng hình tối thiểu cho một shot trong beat: ưu tiên target_duration riêng của shot, hoặc chia đều nhu cầu của beat."""
    if shot.get("target_duration"):
        return round(float(shot["target_duration"]), 2)
    ed = cfg["editorial"]
    beat = beats_by_id(project).get(shot.get("beat"))
    b_shots = shots_in_beat(project, shot["beat"]) if beat else []
    n = max(1, len(b_shots))
    total = beat_total_need(proj, beat, cfg) if beat else 0.0
    if total and len(b_shots) > 1:
        overlap = sum(
            float(s.get("transition_sec", ed.get("dissolve_sec", 0.5)))
            for s in b_shots[:-1]
            if s.get("transition_out", "cut") in ("dissolve", "fade_black")
        )
        total += overlap
    share = total / n if total else float(ed.get("preferred_shot_sec", 4.0))
    return round(max(float(ed.get("min_beat_shot_sec", 2.0)), share), 2)
