import wave

import numpy as np

from conftest import make_clip
from studio import beats as bt
from studio import manifest as mf
from studio import media, render, takes, timeline


def _wav(path, seconds, sr=24000):
    path.parent.mkdir(parents=True, exist_ok=True)
    x = (0.3 * np.sin(2 * np.pi * 300 * np.arange(int(sr * seconds)) / sr) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())


def _setup(project, beats, shot_beats):
    clips = project / "assets" / "clips"
    shots = []
    for i, b in enumerate(shot_beats, 1):
        make_clip(clips / f"shot_{i:02d}.mp4", seconds=8)
        shots.append({"shot_id": f"shot_{i:02d}", "order": i, "beat": b, "clip_output_path": f"assets/clips/shot_{i:02d}.mp4",
                      "status": "qa_pass", "audio": {"mode": "voiceover_external", "line": ""}})
    for b in beats:
        _wav(project / b["voiceover_path"], b.pop("_vo_sec"))
    m = mf.load(project)
    m["beats"], m["shots"] = beats, shots
    mf.save(project, m)
    return m


def test_beat_voiceover_spans_shots_and_splits_picture(project, cfg):
    m = _setup(project, [{"beat_id": "b1", "order": 1, "narration": "A long line that spans two shots.",
                          "voiceover_path": "assets/audio/vo/beat_b1.wav", "_vo_sec": 5.0}], ["b1", "b1"])
    segs = timeline.compute(project, m, cfg)
    need_total = cfg["editorial"]["vo_pre_roll_sec"] + 5.0 + cfg["editorial"]["vo_post_roll_sec"]
    assert all(s["source"] == "beat_share" for s in segs)
    assert abs(sum(s["duration"] for s in segs) - need_total) < 0.1          # hình vừa đủ cho lời của beat
    assert segs[0]["vo_span"] and segs[0]["vo_duration"] > segs[0]["duration"]  # lời chạy sang shot 2 (L-cut)
    cues = timeline.subtitle_cues(segs)
    assert len(cues) == 1 and cues[0][1] - cues[0][0] > segs[0]["duration"]    # phụ đề không bị cắt ở cuối shot 1
    assert takes.needed_seconds(project, m["shots"][0], cfg, m) == round(need_total / 2, 2)


def test_j_cut_starts_narration_before_picture(project, cfg):
    m = _setup(project, [
        {"beat_id": "b1", "order": 1, "narration": "one", "voiceover_path": "assets/audio/vo/b1.wav", "_vo_sec": 2.0},
        {"beat_id": "b2", "order": 2, "narration": "two", "j_cut_sec": 0.8, "voiceover_path": "assets/audio/vo/b2.wav",
         "_vo_sec": 2.0},
    ], ["b1", "b2"])
    segs = timeline.compute(project, m, cfg)
    b2 = segs[1]
    assert b2["vo_offset"] < 0                                              # lời beat 2 vào trước hình beat 2
    assert b2["timeline_start"] + b2["vo_offset"] < segs[0]["timeline_start"] + segs[0]["duration"]
    assert not any("chồng" in n for s in segs for n in s["notes"])          # vẫn không chồng lời beat 1


def test_overlapping_narration_is_flagged(project, cfg):
    m = _setup(project, [
        {"beat_id": "b1", "order": 1, "narration": "one", "voiceover_path": "assets/audio/vo/b1.wav", "_vo_sec": 6.0},
        {"beat_id": "b2", "order": 2, "narration": "two", "voiceover_path": "assets/audio/vo/b2.wav", "_vo_sec": 2.0},
    ], ["b1", "b2"])
    m["shots"][0]["edit_in"], m["shots"][0]["edit_out"] = 0.0, 3.0         # đạo diễn cắt ngắn hình beat 1
    segs = timeline.compute(project, m, cfg)
    notes = [n for s in segs for n in s["notes"]]
    assert any("chồng" in n for n in notes) and any("Beat b1" in n for n in notes)


def test_render_with_beats(project, cfg):
    m = _setup(project, [{"beat_id": "b1", "order": 1, "narration": "spanning narration line",
                          "j_cut_sec": 0.5, "voiceover_path": "assets/audio/vo/b1.wav", "_vo_sec": 4.0}], ["b1", "b1"])
    segs = timeline.compute(project, m, cfg)
    out = project / "output" / "beats.mp4"
    res = render.render(segs, out, cfg)
    assert res["voiceover_tracks"] == 1
    assert abs(media.probe(out)["duration"] - timeline.total_duration(segs)) < 0.1


def test_shot_need_floor(project, cfg):
    m = _setup(project, [{"beat_id": "b1", "order": 1, "narration": "x", "voiceover_path": "assets/audio/vo/b1.wav",
                          "_vo_sec": 1.0}], ["b1", "b1", "b1"])
    assert bt.shot_need(project, m, m["shots"][0], cfg) == cfg["editorial"]["min_beat_shot_sec"]


def test_voiceover_command_links_beat_wav(project, cfg, monkeypatch, capsys):
    import json
    from studio import cli
    monkeypatch.setattr("studio.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    m = _setup(project, [{"beat_id": "b1", "order": 1, "narration": "beat line",
                          "voiceover_path": "assets/audio/vo/beat_b1.wav", "_vo_sec": 3.0}], ["b1", "b1"])
    m["beats"][0].pop("voiceover_path")                                   # WAV có sẵn nhưng chưa liên kết
    mf.save(project, m)
    cli.main(["voiceover", "--project", str(project)])
    res = json.loads(capsys.readouterr().out)
    assert [r["shot"] for r in res["shots"]] == ["b1"]                    # 1 file cho cả beat, không theo shot
    assert mf.load(project)["beats"][0]["voiceover_path"] == "assets/audio/vo/beat_b1.wav"


def test_storyboard_gate(project, cfg, capsys):
    import json
    import pytest
    from studio import cli, storyboard
    m = _setup(project, [{"beat_id": "b1", "order": 1, "narration": "line", "voiceover_path": "assets/audio/vo/b1.wav",
                          "_vo_sec": 1.0}], ["b1", "b1"])
    cli.main(["storyboard", "--project", str(project)])
    res = json.loads(capsys.readouterr().out)
    assert res["beats"] == 1 and res["shots"] == 2 and not res["approval"]["valid"]
    assert (project / "output" / "storyboard.html").exists()
    with pytest.raises(SystemExit):   # chưa duyệt → không cho tạo video
        cli.main(["flow-generate", "--project", str(project), "--kind", "video"])
    cli.main(["storyboard-approve", "--project", str(project)])
    capsys.readouterr()
    assert storyboard.approval_state(mf.load(project))["valid"]
    m = mf.load(project); m["beats"][0]["narration"] = "changed"; mf.save(project, m)   # sửa sau khi duyệt
    assert not storyboard.approval_state(mf.load(project))["valid"]
    with pytest.raises(SystemExit):   # phải xuất lại storyboard trước khi duyệt lại
        cli.main(["storyboard-approve", "--project", str(project)])


def test_storyboard_gate_blocks_even_without_beats(project, cfg):
    import pytest
    from studio import cli
    m = mf.load(project)
    m["beats"] = []
    m["shots"] = [{"shot_id": "shot_01", "order": 1, "veo_prompt": "Wide shot of a studio."}]
    mf.save(project, m)
    with pytest.raises(SystemExit):
        cli.main(["flow-generate", "--project", str(project), "--kind", "video"])
