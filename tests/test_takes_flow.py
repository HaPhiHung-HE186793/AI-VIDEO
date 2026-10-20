from conftest import make_clip
from studio import takes
from studio.flow import match_row_to_shot, norm_text

PROMPTS = {
    "shot_04": "Close-up profile of the head, 85mm lens, slow push-in. Rex is a massive adult Tyrannosaurus rex...",
    "shot_08": "Low-angle close-up, 65mm lens, slow push-in. Rex is a massive adult Tyrannosaurus rex...",
    "shot_05": "Medium close-up from the front, 50mm lens, very slow push-in. Rex is a massive adult...",
}


def test_row_matching_uses_prompt_shown_in_row():
    row = "play_circle play_circle download undo delete Low-angle close-up, 65mm lens, slow push-in. Rex is a massi… " \
          "Ngày tạo: 19 thg 10, 2026 Veo 3.1 - Quality • 720p"
    assert match_row_to_shot(row, PROMPTS) == "shot_08"
    assert match_row_to_shot("Close-up profile of the head, 85mm lens, slow…", PROMPTS) == "shot_04"
    assert match_row_to_shot("Ảnh đã tải lên 16:9", PROMPTS) is None


def test_shared_prompt_prefix_picks_longest_match():
    prompts = {"shot_01": "Extreme close-up macro shot, 100mm lens: the closed eye of the Tyrannosaurus rex, heavy lid",
               "shot_04": "Extreme close-up macro shot, 100mm lens: the two large nostrils and the scarred upper snout"}
    row_eye = "download Extreme close-up macro shot, 100mm lens: the closed eye of the Tyrannosaurus… Nano Banana Pro"
    row_nose = "download Extreme close-up macro shot, 100mm lens: the two large nostrils and the scar… 16:9"
    assert match_row_to_shot(row_eye, prompts) == "shot_01"
    assert match_row_to_shot(row_nose, prompts) == "shot_04"
    # Hàng chỉ hiện phần mở đầu chung của hai prompt → hòa điểm → không đoán.
    assert match_row_to_shot("Extreme close-up macro shot, 100mm lens: …", prompts) is None


def test_norm_text():
    assert norm_text("  A\n b\tC ") == "a b c"


def _vision(score, defects=(), verdict="pass", identity=8):
    return {"identity_score_1_10": identity, "prompt_adherence_1_10": 8, "aesthetic_1_10": 8,
            "overall_score_1_10": score, "defects": list(defects), "verdict": verdict}


def _take(n, vision, dur=8.0, tech="warn"):
    return {"take": n, "qa": {"duration": dur, "technical": {"verdict": tech}, "vision": vision}}


def test_clean_windows_avoid_major_only():
    defects = [{"severity": "major", "t_from": 2.5, "t_to": 3.5}, {"severity": "minor", "t_from": 6, "t_to": 7}]
    assert takes.clean_windows(8.0, defects) == [(0.0, 2.25), (3.75, 8.0)]


def test_choose_prefers_clean_take_and_cuts_around_defect(cfg):
    open_jaw = {"rule": "mouth_closed", "severity": "major", "t_from": 2.5, "t_to": 3.5}
    shot = {"shot_id": "s", "takes": [
        _take(1, _vision(9, [open_jaw])),              # điểm cao hơn nhưng lỗi giữa clip
        _take(2, _vision(8)),                          # sạch
    ]}
    d = takes.choose_take(shot, need_sec=5.0, cfg=cfg)
    assert d["take"] == 2
    # take 1 vẫn chọn được nếu chỉ cần 4s (đoạn 3.75–8.0 = 4.25s) — và cửa sổ phải nằm ngoài lỗi
    d1 = takes.choose_take({"shot_id": "s", "takes": [_take(1, _vision(9, [open_jaw]))]}, need_sec=4.0, cfg=cfg)
    assert d1["take"] == 1 and d1["edit_in"] >= 3.75 and d1["edit_out"] <= 8.0


