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


def test_multi_waypoint_expansion_and_star_anchoring(tmp_path, cfg):
    from studio import manifest as mf

    proj_data = {
        "project_slug": "test-xianxia-fight",
        "language": "vi",
        "style_line": "3D cel-shaded anime style",
        "characters": [
            {"id": "HERO", "name": "Han Li", "identity_line": "a young cultivator in azure robes with short black hair",
             "reference_images": ["assets/characters/HERO.png"]},
        ],
        "environments": [{"id": "PEAK", "name": "Cloud Peak", "identity_line": "a misty mountain peak at dawn"}],
        "shots": [
            {
                "shot_id": "shot_03",
                "order": 1,
                "beat": "b01",
                "generation_mode": "first_last",
                "camera": "Medium wide shot, 35mm lens",
                "subjects": ["HERO"],
                "environment": "PEAK",
                "lighting": "golden dawn rim light",
                "start_action": "Han Li stands calm on the stone platform with hands behind his back",
                "mid_actions": [
                    "Han Li raises his right hand forming a glowing golden sword seal",
                    "Seventy-two emerald flying swords materialize in a lotus formation around Han Li",
                    "Han Li points forward launching the emerald sword array in a golden shockwave",
                ],
                "end_action": "Han Li lowers his hand as the sword array streaks into the distant clouds",
                "action": "Han Li summons and launches the emerald sword formation",
                "audio": {"mode": "voiceover_external", "sfx": "sword hum and thunder"},
            }
        ],
    }
    expanded = mf.expand_shot_waypoints(proj_data)
    assert len(expanded) == 1
    assert expanded[0]["waypoints"] == 3
    assert expanded[0]["sub_shots"] == ["shot_03a", "shot_03b", "shot_03c", "shot_03d"]
    assert len(proj_data["shots"]) == 4

    f0_rel = proj_data["shots"][0]["first_frame_path"]
    f0_file = tmp_path / f0_rel
    f0_file.parent.mkdir(parents=True, exist_ok=True)
    f0_file.write_bytes(b"fake_f0")

    prefixes = set()
    for idx, s in enumerate(proj_data["shots"]):
        assert s["anchor_frame_shot"] == "shot_03a"
        assert mf.root_anchor_frame_path(proj_data, s, tmp_path) == f0_file
        s["veo_prompt"] = prompts.build_prompt(proj_data, s)
        s["last_frame_prompt"] = prompts.build_last_frame_prompt(proj_data, s)
        prefixes.add(s["last_frame_prompt"][:60])
        score, _ = prompts.complexity_score(s, idx, len(proj_data["shots"]))
        assert prompts.route_model(score, cfg)["tier"] == "fast"
    assert len(prefixes) == 4


