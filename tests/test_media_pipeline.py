import json
import wave

import numpy as np

from conftest import make_clip
from studio import audio as au
from studio import manifest as mf
from studio import media, qa, render, timeline


def _shot(sid, order, **kw):
    return {"shot_id": sid, "order": order, "clip_output_path": f"assets/clips/{sid}.mp4", "status": "rendered", **kw}


def _save(proj, shots):
    m = mf.load(proj)
    m["shots"] = shots
    mf.save(proj, m)
    return m


def test_letterbox_is_rejected_and_clean_clip_passes(tmp_path, cfg):
    bad = make_clip(tmp_path / "lb.mp4", seconds=4.5, letterbox=40)
    good = make_clip(tmp_path / "ok.mp4", seconds=4.5)
    bad_codes = {f["code"] for f in qa.technical_qa(bad, cfg)["findings"]}
    good_res = qa.technical_qa(good, cfg)
    assert "LETTERBOX" in bad_codes
    assert good_res["verdict"] == "pass", good_res["findings"]


def test_freeze_detected(tmp_path, cfg):
    clip = tmp_path / "still.mp4"
    media.run_ffmpeg(["-f", "lavfi", "-i", "color=c=gray:s=640x360:r=24:d=5", "-f", "lavfi", "-i", "sine=d=5",
                      "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)])
    codes = {f["code"] for f in qa.technical_qa(clip, cfg)["findings"]}
    assert "FREEZE" in codes


def test_speech_window_estimate(tmp_path):
    clip = make_clip(tmp_path / "talk.mp4", seconds=8, speech=(1.0, 6.0))
    sw = au.speech_window(clip)
    assert sw["reliable"]
    assert abs(sw["start"] - 1.0) < 0.2 and abs(sw["end"] - 6.0) < 0.2


def test_assemble_keeps_audio_and_video_in_sync(project, cfg):
    clips = project / "assets" / "clips"
    make_clip(clips / "shot_01.mp4", seconds=8, speech=(0.5, 5.0))
    make_clip(clips / "shot_02.mp4", seconds=8, speech=(1.5, 6.5))
    make_clip(clips / "shot_03.mp4", seconds=6)
    shots = [
        _shot("shot_01", 1, audio={"mode": "veo_dialogue", "line": "Hello there friend"}),
        _shot("shot_02", 2, audio={"mode": "veo_dialogue", "line": "A second line of dialogue"}, transition_out="dissolve"),
        _shot("shot_03", 3, audio={"mode": "sfx_only"}),
    ]
    m = _save(project, shots)
    segs = timeline.compute(project, m, cfg)
    assert [s["shot_id"] for s in segs] == ["shot_01", "shot_02", "shot_03"]
    assert segs[0]["tout"] < 6.0          # cắt sau khi hết thoại, không giữ cả 8s
    assert segs[1]["tin"] > 1.0           # bỏ khoảng lặng đầu shot 2
    assert segs[2]["transition_in_sec"] > 0  # dissolve theo yêu cầu
    assert segs[1]["transition_in_sec"] == 0  # mặc định hard cut

    out = project / "output" / "final.mp4"
    srt = project / "output" / "subs.srt"
    assert render.write_srt(segs, srt, cfg) == 2
    render.render(segs, out, cfg, srt=srt, burn_subs=True)
    info = media.probe(out)
    expected = timeline.total_duration(segs)
    assert abs(info["duration"] - expected) < 0.1, (info["duration"], expected)
    # Audio và video phải dài bằng nhau (không lệch tiếng/hình)
    pcm = media.read_pcm(out, sr=16000)
    assert abs(len(pcm) / 16000 - expected) < 0.1
    # Loudness đã được chuẩn hóa: không câm, đỉnh dưới -1 dBFS (limiter)
    assert 0.01 < float(np.sqrt(np.mean(pcm ** 2))) < 0.9
    assert float(np.max(np.abs(pcm))) < 10 ** (-1.0 / 20)
    # Fade chương: frame đầu tối, nửa giây cuối tiếng nhỏ dần
    graph = (out.parent / "filtergraph.txt").read_text(encoding="utf-8")
    assert "fade=t=in" in graph and "afade=t=out" in graph
    first, _ = media.read_frame_at(out, 0.0)
    assert float(first.mean()) < 25


def test_vertical_render_and_voiceover_mix(project, cfg):
    clips = project / "assets" / "clips"
    make_clip(clips / "shot_01.mp4", seconds=8, tone=220)
    vo = project / "assets" / "audio" / "vo" / "shot_01.wav"
    vo.parent.mkdir(parents=True)
    sr = 24000
    t = np.arange(int(sr * 3.0)) / sr
    with wave.open(str(vo), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((0.3 * np.sin(2 * np.pi * 600 * t) * 32767).astype(np.int16).tobytes())
    m = _save(project, [_shot("shot_01", 1, audio={"mode": "voiceover_external", "line": "Narration line"},
                              voiceover_path="assets/audio/vo/shot_01.wav")])
    segs = timeline.compute(project, m, cfg)
    ed = cfg["editorial"]
    assert abs(segs[0]["duration"] - (ed["vo_pre_roll_sec"] + 3.0 + ed["vo_post_roll_sec"])) < 0.05
    out = project / "output" / "final_9x16.mp4"
    res = render.render(segs, out, cfg, fmt="vertical")
    info = media.probe(out)
    assert (info["width"], info["height"]) == (360, 640)
    assert res["voiceover_tracks"] == 1


def test_intra_scene_seam_cuts_at_matching_frame(project, cfg):
    clips = project / "assets" / "clips"
    a = make_clip(clips / "shot_01.mp4", seconds=8)
    # Shot B bắt đầu đúng bằng frame 5.0s của A (mô phỏng nối bằng frame trích xuất)
    media.run_ffmpeg(["-ss", "5.0", "-i", str(a), "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
                      "-c:a", "aac", str(clips / "shot_02.mp4")])
    m = _save(project, [_shot("shot_01", 1, transition_to_next="INTRA_SCENE_CONTINUE"), _shot("shot_02", 2)])
    segs = timeline.compute(project, m, cfg)
    assert abs(segs[0]["tout"] - 5.0) <= 0.1, segs[0]["tout"]
    assert segs[0]["seam_l1"] < cfg["editorial"]["seam_max_l1"]
    assert segs[1]["tin"] == 0.0


def test_failed_qa_shots_are_excluded(project, cfg):
    clips = project / "assets" / "clips"
    make_clip(clips / "shot_01.mp4", seconds=5)
    make_clip(clips / "shot_02.mp4", seconds=5)
    m = _save(project, [_shot("shot_01", 1), _shot("shot_02", 2, status="qa_fail")])
    assert [s["shot_id"] for s in timeline.compute(project, m, cfg)] == ["shot_01"]
    assert len(timeline.compute(project, m, cfg, include_pending=True)) == 2


def test_manifest_save_is_atomic_with_backup(project):
    m = mf.load(project)
    m["project_name"] = "changed"
    mf.save(project, m)
    assert json.loads((project / "project_manifest.json.bak").read_text(encoding="utf-8"))["project_name"] == "test"
    assert mf.load(project)["project_name"] == "changed"


def test_manual_window_keeps_voiceover(project, cfg):
    clips = project / "assets" / "clips"
    make_clip(clips / "shot_01.mp4", seconds=8)
    vo = project / "assets" / "audio" / "vo" / "shot_01.wav"
    vo.parent.mkdir(parents=True)
    sr = 24000
    with wave.open(str(vo), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((0.3 * np.sin(2 * np.pi * 500 * np.arange(sr * 2) / sr) * 32767).astype(np.int16).tobytes())
    m = _save(project, [_shot("shot_01", 1, audio={"mode": "voiceover_external", "line": "x"},
                              voiceover_path="assets/audio/vo/shot_01.wav", edit_in=1.0, edit_out=6.0)])
    seg = timeline.compute(project, m, cfg)[0]
    assert seg["source"] == "manual" and seg["vo_path"] is not None
    assert abs(seg["duration"] - 5.0) < 0.05


def test_auto_select_does_not_block_seam_or_voiceover_fit(project, cfg):
    clips = project / "assets" / "clips"
    a = make_clip(clips / "shot_01.mp4", seconds=8)
    media.run_ffmpeg(["-ss", "5.0", "-i", str(a), "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
                      "-c:a", "aac", str(clips / "shot_02.mp4")])
    # Shot 01 có edit_in/edit_out do auto-select đặt (khớp auto_selection) → không bị coi là manual khóa cứng
    s1 = _shot(
        "shot_01", 1, transition_to_next="INTRA_SCENE_CONTINUE",
        edit_in=1.75, edit_out=6.25,
        auto_selection={"take": 1, "edit_in": 1.75, "edit_out": 6.25, "window": [0.0, 8.0]},
    )
    s2 = _shot("shot_02", 2)
    m = _save(project, [s1, s2])
    segs = timeline.compute(project, m, cfg)
    assert abs(segs[0]["tout"] - 5.0) <= 0.1  # _find_seam vẫn chạy để tìm frame khớp tại 5.0s


def test_audio_clipping_sanitizer_in_filtergraph():
    seg = {
        "duration": 4.0, "has_audio": True, "tin": 0.5,
        "shot": {"selected_take": 1, "takes": [{"take": 1, "qa": {"technical": {"findings": [{"code": "AUDIO_CLIPPING"}]}}}]},
    }
    chain = render._audio_chain(0, seg)
    assert "volume=-4.5dB,lowpass=f=7500" in chain