def test_choose_marks_retake_when_nothing_usable(cfg):
    bad = {"severity": "major", "t_from": 1.0, "t_to": 7.0, "rule": "identity"}
    shot = {"shot_id": "s", "takes": [_take(1, _vision(3, [bad], "retake")), _take(2, _vision(9), tech="fail"),
                                      {"take": 3, "qa": {}}]}
    d = takes.choose_take(shot, need_sec=4.0, cfg=cfg)
    assert d["retake"] and len(d["reasons"]) == 3


def test_minor_defects_lower_score(cfg):
    minor = {"severity": "minor", "t_from": 1, "t_to": 2, "rule": "anatomy"}
    shot = {"shot_id": "s", "takes": [_take(1, _vision(8, [minor, minor])), _take(2, _vision(8))]}
    assert takes.choose_take(shot, 4.0, cfg)["take"] == 2


def test_validate_take_result():
    assert takes.validate_take_result(_vision(8), 8.0) == []
    bad = _vision(11, [{"severity": "fatal", "t_from": 5, "t_to": 2}])
    errs = takes.validate_take_result(bad, 8.0)
    assert len(errs) >= 3


def test_take_sheet_has_timestamps(tmp_path):
    clip = make_clip(tmp_path / "c.mp4", seconds=6)
    sh = takes.take_sheet(clip, tmp_path / "sheet.jpg")
    assert sh["sheet"].exists() and len(sh["times"]) == 8 and sh["times"][-1] < 6.0


def test_rubric_merges_project_rules(cfg):
    proj = {"qa_rubric": [{"id": "mouth_closed", "check": "Miệng khép, môi che răng"}]}
    ids = [r["id"] for r in takes.rubric_for(proj, cfg)]
    assert "mouth_closed" in ids and "identity" in ids
    prompt = takes.build_take_prompt(proj, {"veo_prompt": "x"}, cfg, 8, 8.0)
    assert "mouth_closed" in prompt and "t_from" in prompt


def test_choose_take_respects_beat_share(cfg):
    shot = {"shot_id": "s", "takes": [_take(1, _vision(8))]}
    d = takes.choose_take(shot, need_sec=2.6, cfg=cfg, pref=2.6)
    assert abs((d["edit_out"] - d["edit_in"]) - 2.6) < 0.01


def test_round_robin_reference_paths_keeps_second_character_and_props():
    from studio import manifest as mf

    m = {
        "characters": [
            {"id": "CHAR_DAT", "reference_images": ["c/dat_front.png", "c/dat_34.png", "c/dat_exp.png"]},
            {"id": "CHAR_TAN", "reference_images": ["c/tan_front.png", "c/tan_34.png", "c/tan_exp.png"]},
        ],
        "environments": [{"id": "ENV_CAFE", "path": "e/cafe.png"}],
        "props": [{"id": "PROP_PHONE", "name": "smartphone", "path": "p/phone.png"}],
    }
    # Cảnh 2 nhân vật: cả 2 nhân vật đều phải có ảnh mặt chính diện trong 3 slot
    s_two = {"subjects": ["CHAR_DAT", "CHAR_TAN"], "environment": "ENV_CAFE"}
    refs_two = mf.shot_reference_paths(m, s_two, limit=3)
    assert refs_two == ["c/dat_front.png", "c/tan_front.png", "c/dat_34.png"]

    # Cảnh 2 nhân vật + đạo cụ: giữ cả 2 nhân vật + ảnh đạo cụ
    s_prop = {"subjects": ["CHAR_DAT", "CHAR_TAN"], "props": ["PROP_PHONE"], "environment": "ENV_CAFE"}
    refs_prop = mf.shot_reference_paths(m, s_prop, limit=3)
    assert refs_prop == ["c/dat_front.png", "c/tan_front.png", "p/phone.png"]

    # Cảnh 1 nhân vật: 2 góc nhân vật + 1 ảnh bối cảnh sạch
    s_one = {"subjects": ["CHAR_DAT"], "environment": "ENV_CAFE"}
    refs_one = mf.shot_reference_paths(m, s_one, limit=3)
    assert refs_one == ["c/dat_front.png", "c/dat_34.png", "e/cafe.png"]