def test_large_ensemble_12_characters_and_crowd_staging(tmp_path, cfg):
    import cv2
    import numpy as np
    from studio import manifest as mf

    names = [
        ("CHAR_DAT", "Dat", "a 23-year-old Vietnamese guy with messy black hair, round glasses, and an olive hoodie"),
        ("CHAR_TAN", "Tan", "a 23-year-old Vietnamese guy with middle-part black hair and a cream polo shirt"),
        ("CHAR_LINH", "Linh", "a gentle young Vietnamese woman with long straight black hair and a beige cardigan"),
        ("CHAR_HOANG_ANH", "Hoang Anh", "a lively 23-year-old Vietnamese guy with a short fade haircut and a varsity jacket"),
        ("CHAR_VIET_DUONG", "Viet Duong", "a cheerful 23-year-old Vietnamese guy with a buzz cut and a blue denim jacket"),
        ("CHAR_NGUYEN_PHONG", "Nguyen Phong", "a funny 23-year-old Vietnamese guy with wavy black hair and a mustard yellow polo"),
        ("CHAR_DUY_KHIEM", "Duy Khiem", "a cool 23-year-old Vietnamese guy with side-parted hair and a maroon plaid shirt"),
        ("CHAR_VIET_DUC", "Viet Duc", "a calm 23-year-old Vietnamese guy with neat short hair, square glasses, and a navy sweater"),
        ("CHAR_QUANG_BINH", "Quang Binh", "a sporty 23-year-old Vietnamese guy with spiky black hair and a grey zip hoodie"),
        ("CHAR_PHI_HUNG", "Phi Hung", "an energetic 23-year-old Vietnamese guy with curly black hair and a black bomber jacket"),
        ("CHAR_NHAT_ANH", "Nhat Anh", "a tall 23-year-old Vietnamese guy with undercut black hair and a white linen shirt"),
        ("CHAR_MINH_QUAN", "Minh Quan", "a smiling 23-year-old Vietnamese guy with parted hair and a teal crewneck tee"),
    ]
    chars = []
    for idx, (cid, name, id_line) in enumerate(names):
        rel = f"assets/characters/{cid}_front.png"
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        img = np.full((300, 240, 3), 40 + idx * 15, dtype=np.uint8)
        cv2.imwrite(str(p), img)
        chars.append({"id": cid, "name": name, "short_name": name, "identity_line": id_line, "reference_images": [rel]})

    proj = {
        "project_slug": "reunion-12",
        "language": "vi",
        "style_line": "2D indie animated cartoon, bold clean outlines",
        "characters": chars,
        "environments": [{"id": "ENV_CAFE", "name": "Rooftop Cafe", "identity_line": "a dreamy rooftop cafe with long wooden table"}],
    }
    shot = {
        "shot_id": "shot_04",
        "generation_mode": "first_last",
        "first_frame_path": "assets/frames/KF_S04_START.jpg",
        "last_frame_path": "assets/frames/KF_S04_END.jpg",
        "camera": "Wide group shot, 35mm lens",
        "subjects": ["CHAR_DAT", "CHAR_TAN", "CHAR_LINH"],
        "ensemble_cast": [cid for cid, _, _ in names[3:]],
        "action": "Dat raises his iced coffee glass to toast Tan and Linh as the whole table cheers",
        "end_action": "Everyone around the long wooden table clinks glasses together laughing warmly",
        "environment": "ENV_CAFE",
        "lighting": "warm golden string lights",
        "audio": {"mode": "voiceover_external", "sfx": "cheering and clinking glasses"},
    }
    ff_p = prompts.build_first_frame_prompt(proj, shot)
    lf_p = prompts.build_last_frame_prompt(proj, shot)
    veo_p = prompts.build_prompt(proj, shot)
    shot["veo_prompt"] = veo_p

    # Cả 12 nhân vật có tên đều phải xuất hiện đầy đủ trong cả 3 tầng prompt
    for _, name, _ in names:
        assert name in ff_p
        assert name in lf_p
        assert name in veo_p

    # Nhãn vị trí Trái/Giữa/Phải đồng bộ cả 3 tầng + khóa thuộc tính tóc dài/ngắn + quần chúng nền đông vui
    assert "On the left, Dat is" in ff_p and "On the left, Dat is" in veo_p
    assert "All 12 named characters seated together around the main table from left to right:" in veo_p
    assert "neighboring tables are occupied by lively unnamed cafe patrons" in veo_p
    assert "then smoothly transitioning so Everyone around the long wooden table clinks glasses" in veo_p

    # Tự động ghép bảng Group Cast Sheet cho 12 nhân vật vào 1 slot ảnh tham chiếu
    refs = mf.shot_reference_paths(proj, shot, proj_dir=tmp_path, limit=3)
    assert any("_composites/group_cast_12p_" in r for r in refs)
    codes = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "PROMPT_TOO_LONG" not in codes
    assert "IDENTITY_LINE_DRIFT" not in codes


