from studio import manifest as mf
from studio import progress


def _proj(project, **extra):
    m = mf.load(project)
    m.update({"project_slug": "proj", "beats": [{"beat_id": "b01", "order": 1, "narration": "Hi."}], **extra})
    m["shots"] = [{"shot_id": "s1", "order": 1, "beat": "b01", "veo_prompt": "x", "generation_mode": "text"}]
    mf.save(project, m)
    return m


def test_stage_flags_pending_flow_job_before_anything_else(project, cfg):
    m = _proj(project, flow_jobs=[{"shot": "s1", "kind": "video", "count": 2, "credits": 200, "at": "2026-10-20T09:00"}])
    st = progress.stage(project, m)
    assert st["step"] == 5 and "flow-harvest" in st["commands"][0] and "KHÔNG gửi tạo lại" in st["detail"]


def test_stage_waits_for_storyboard_approval(project, cfg):
    st = progress.stage(project, _proj(project))
    assert st["needs_user"] and "storyboard" in st["title"]


def test_progress_md_lists_missing_media_and_notes(project, cfg):
    m = _proj(project, music_path="assets/audio/music/x.wav")
    progress.add_note(m, "Chốt giọng Charon", cfg, "decision")
    progress.log_command(m, "voiceover", ["voiceover", "--project", "proj"], cfg)
    md = progress.render(project, m, cfg)
    assert "assets/audio/music/x.wav" in md and "Chốt giọng Charon" in md and "resume" in md
    assert progress.missing_media(project, m) == [("assets/audio/music/x.wav", "nhạc nền")]


def test_other_machine_warning(cfg, monkeypatch):
    monkeypatch.setenv("STUDIO_MACHINE", "may-cong-ty")
    m = {"last_activity": {"at": progress.now(), "machine": "may-nha", "command": "flow-harvest"}}
    assert progress.other_machine_active(m, cfg)["machine"] == "may-nha"
    m["last_activity"]["machine"] = "may-cong-ty"
    assert progress.other_machine_active(m, cfg) == {}


def test_media_push_pull_roundtrip(project, cfg, tmp_path, monkeypatch):
    m = _proj(project, music_path="assets/audio/music/x.wav")
    f = project / "assets/audio/music/x.wav"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"RIFF....")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", str(tmp_path / "shared"))
    assert progress.sync_media(project, m, cfg, "push")["copied"] == 1
    f.unlink()
    assert progress.sync_media(project, m, cfg, "pull")["copied"] == 1 and f.read_bytes() == b"RIFF...."


def test_media_sync_via_rclone_remote(project, cfg, tmp_path, monkeypatch):
    import pytest
    try:
        progress.rclone_exe()
    except Exception:
        pytest.skip("rclone chưa cài")
    m = _proj(project, music_path="assets/audio/music/x.wav")
    f = project / "assets/audio/music/x.wav"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"RIFF-rclone")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", "rclone:" + (tmp_path / "remote").as_posix())
    assert progress.sync_media(project, m, cfg, "push")["copied"] == 1
    f.unlink()
    res = progress.sync_media(project, m, cfg, "pull")
    assert res["copied"] == 1 and f.read_bytes() == b"RIFF-rclone"
