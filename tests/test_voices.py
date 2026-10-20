from studio import audio as au
from studio import media, prompts


def _voice(path, f0, tilt, seconds=4.0, seed_shift=0.0):
    """Giọng tổng hợp: chuỗi hài âm f0 (độ dốc phổ `tilt`) + rung cao độ + ngắt âm tiết."""
    harmonics = "+".join(f"pow({tilt},{k})*sin(2*PI*{k}*{f0}*t)" for k in range(1, 12))
    expr = f"0.15*({harmonics})*gt(sin(2*PI*3*t+{seed_shift}),-0.3)"
    media.run_ffmpeg(["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=16000:d={seconds}", "-ac", "1", str(path)])
    return path


def test_same_voice_matches_and_different_voice_does_not(tmp_path):
    a = au.voice_profile(_voice(tmp_path / "a.wav", 115, 0.7))
    b = au.voice_profile(_voice(tmp_path / "b.wav", 118, 0.7, seed_shift=1.3))   # cùng giọng, câu khác
    c = au.voice_profile(_voice(tmp_path / "c.wav", 210, 0.35))                  # giọng cao, sáng hơn
    assert au.compare_voice_profiles(a, b)["verdict"] == "rất có thể cùng giọng"
    assert au.compare_voice_profiles(a, c)["verdict"] == "khác giọng rõ"


def test_silence_reports_insufficient_data(tmp_path):
    p = tmp_path / "s.wav"
    media.run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "3", str(p)])
    assert au.compare_voice_profiles(au.voice_profile(p), au.voice_profile(p))["verdict"] == "không đủ dữ liệu"


def _project():
    return {"language": "vi", "narrator_voice": "Charon",
            "characters": [{"id": "LOGIC", "name": "Logic", "voice": "Alnilam"}, {"id": "EMO", "name": "Emo"}]}


def test_shot_voice_resolution():
    p = _project()
    assert prompts.shot_voice(p, {"audio": {"mode": "veo_dialogue", "speaker": "LOGIC"}}) == "Alnilam"
    assert prompts.shot_voice(p, {"audio": {"mode": "veo_narration"}}) == "Charon"
    assert prompts.shot_voice(p, {"audio": {"mode": "veo_dialogue", "speaker": "LOGIC", "voice": "Puck"}}) == "Puck"
    assert prompts.shot_voice(p, {"audio": {"mode": "sfx_only"}}) == ""


def test_lint_warns_only_when_voice_not_fixed(cfg):
    p = _project()
    base = {"shot_id": "s", "veo_prompt": "Medium shot of a brain cell talking in a neon room, 2D cartoon. " * 3}
    fixed = {**base, "audio": {"mode": "veo_dialogue", "speaker": "LOGIC", "line": "Xin chào"}}
    loose = {**base, "audio": {"mode": "veo_dialogue", "speaker": "EMO", "line": "Xin chào"}}
    assert "NO_FIXED_VOICE" not in {f["code"] for f in prompts.lint_shot(p, fixed, cfg)}
    assert "NO_FIXED_VOICE" in {f["code"] for f in prompts.lint_shot(p, loose, cfg)}


def test_transcript_match_handles_numbers():
    assert au.words_match("Sixty-six million years ago, this was his kingdom.",
                          "66 million years ago, this was his kingdom.") == 1.0
    assert au.words_match("Patience is his greatest weapon.", "Patience is a weapon.") < 0.9


def test_fit_narration_removes_long_pause_and_speeds_up(tmp_path):
    import numpy as np
    sr = 24000
    tone = lambda s: (0.3 * np.sin(2 * np.pi * 180 * np.arange(int(sr * s)) / sr) * 32767).astype(np.int16)  # noqa: E731
    gap = np.zeros(int(sr * 2.0), dtype=np.int16)
    src = tmp_path / "raw.wav"
    au._write_wav(src, np.concatenate([tone(3), gap, tone(3)]).tobytes(), sr)   # 8s, có 2s lặng
    info = au.fit_narration(src, tmp_path / "fit.wav", max_sec=5.0)
    assert info["before_sec"] == 8.0
    assert info["tempo"] > 1.0 and abs(info["after_sec"] - 5.0) < 0.15       # rút lặng → 6.3s → tăng tốc về 5s
