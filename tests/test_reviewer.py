import json

import pytest

from conftest import make_clip
from studio import cli, qa
from studio import manifest as mf

AGENT_VARS = ("CLAUDECODE", "AI_AGENT", "STUDIO_REVIEWER", "GEMINI_API_KEY", "GOOGLE_API_KEY")


@pytest.fixture
def clean_env(monkeypatch):
    for k in AGENT_VARS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("studio.config.load_dotenv", lambda *a, **k: None)  # không đọc key thật từ .env
    return monkeypatch


def test_inside_claude_code_uses_agent(clean_env, cfg):
    clean_env.setenv("CLAUDECODE", "1")
    clean_env.setenv("AI_AGENT", "claude-code_x")
    rv = qa.detect_reviewer(cfg)
    assert rv["mode"] == "agent" and rv["agent"] == "claude-code_x"


def test_standalone_without_key_is_manual(clean_env, cfg):
    assert qa.detect_reviewer(cfg)["mode"] == "manual"


def test_explicit_override_wins(clean_env, cfg):
    clean_env.setenv("CLAUDECODE", "1")
    assert qa.detect_reviewer(cfg, "api")["mode"] == "api"
    clean_env.setenv("STUDIO_REVIEWER", "agent")
    clean_env.delenv("CLAUDECODE")
    assert qa.detect_reviewer(cfg)["mode"] == "agent"  # vd. Antigravity: đặt STUDIO_REVIEWER=agent


def test_validate_vision_result():
    assert qa.validate_vision_result({"verdict": "pass", "overall_score_1_10": 8}) == []
    errs = qa.validate_vision_result({"verdict": "retake", "overall_score_1_10": 11})
    assert len(errs) == 2  # điểm ngoài khoảng + thiếu retake_advice


def test_agent_review_flow_updates_status(clean_env, project, capsys):
    clean_env.setenv("CLAUDECODE", "1")
    make_clip(project / "assets" / "clips" / "shot_01.mp4", seconds=5)
    m = mf.load(project)
    m["project_slug"] = "proj"
    m["shots"] = [{"shot_id": "shot_01", "order": 1, "clip_output_path": "assets/clips/shot_01.mp4",
                   "status": "qa_pass", "subjects": ["CHAR_A"], "veo_prompt": "A shot",
                   "qa": {"technical": {"verdict": "pass"}}}]
    mf.save(project, m)

    cli.main(["qa-vision", "--project", str(project)])
    res = json.loads(capsys.readouterr().out)
    assert res["reviewer"]["mode"] == "agent" and "agent_instructions" in res
    result_path = res["shots"][0]["result_path"]

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({"verdict": "retake", "overall_score_1_10": 3, "identity_match": [],
                   "retake_advice": "Dùng ảnh tham chiếu"}, f)
    cli.main(["qa-vision-submit", "--project", str(project)])
    sub = json.loads(capsys.readouterr().out)
    assert sub["submitted"][0]["status"] == mf.STATUS_QA_FAIL
    shot = mf.load(project)["shots"][0]
    assert shot["qa"]["vision"]["reviewer"].startswith("agent:")


def test_project_lock_serializes(project):
    import threading, time
    from studio import manifest as mf
    order = []

    def hold():
        with mf.ProjectLock(project):
            order.append("A-start"); time.sleep(1.0); order.append("A-end")

    th = threading.Thread(target=hold); th.start(); time.sleep(0.2)
    with mf.ProjectLock(project, poll=0.1):
        order.append("B")
    th.join()
    assert order == ["A-start", "A-end", "B"]