def test_detect_rubber_stamp_blocks_uniform_batch(project, capsys):
    import json
    import pytest
    from studio import cli, manifest as mf

    m = mf.load(project)
    shots = []
    for i in range(1, 7):
        sid = f"shot_{i:02d}"
        shots.append({
            "shot_id": sid, "order": i,
            "takes": [{"take": 1, "path": f"assets/clips/takes/{sid}_take01.mp4", "qa": {"duration": 8.0}}],
        })
        rp = takes.take_paths(project, sid, 1)["result"]
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "identity_score_1_10": 9, "prompt_adherence_1_10": 9, "aesthetic_1_10": 9,
            "overall_score_1_10": 9, "defects": [], "verdict": "pass",
            "notes": f"{sid} take 1 verified via contact sheet inspection: character identity matches prompt.",
        }), encoding="utf-8")
    m["shots"] = shots
    mf.save(project, m)

    with pytest.raises(SystemExit) as exc:
        cli.main(["qa-takes-submit", "--project", str(project)])
    assert exc.value.code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "RUBBER_STAMP_DETECTED" and len(out["issues"]) == 2


def test_keyframe_uid_and_daisy_chaining(tmp_path):
    from studio import manifest as mf

    m = {
        "project_slug": "podcast-giac-mo-thiep-cuoi",
        "shots": [
            {
                "shot_id": "shot_01",
                "order": 1,
                "generation_mode": "first_last",
                "first_frame_path": "assets/frames/KF_PGMTC_S01_START.png",
                "last_frame_path": "assets/frames/KF_PGMTC_S01_END.png",
                "transition_to_next": "INTRA_SCENE_CONTINUE",
            },
            {
                "shot_id": "shot_02",
                "order": 2,
                "generation_mode": "first_frame",
                "first_frame_path": "",
                "chain_from_prev": True,
            },
        ],
    }
    assert mf.project_code(m) == "PGMTC"
    assert mf.keyframe_uid(m, "shot_01", "start") == "KF_PGMTC_S01_START"
    assert mf.keyframe_uid(m, "shot_01", "end") == "KF_PGMTC_S01_END"
    assert mf.asset_uid(m, "CHAR_NAM", "front") == "REF_PGMTC_CHAR_NAM_FRONT"

    linked = mf.resolve_chained_keyframes(m)
    assert len(linked) == 1
    assert m["shots"][1]["first_frame_path"] == "assets/frames/KF_PGMTC_S01_END.png"


