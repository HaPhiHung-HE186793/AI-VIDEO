from studio import prompts


def _project():
    return {
        "language": "vi",
        "style_line": "2D flat cartoon animation, bold clean outlines",
        "characters": [
            {"id": "LOGIC", "name": "Logic", "identity_line": "a nerdy pink brain cell with thick glasses and a blue tie",
             "reference_images": ["assets/characters/LOGIC.png"]},
            {"id": "EMO", "name": "Emo", "identity_line": "a playful brain cell in a backward green cap",
             "reference_images": ["assets/characters/EMO.png"]},
        ],
        "environments": [{"id": "ENV", "name": "Brain HQ", "identity_line": "a neon brain control room"}],
    }


def test_build_prompt_is_structured_and_affirmative():
    shot = {
        "camera": "Medium two-shot, 35mm, static", "subjects": ["LOGIC", "EMO"],
        "action": "Logic taps the blank screen while Emo sips a boba tea", "environment": "ENV",
        "lighting": "warm practical light",
        "audio": {"mode": "veo_dialogue", "speaker": "LOGIC", "line": "Hạn chót là tối nay rồi!", "delivery": "urgent",
                  "sfx": "soft console beeps"},
    }
    p = prompts.build_prompt(_project(), shot)
    assert p.startswith("Medium two-shot")
    assert "a nerdy pink brain cell with thick glasses and a blue tie" in p
    assert 'Logic speaks to camera in Vietnamese, urgent: "Hạn chót là tối nay rồi!"' in p
    assert "Emo listens with mouth closed" in p
    assert "Logic is a nerdy pink brain cell" in p
    assert "A neon brain control room" in p
    assert p.endswith("No subtitles, no on-screen text.")
    assert len(p) < 750


def test_external_voiceover_keeps_veo_silent_of_speech():
    shot = {"camera": "Wide shot", "action": "Fog drifts", "audio": {"mode": "voiceover_external", "line": "Narration", "sfx": "wind"}}
    p = prompts.build_prompt(_project(), shot)
    assert "Narration" not in p
    assert "Ambient sound only: wind." in p


def test_clean_legacy_prompt_strips_boilerplate():
    legacy = ("Wide shot of a T-Rex walking, no subtitles, no on-screen text. Continuous unbroken 3-phase anatomical motion across "
              "the full 0.0s to 8.0s clip matching the narration duration (never finish the action early and never stop, freeze, "
              "or park in a static rest pose while speaking). Consistent 360-degree character model geometry and skin texture "
              "across all angles, accurate limb and jaw articulation, no extra limbs, no morphing.")
    cleaned, n = prompts.clean_legacy_prompt(legacy)
    assert n == 2
    assert cleaned == "Wide shot of a T-Rex walking. No subtitles, no on-screen text."


def test_lint_flags_legacy_problems(cfg):
    proj = _project()
    shot = {"shot_id": "s1", "subjects": ["LOGIC"], "generation_mode": "text",
            "veo_prompt": "Strict v10.0 masterpiece 8k shot. (0.0s-2.8s) a; (2.8s-5.6s) b; (5.6s-8.0s) c. NEVER float, "
                          "never morph, zero bones, no skeleton. " + "x" * 900,
            "audio": {"mode": "veo_narration", "line": "short"}}
    codes = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert {"PROMPT_TOO_LONG", "JUNK_TOKENS", "TOO_MANY_NEGATIONS", "TOO_MANY_PHASES",
            "IDENTITY_LINE_DRIFT", "NO_IDENTITY_REFERENCE", "NARRATION_IN_VEO"} <= codes


def test_lint_line_length_vietnamese(cfg):
    proj = _project()
    line = " ".join(["chữ"] * 25)
    shot = {"shot_id": "s1", "veo_prompt": "Medium shot of a room, warm light, 2D cartoon style. " * 4,
            "audio": {"mode": "veo_dialogue", "line": line}}
    codes = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "LINE_TOO_LONG" in codes


def test_bite_is_not_hijacked_by_dinosaur_rules():
    """Engine cũ chèn câu 'T-Rex ... 6-ton' vào MỌI prompt có chữ bite — không được tái diễn."""
    shot = {"camera": "Close-up", "action": "Emo takes a bite of a sandwich", "subjects": ["EMO"]}
    p = prompts.build_prompt(_project(), shot)
    assert "T-Rex" not in p and "6-ton" not in p