def test_script_to_cast_linter_catches_missing_named_characters(cfg):
    proj = {
        "language": "vi",
        "style_line": "2D cartoon",
        "audio_strategy": "voiceover_external",
        "characters": [
            {"id": "CHAR_DAT", "name": "Đạt", "short_name": "Dat", "identity_line": "a guy with glasses",
             "reference_images": ["a.png"]},
            {"id": "CHAR_HOANG_ANH", "name": "Hoàng Anh", "short_name": "Hoang Anh", "identity_line": "a guy in varsity jacket",
             "reference_images": ["b.png"]},
            {"id": "CHAR_VIET_DUONG", "name": "Việt Đường", "short_name": "Viet Duong", "identity_line": "a guy in denim jacket",
             "reference_images": ["c.png"]},
        ],
        "beats": [
            {
                "beat_id": "b05",
                "order": 1,
                "narration": "Hoàng Anh với Việt Đường ngồi cạnh phì cười, còn Nguyễn Phong với Duy Khiêm giơ máy quay cảnh Đạt ngồi dỗi!",
            }
        ],
        "shots": [
            {
                "shot_id": "shot_09",
                "beat": "b05",
                "generation_mode": "first_last",
                "first_frame_path": "f1.jpg",
                "last_frame_path": "f2.jpg",
                "camera": "Medium two-shot",
                "subjects": ["CHAR_HOANG_ANH", "CHAR_DAT"],
                "action": "Hoang Anh laughs at Dat",
                "veo_prompt": "Medium two-shot. Hoang Anh is a guy in varsity jacket. Dat is a guy with glasses.",
            }
        ],
    }
    findings = prompts.lint_project(proj, cfg)
    codes = {f["code"] for f in findings}
    assert "UNDECLARED_NAMED_CHARACTER" in codes
    assert "NAMED_CHARACTER_MISSING_IN_SCENE" in codes
    undeclared_msg = next(f["msg"] for f in findings if f["code"] == "UNDECLARED_NAMED_CHARACTER")
    assert "Nguyễn Phong" in undeclared_msg and "Duy Khiêm" in undeclared_msg
    missing_scene_msg = next(f["msg"] for f in findings if f["code"] == "NAMED_CHARACTER_MISSING_IN_SCENE")
    assert "CHAR_VIET_DUONG" in missing_scene_msg


def test_director_timeline_and_keyframe_staging_choreography(cfg):
    proj = {
        "language": "vi",
        "style_line": "Live-action creature feature, IMAX 70mm Panavision Anamorphic lens",
        "characters": [
            {"id": "CHAR_TREX", "name": "Rex", "short_name": "Rex",
             "identity_line": "a massive adult Tyrannosaurus rex with dark charcoal scales",
             "reference_images": ["assets/characters/rex.png"]},
            {"id": "CHAR_SPINO", "name": "Spino", "short_name": "Spino",
             "identity_line": "a colossal adult Spinosaurus with a crimson-streaked dorsal sail",
             "reference_images": ["assets/characters/spino.png"]},
        ],
        "environments": [{"id": "ENV_SWAMP", "name": "Storm Swamp", "identity_line": "a flooded cypress swamp at night"}],
    }
    shot = {
        "shot_id": "shot_03",
        "generation_mode": "first_last",
        "first_frame_path": "f1.jpg",
        "last_frame_path": "f2.jpg",
        "camera": "Wide tracking shot, 35mm Anamorphic lens",
        "subjects": ["CHAR_TREX", "CHAR_SPINO"],
        "environment": "ENV_SWAMP",
        "lighting": "lightning backlight",
        "start_action": "Rex and Spino charge toward each other",
        "action": "Rex and Spino collide chest-to-chest",
        "end_action": "Rex and Spino grapple in churning water",
        "start_staging": {
            "camera_blocking": "1.1m low-angle 35mm Anamorphic lens at f/2.8",
            "subject_poses": {
                "CHAR_TREX": "Left frame charging right with lowered skull",
                "CHAR_SPINO": "Right frame charging left with raised claws",
            },
            "vfx_environment": "Dual V-shaped bow waves of black swamp water",
        },
        "end_staging": {
            "camera_blocking": "1.1m low-angle 35mm framing misted with spray",
            "subject_poses": {
                "CHAR_TREX": "Center-left wedged against Spino's flank",
                "CHAR_SPINO": "Center-right shoved half a step backward",
            },
            "vfx_environment": "4-meter radial shockwave curtain collapsing into the swamp",
        },
        "timeline_phases": [
            {
                "time": "0.0s-2.4s",
                "phase_name": "Swamp Charge",
                "camera": "35mm dolly tracks inward at water level",
                "subjects": {
                    "CHAR_TREX": "Rex sprints from the left with booming strides",
                    "CHAR_SPINO": "Spino charges from the right raising its claws",
                },
                "vfx": "Dual V-shaped bow waves surge toward center",
                "sfx": "rapid splashes",
            },
            {
                "time": "2.4s-5.2s",
                "phase_name": "Chest Collision",
                "camera": "Camera absorbs a heavy handheld impact jolt",
                "subjects": {
                    "CHAR_TREX": "Rex slams its chest into Spino's torso",
                    "CHAR_SPINO": "Spino buckles backward raking its claws across Rex",
                },
                "vfx": "3D radial shockwave ring of water explodes 4 meters high",
                "sfx": "bone-crushing collision",
            },
            {
                "time": "5.2s-8.0s",
                "phase_name": "Grappling Settle",
                "camera": "Camera holds tight on the grappling pair",
                "subjects": {
                    "CHAR_TREX": "Rex digs its hind talons into the mud",
                    "CHAR_SPINO": "Spino braces its hind legs snapping its jaws",
                },
                "vfx": "Airborne water curtain crashes back into the swamp",
                "sfx": "cascading water",
            },
        ],
        "audio": {"mode": "sfx_only", "sfx": "collision impact"},
    }
    ff_p = prompts.build_first_frame_prompt(proj, shot)
    lf_p = prompts.build_last_frame_prompt(proj, shot)
    veo_p = prompts.build_prompt(proj, shot)
    shot["veo_prompt"] = veo_p

    assert "Camera & Optics: 1.1m low-angle 35mm Anamorphic lens" in ff_p
    assert "Character Staging & Anatomy: Rex: Left frame charging right" in ff_p
    assert "Environment & 3D VFX State: Dual V-shaped bow waves" in ff_p
    assert "Surgical action-impact edit" in lf_p
    assert "Character Staging & Anatomy: Rex: Center-left wedged" in lf_p
    assert "Choreography timeline: [0.0s-2.4s Swamp Charge]" in veo_p
    assert "[2.4s-5.2s Chest Collision]" in veo_p
    assert "[5.2s-8.0s Grappling Settle]" in veo_p

    codes = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "TOO_MANY_PHASES" not in codes
    assert "PROMPT_TOO_LONG" not in codes
    assert "PASSIVE_SUBJECT_IN_PHASE" not in codes

    # Nếu 1 nhân vật bị bỏ quên trong 1 pha -> cảnh báo PASSIVE_SUBJECT_IN_PHASE
    shot["timeline_phases"][1]["subjects"].pop("CHAR_SPINO")
    codes_missing = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "PASSIVE_SUBJECT_IN_PHASE" in codes_missing



