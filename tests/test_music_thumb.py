import wave

from conftest import make_clip
from studio import music, thumbnail


def test_intensity_follows_beats():
    secs = [(0, 5, "hook"), (5, 10, "climax"), (10, 15, "cliffhanger")]
    c = music.intensity_curve(secs, 15)
    assert c[750] > c[250] and c[750] > c[1300]  # cao trào mạnh nhất, câu hỏi treo lắng xuống


def test_synth_score_writes_stereo_wav(tmp_path):
    res = music.synth_score(6.0, [(0, 3, "need"), (3, 6, "climax")], tmp_path / "s.wav", sr=16000)
    with wave.open(res["path"]) as w:
        assert w.getnchannels() == 2 and abs(w.getnframes() / w.getframerate() - 6.0) < 0.01


def test_thumbnail_picks_frame_and_writes_both_sizes(tmp_path):
    clip = make_clip(tmp_path / "a.mp4", seconds=3)
    segs = [{"shot_id": "a", "clip": clip, "tin": 0.0, "tout": 3.0, "shot": {}}]
    res = thumbnail.make(segs, tmp_path / "out", "24 giờ ở Hell Creek", "Chương 1")
    assert res["frame"]["shot"] == "a" and len(res["files"]) == 2
    from PIL import Image
    assert Image.open(res["files"]["thumbnail_9x16.jpg"]).size == (1080, 1920)


def test_font_without_vietnamese_glyphs_is_skipped():
    impact = "C:/Windows/Fonts/impact.ttf"
    from pathlib import Path
    if Path(impact).exists():
        assert thumbnail._covers(impact, "HELL CREEK") and not thumbnail._covers(impact, "GIỜ")