def test_complexity_routing(cfg):
    calm = {"action": "clouds drift over a valley", "camera": "wide aerial"}
    busy = {"action": "Rex grabs a branch and shakes it", "camera": "extreme close-up", "subjects": ["A", "B"]}
    s1, _ = prompts.complexity_score(calm, 3, 10)
    s2, _ = prompts.complexity_score(busy, 3, 10)
    assert prompts.route_model(s1, cfg)["tier"] == "fast"
    assert prompts.route_model(s2, cfg)["tier"] == "quality"


def test_normalize_lang():
    assert prompts.normalize_lang("Tiếng Việt") == "vi"
    assert prompts.normalize_lang("English") == "en"
    assert prompts.normalize_lang("ko") == "ko"


def test_cross_attribute_lock_and_first_last_camera_alignment(cfg):
    proj = {
        "language": "vi",
        "style_line": "2D anime style, clean line art",
        "characters": [
            {"id": "NAM", "name": "Nam", "identity_line": "a 24-year-old man with short black hair and round glasses in an olive hoodie",
             "reference_images": ["assets/characters/NAM.png"]},
            {"id": "TAN", "name": "Vu Tan", "identity_line": "a 24-year-old man with short parted black hair in a cream polo shirt",
             "reference_images": ["assets/characters/TAN.png"]},
            {"id": "LINH", "name": "Linh", "identity_line": "a 23-year-old woman with long dark hair in a beige cardigan",
             "reference_images": ["assets/characters/LINH.png"]},
        ],
        "environments": [{"id": "CAFE", "name": "Rooftop Cafe", "identity_line": "a cozy rooftop cafe at twilight"}],
    }
    shot = {
        "shot_id": "shot_13",
        "generation_mode": "first_last",
        "first_frame_path": "assets/frames/KF_S13_START.jpg",
        "last_frame_path": "assets/frames/KF_S13_END.jpg",
        "camera": "Medium three-shot, 35mm lens, gentle push-in",
        "subjects": ["TAN", "NAM", "LINH"],
        "action": "Vu Tan and Linh comfort pouting Nam across the table",
        "environment": "CAFE",
        "lighting": "warm golden string lights",
        "audio": {"mode": "voiceover_external", "sfx": "laughter"},
    }
    veo_p = prompts.build_prompt(proj, shot)
    assert "steady locked-off framing, single continuous take" in veo_p
    assert "push-in" not in veo_p.lower()
    assert "On the left, Vu Tan is" in veo_p
    assert "In the center, Nam is" in veo_p
    assert "On the right, Linh is" in veo_p
    assert "Only Nam wears glasses while Vu Tan and Linh keep bare eyes" in veo_p
    assert "only Linh has long hair while Vu Tan and Nam keep short hair" in veo_p
    shot["veo_prompt"] = veo_p
    codes = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "TOO_MANY_NEGATIONS" not in codes
    assert "FIRST_LAST_CAMERA_MISMATCH" not in codes
    neg = prompts.effective_negative_prompt(proj, shot)
    assert "cross-dissolve" in neg and "attribute swapping" in neg


def test_detect_mid_clip_dissolve_and_daisy_chain_choose_take(cfg):
    import numpy as np
    from studio import qa, takes

    fps = 24.0
    fa = np.full((180, 320), 30, dtype=np.uint8)
    fb = np.full((180, 320), 210, dtype=np.uint8)
    frames = [fa.copy() for _ in range(40)]
    for k in range(24):
        alpha = (k + 1) / 25.0
        frames.append(((1.0 - alpha) * fa + alpha * fb).astype(np.uint8))
    frames.extend([fb.copy() for _ in range(40)])
    dissolves = qa.detect_mid_clip_dissolve(frames, fps)
    assert len(dissolves) == 1

    shot_a = {
        "shot_id": "shot_01",
        "takes": [{"take": 1, "qa": {"duration": 8.0, "technical": {"verdict": "pass"},
                                     "vision": {"verdict": "pass", "overall_score_1_10": 9,
                                                "identity_score_1_10": 9, "prompt_adherence_1_10": 9, "defects": []}}}],
    }
    shot_b = {
        "shot_id": "shot_02",
        "chain_from_prev": True,
        "takes": [{"take": 1, "qa": {"duration": 8.0, "technical": {"verdict": "pass"},
                                     "vision": {"verdict": "pass", "overall_score_1_10": 9,
                                                "identity_score_1_10": 9, "prompt_adherence_1_10": 9, "defects": []}}}],
    }
    res_a = takes.choose_take(shot_a, 4.5, cfg, pref=4.5, chain_next=True)
    res_b = takes.choose_take(shot_b, 4.5, cfg, pref=4.5, chain_next=False)
    assert res_a["edit_out"] == 8.0 and res_a["edit_in"] == 3.5
    assert res_b["edit_in"] == 0.0 and res_b["edit_out"] == 4.5
