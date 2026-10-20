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


def test_drums_land_on_cuts_in_intense_sections():
    secs = [(0, 5, "hook"), (5, 15, "climax")]
    c = music.intensity_curve(secs, 15)
    times = music.drum_times(15, c, cuts=[2.0, 7.3, 11.1])
    assert 7.3 in times and 11.1 in times      # cắt hình trong cao trào → có trống đúng điểm cắt
    assert 2.0 not in times                    # hook yên lặng: không trống
    assert all(b - a > 0.2 for a, b in zip(times, times[1:]))


def test_publish_hashtags_and_limits():
    from studio import publish
    assert publish.hashtag("T. rex") == "#TRex" and publish.hashtag("Hell Creek") == "#HellCreek"
    assert publish.check({"title": "x" * 101}) and not publish.check({"title": "ok", "tags": ["a"]})
    assert publish.fmt_ts(75) == "1:15"


def test_lut_cube_is_valid_and_identity_at_zero_strength(tmp_path):
    import numpy as np
    from studio import grade
    path = grade.write_cube(tmp_path / "g.cube", "documentary", 1.0, size=9)
    lines = path.read_text().splitlines()
    assert "LUT_3D_SIZE 9" in lines and len([l for l in lines if l[:1].isdigit()]) == 9 ** 3
    x = np.random.default_rng(0).random((100, 3))
    assert np.allclose(grade.transform(x, "documentary", 0.0), x)
    assert np.allclose(grade.transform(np.array([[0.0, 0, 0], [1, 1, 1]]), "documentary")[:, 0], [0, 1], atol=0.03)