def test_ilm_3d_spatial_modes_contact_physics_and_fantasy_trap_linter(cfg):
    proj = {
        "language": "en",
        "style_line": "Photorealistic ILM Jurassic World Dominion live-action creature cinematography",
        "characters": [
            {"id": "CHAR_TREX", "name": "Rex", "short_name": "Rex",
             "identity_line": "a massive 9-ton adult Tyrannosaurus rex with wet dark amber reptile eyes",
             "reference_images": ["assets/characters/rex.png"]},
            {"id": "CHAR_SPINO", "name": "Spino", "short_name": "Spino",
             "identity_line": "a colossal 11-ton adult Spinosaurus with a weathered dark dorsal sail",
             "reference_images": ["assets/characters/spino.png"]},
        ],
        "environments": [{"id": "ENV_SWAMP", "name": "Sanctuary", "identity_line": "a flooded cypress forest at night"}],
    }
    shot = {
        "shot_id": "shot_06b",
        "generation_mode": "first_last",
        "spatial_mode": "jaw_clamp",
        "first_frame_path": "f1.jpg",
        "last_frame_path": "f2.jpg",
        "camera": "1.6m close-up 3/4 combat shot, 50mm Panavision Anamorphic lens",
        "subjects": ["CHAR_TREX", "CHAR_SPINO"],
        "environment": "ENV_SWAMP",
        "lighting": "warm 2700K amber ground firelight and cold 6500K steel-teal rain rim light",
        "start_action": "Rex's open jaws press against Spino's throat",
        "action": "Rex clamps its jaws deep into Spino's neck flesh",
        "end_action": "Rex holds Spino's neck pinned in a jaw clamp",
        "start_staging": {
            "camera_blocking": "1.6m close-up 3/4 combat shot, 50mm lens at f/2.0",
            "foreground_occlusion": "Blurred wet cypress roots in lower-left foreground",
            "subject_poses": {
                "CHAR_TREX": "Center-left driving upward",
                "CHAR_SPINO": "Center-right caught in Rex's jaws",
            },
            "contact_physics": "Full jaw-clamp tissue deformation on wet neck hide",
            "vfx_environment": "Heavy steel-teal rain sheets",
        },
        "end_staging": {
            "camera_blocking": "1.6m close-up tilted downward",
            "subject_poses": {
                "CHAR_TREX": "Center-left clamping Spino's throat",
                "CHAR_SPINO": "Center-right wrenched downward",
            },
            "contact_physics": "35,000-Newton bite compressing neck skin folds",
            "vfx_environment": "Saliva and rainwater spray",
        },
        "audio": {"mode": "sfx_only", "sfx": "visceral bite crunch"},
    }
    ff_p = prompts.build_first_frame_prompt(proj, shot)
    veo_p = prompts.build_prompt(proj, shot)
    shot["veo_prompt"] = veo_p

    assert "Driving forward from center-left with jaws clamped deep into its rival's neck, Rex is" in veo_p
    assert "Pinned in center-right with neck hide compressed under the bite, Spino is" in veo_p
    assert "foreground scale anchor: Blurred wet cypress roots" in ff_p
    assert "Physical Contact & Mass Coupling: Full jaw-clamp tissue deformation" in ff_p

    codes_clean = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "FANTASY_LIGHTING_TRAP" not in codes_clean

    # Inject fantasy traps -> linter must flag FANTASY_LIGHTING_TRAP
    shot["veo_prompt"] += " Rex has glowing amber eyes under blue-violet lightning."
    codes_trap = {f["code"] for f in prompts.lint_shot(proj, shot, cfg)}
    assert "FANTASY_LIGHTING_TRAP" in codes_trap