def test_build_prompts_generates_first_and_last_keyframe_prompts(project, capsys):
    import json
    from studio import cli, manifest as mf

    m = mf.load(project)
    m["project_slug"] = "podcast-giac-mo-thiep-cuoi"
    m["characters"] = [{"id": "CHAR_NAM", "short_name": "Nam", "identity_line": "a 28-year-old man in an olive shirt"}]
    m["environments"] = [{"id": "ENV_STUDIO", "identity_line": "a warm podcast studio with acoustic panels"}]
    m["shots"] = [
        {
            "shot_id": "shot_01",
            "order": 1,
            "camera": "Medium shot, 50mm lens, slow push-in",
            "subjects": ["CHAR_NAM"],
            "environment": "ENV_STUDIO",
            "action": "Nam places a red wedding invitation card on the wooden table",
            "end_action": "Nam rests his hand beside the red wedding invitation card on the table",
            "lighting": "warm tungsten key light",
            "audio": {"mode": "voiceover_external", "line": "Tối qua tao mơ thấy đám cưới."},
            "generation_mode": "first_last",
            "transition_to_next": "INTRA_SCENE_CONTINUE",
        },
        {
            "shot_id": "shot_02",
            "order": 2,
            "camera": "Close-up shot, 85mm lens",
            "subjects": ["CHAR_NAM"],
            "environment": "ENV_STUDIO",
            "action": "Nam looks down at the card thoughtfully",
            "lighting": "warm tungsten key light",
            "audio": {"mode": "voiceover_external", "line": "Tấm thiệp đỏ nằm ngay trên bàn."},
            "generation_mode": "first_frame",
            "chain_from_prev": True,
        },
    ]
    mf.save(project, m)

    cli.main(["build-prompts", "--project", str(project)])
    out = json.loads(capsys.readouterr().out)
    assert "shot_01:start" in out["built_keyframe_prompts"]
    assert "shot_01:end" in out["built_keyframe_prompts"]
    m2 = mf.load(project)
    s1, s2 = m2["shots"][0], m2["shots"][1]
    assert s1["first_frame_path"] == "assets/frames/KF_PGMTC_S01_START.png"
    assert s1["last_frame_path"] == "assets/frames/KF_PGMTC_S01_END.png"
    assert "start frame reference" in s1["last_frame_prompt"].lower()
    # Shot 2 tự động nối từ last_frame_path của Shot 1 (Daisy-Chain)
    assert s2["first_frame_path"] == "assets/frames/KF_PGMTC_S01_END.png"
    # Keyframe-locked shot không nhép miệng -> giảm độ khó, định tuyến sang Fast
    assert s2["routing"]["tier"] == "fast"


def test_stage_unique_file_and_sort_shots_for_flow(tmp_path):
    from studio import cli, flow as fl

    char_dir = tmp_path / "assets" / "characters" / "nam"
    char_dir.mkdir(parents=True)
    front = char_dir / "front.png"
    front.write_bytes(b"fake-png")

    staged = fl.stage_unique_file(front, stage_dir=tmp_path / ".staged")
    assert staged.name == "REF_NAM_FRONT.png"
    assert staged.exists()

    explicit = fl.stage_unique_file(front, stage_dir=tmp_path / ".staged", uid="KF_PGMTC_S01_START")
    assert explicit.name == "KF_PGMTC_S01_START.png"

    shots = [
        {"shot_id": "shot_01", "generation_mode": "first_frame", "routing": {"label": "Veo 3.1 - Quality"}},
        {"shot_id": "shot_02", "generation_mode": "first_frame", "routing": {"label": "Veo 3.1 - Fast"}},
        {"shot_id": "shot_03", "generation_mode": "first_frame", "routing": {"label": "Veo 3.1 - Quality"}},
        {"shot_id": "shot_04", "generation_mode": "first_frame", "routing": {"label": "Veo 3.1 - Fast"}},
    ]
    sorted_shots = cli.sort_shots_for_flow(shots, "video", "Veo 3.1 - Quality")
    # Các shot cùng model được gom liền nhau để không phải mở Settings đổi qua lại ở mỗi shot
    labels = [s["routing"]["label"] for s in sorted_shots]
    assert labels == ["Veo 3.1 - Fast", "Veo 3.1 - Fast", "Veo 3.1 - Quality", "Veo 3.1 - Quality"]


def test_build_continuity_sheets(tmp_path):
    from pathlib import Path
    import numpy as np
    from studio import media

    cv2 = media.cv2_module()
    shots = []
    for i in range(1, 4):
        sid = f"shot_{i:02d}"
        shots.append({"shot_id": sid, "selected_take": 1, "takes": [{"take": 1}]})
        sp = takes.take_paths(tmp_path, sid, 1)["sheet"]
        sp.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(sp), np.full((240, 640, 3), 80 * i, dtype=np.uint8))

    sheets = takes.build_continuity_sheets(tmp_path, shots, batch_size=2)
    assert len(sheets) == 2
    assert Path(sheets[0]).exists()