def test_storyboard_grid_prompt_and_auto_slicer(tmp_path, cfg):
    import numpy as np
    from scripts.studio import media, storyboard as sb

    cv2 = media.cv2_module()
    proj_dir = tmp_path / "demo_grid"
    proj_dir.mkdir(parents=True, exist_ok=True)
    proj = {
        "project_name": "Demo Grid",
        "project_slug": "demo-grid",
        "aspect_ratio": "16:9",
        "style_line": "Photorealistic ILM live-action creature cinematography",
        "characters": [
            {"id": "CHAR_A", "name": "Rex", "short_name": "Rex", "identity_line": "9-ton adult Tyrannosaurus rex"},
            {"id": "CHAR_B", "name": "Spino", "short_name": "Spino", "identity_line": "11-ton adult Spinosaurus"},
        ],
        "environments": [{"id": "ENV_1", "name": "Swamp", "identity_line": "flooded cypress swamp at night"}],
        "shots": [
            {"shot_id": f"shot_{i:02d}", "order": i, "generation_mode": "first_last",
             "camera": "1.5m low-angle 35mm lens", "start_action": f"Start action {i}", "end_action": f"End action {i}"}
            for i in range(1, 5)
        ],
    }
    panels = sb.default_grid_panels(proj, rows=2, cols=2)
    assert len(panels) == 4
    gp = prompts.build_storyboard_grid_prompt(proj, rows=2, cols=2, panels=panels)
    assert "Seamless edge-to-edge 2x2 cinematic storyboard contact sheet" in gp
    assert "Panel 1 (Row 1 Left):" in gp
    assert "Panel 4 (Row 2 Right):" in gp

    # Create a synthetic 2x2 grid image (1920x1080) with black divider lines at x=960, y=540
    canvas = np.full((1080, 1920, 3), 90, dtype=np.uint8)
    canvas[:, 958:962] = 0
    canvas[538:542, :] = 0
    grid_file = proj_dir / "grid_2x2.jpg"
    cv2.imwrite(str(grid_file), canvas)

    res = sb.slice_storyboard_grid(grid_file, proj_dir, proj, rows=2, cols=2, apply_to_shots=True)
    assert len(res["panels"]) == 4
    assert (proj_dir / res["annotated_sheet"]).exists()
    p1 = cv2.imread(str(proj_dir / res["panels"][0]["path"]))
    assert p1.shape == (1080, 1920, 3)
