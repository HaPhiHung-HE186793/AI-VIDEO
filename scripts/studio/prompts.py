"""Dựng prompt Veo 3.1 có cấu trúc, lint prompt, dọn boilerplate cũ và định tuyến model.

Nguyên tắc (xem references/prompt_templates.md):
- Prompt khẳng định, 400–750 ký tự: [máy quay] [chủ thể + hành động] [bối cảnh + ánh sáng] [phong cách] [âm thanh].
- Mô tả nhân vật là `identity_line` dán NGUYÊN VĂN ở mọi shot; danh tính thật được khóa bằng ảnh tham chiếu.
- Thứ cần loại bỏ để ở `negative_prompt`, không nhồi câu phủ định vào prompt.
"""

import re

from . import manifest as mf

LANGUAGE_RATES = {
    "vi": {"name": "Tiếng Việt", "unit": "âm tiết", "rec_max_per_8s": 19, "hard_max_per_8s": 22},
    "en": {"name": "English", "unit": "words", "rec_max_per_8s": 18, "hard_max_per_8s": 22},
    "ja": {"name": "日本語", "unit": "mora", "rec_max_per_8s": 35, "hard_max_per_8s": 42},
    "ko": {"name": "한국어", "unit": "âm tiết", "rec_max_per_8s": 26, "hard_max_per_8s": 32},
}

LANGUAGE_NAMES_EN = {"vi": "Vietnamese", "en": "English", "ja": "Japanese", "ko": "Korean"}

GENERATION_MODES = ("text", "ingredients", "first_frame", "first_last", "extend")
AUDIO_MODES = ("sfx_only", "voiceover_external", "veo_dialogue", "veo_narration")

# Câu boilerplate do engine cũ (v8–v10) tự chèn vào prompt. Chúng không có tác dụng với model
# hoặc gây phản tác dụng (câu phủ định gợi ra đúng thứ cần tránh).
_SENTENCE_END = r".*?\.(?=\s+[A-Z]|\s*$)"  # tới dấu chấm kết câu (bỏ qua "0.0s", "v10.0")
LEGACY_BOILERPLATE = [
    r"\s*Continuous unbroken 3-phase anatomical motion" + _SENTENCE_END,
    r"\s*Consistent 360-degree character model geometry" + _SENTENCE_END,
    r"\s*Strict v\d+(?:\.\d+)? BBC Biomechanical Contact Physics:" + _SENTENCE_END,
    r"\s*Strict Entity Conservation:" + _SENTENCE_END,
    r"\s*True forward spatial progression with strong foreground-to-background parallax" + _SENTENCE_END,
    r"\s*Strict anatomical prop scale relative to the subject's head and limbs" + _SENTENCE_END,
]

JUNK_TOKENS = re.compile(r"\b(8k|4k|AAA|masterpiece|best quality|ultra[- ]?realistic|hyper[- ]?realistic|v\d+\.\d+|strict)\b", re.I)
NEGATION = re.compile(r"\b(never|zero|without|don't|do not|avoid)\b|\bno\s+(?!subtitles\b|on-screen\b)\w+", re.I)
TIMECODE = re.compile(r"\(\s*\d+(?:\.\d+)?\s*s?\s*[-–]\s*\d+(?:\.\d+)?\s*s\s*\)")

INTERACTION_WORDS = re.compile(
    r"\b(bite|bites|biting|clamp|grab|grabs|grip|gripping|hold|holding|pick(?:s)? up|drop|drops|throw|throws|catch|"
    r"fight|fighting|hug|hugs|punch|kick|pour|pours|splash|splashing|dance|dancing|typing|eat|eating|drink|drinking|"
    r"collide|crash|lift|lifts|push|pushes|pull|pulls|shake|shakes)\b",
    re.I,
)
DETAIL_WORDS = re.compile(r"\b(extreme close-up|macro|hands?|fingers?|teeth|jaws|eyes)\b", re.I)


# Giọng dựng sẵn — cùng bộ tên trên Google Flow (mục "Giọng nói") và Gemini TTS.
# Danh sách có thể đổi theo thời gian; tên lạ chỉ bị cảnh báo mức info.
KNOWN_VOICES = {
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam", "Aoede", "Autonoe", "Callirrhoe", "Charon",
    "Despina", "Enceladus", "Erinome", "Fenrir", "Gacrux", "Iapetus", "Kore", "Laomedeia", "Leda", "Orus",
    "Puck", "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager", "Schedar", "Sulafat", "Umbriel",
    "Vindemiatrix", "Zephyr", "Zubenelgenubi",
}


def narrator_voice(project: dict) -> str:
    return project.get("narrator_voice") or project.get("voiceover_voice") or ""


def shot_voice(project: dict, shot: dict) -> str:
    """Giọng cố định của lời nói trong shot: audio.voice > giọng nhân vật đang nói > giọng người dẫn."""
    audio = mf.shot_audio(shot)
    if audio.get("voice"):
        return audio["voice"]
    if audio["mode"] == "veo_dialogue":
        return mf.characters_by_id(project).get(audio.get("speaker"), {}).get("voice", "")
    if audio["mode"] in ("veo_narration", "voiceover_external"):
        return narrator_voice(project)
    return ""


def normalize_lang(lang: str) -> str:
    s = (lang or "").strip().lower()
    if s in LANGUAGE_RATES:
        return s
    table = [("vi", ["viet", "tiếng việt"]), ("en", ["english", "tiếng anh"]), ("ja", ["japan", "nhật"]), ("ko", ["korea", "hàn"])]
    for code, keys in table:
        if any(k in s for k in keys):
            return code
    return "vi"


def count_speech_units(text: str, lang: str) -> int:
    text = re.sub(r"[^\w\s']", " ", text or "")
    if lang in ("ja",):
        return len(re.sub(r"\s", "", text))
    return len(text.split())


def clean_legacy_prompt(text: str) -> tuple:
    """Gỡ boilerplate engine cũ. Trả về (prompt sạch, số đoạn đã gỡ)."""
    out, removed = text or "", 0
    for pat in LEGACY_BOILERPLATE:
        out, n = re.subn(pat, "", out, flags=re.I)
        removed += n
    # Gom các hậu tố "no subtitles" trùng lặp về đúng 1 lần ở cuối.
    out, n_sub = re.subn(r"[,.]?\s*no subtitles,?\s*no on-screen text\.?", "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip().rstrip(",. ")
    if n_sub:
        out += ". No subtitles, no on-screen text."
    return out, removed


def _sentence(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else text + "."


def display_name(character: dict, fallback: str = "") -> str:
    """Tên ngắn dùng trong prompt (`short_name`), để hành động viết "Rex walks..." khớp với chủ thể."""
    return character.get("short_name") or character.get("name") or fallback


def compact_identity(character: dict) -> str:
    """Trích xuất mô tả ngoại hình cô đọng (tóc, kính, trang phục) để nhúng 4..20+ nhân vật vào cùng 1 cảnh mà không tràn prompt."""
    if character.get("compact_identity"):
        return character["compact_identity"].strip().rstrip(".")
    raw = (character.get("identity_line") or "").strip().rstrip(".")
    if not raw:
        return ""
    cleaned = re.sub(
        r"^(?:a|an)?\s*(?:(?:\d+[- ]year[- ]old|young|lively|gentle|cheerful|handsome|pretty|"
        r"tall|chubby|slim|nerdy|playful|calm|energetic|cool|shy|funny|sporty)\s+)*"
        r"(?:vietnamese\s+|asian\s+)?(?:guy|man|woman|girl|boy|person|student|friend|cultivator|brain cell)\s+"
        r"(?:with|in|wearing)\s+",
        "",
        raw,
        flags=re.I,
    )
    cleaned = re.sub(r",?\s+and\s+(?:an?\s+)?", ", ", cleaned, flags=re.I)
    cleaned = re.sub(r"\ban?\s+", "", cleaned, flags=re.I)
    return cleaned.strip(" ,.") or raw


def is_structured(shot: dict) -> bool:
    return bool((shot.get("action") or shot.get("timeline_phases")) and (shot.get("camera") or shot.get("camera_shot")))


_ABSTRACT_CLAUSES = [
    re.compile(r",?\s*\bas if\s+(?:starting|telling|recounting|trying|about|he|she|they)\b[^.,;]*", re.I),
    re.compile(r",?\s*\bwhile recounting\s+(?:his|her|their)\s+[^.,;]*", re.I),
    re.compile(r",?\s*\bas (?:he|she|they) recounts?\s+[^.,;]*", re.I),
    re.compile(r",?\s*\bto tease\s+(?:him|her|them)\s+about\s+[^.,;]*", re.I),
    re.compile(r",?\s*\bin order to\s+(?:tease|mock|convince|prove)\b[^.,;]*", re.I),
]


def _clean_kinematic_action(text: str) -> str:
    """Lược bỏ mệnh đề tâm lý/kể chuyện trừu tượng, chỉ giữ lại động từ vật lý (kinematic action) cho AI."""
    out = (text or "").strip()
    if not out:
        return ""
    for pat in _ABSTRACT_CLAUSES:
        out = pat.sub("", out)
    return re.sub(r"\s{2,}", " ", out).strip(" ,.")


def _build_director_timeline(shot: dict, chars: dict = None) -> str:
    """Biên dịch bảng phân cảnh theo từng mốc giây (`timeline_phases`) chuẩn Đạo diễn Hình ảnh & VFX.

    Mỗi pha gồm:
    - `time`: mốc giây (vd. '0.0s-2.2s')
    - `phase_name`: tên nhịp hành động (vd. 'Wind-Up & Charge')
    - `camera`: chuyển động ống kính / tiêu cự trong mốc giây đó
    - `subjects`: dict {CHAR_ID: hành động cơ sinh học cụ thể của từng nhân vật} hoặc chuỗi mô tả
    - `vfx`: tương tác vật lý / hiệu ứng 3D / môi trường trong mốc giây đó
    - `sfx`: điểm nổ âm thanh đồng bộ (tùy chọn)
    """
    phases = shot.get("timeline_phases")
    if not isinstance(phases, list) or not phases:
        return ""
    chars = chars or {}
    blocks = []
    for idx, ph in enumerate(phases, 1):
        if not isinstance(ph, dict):
            continue
        t_window = (ph.get("time") or f"Phase {idx}").strip(" []")
        p_label = (ph.get("phase_name") or ph.get("label") or "").strip()
        header = f"[{t_window} {p_label}]" if p_label else f"[{t_window}]"
        segs = [header]
        cam = _clean_kinematic_action(ph.get("camera") or "")
        if cam:
            segs.append(_sentence(f"Camera: {cam}"))
        subj = ph.get("subjects")
        if isinstance(subj, dict) and subj:
            s_clauses = []
            for cid, s_act in subj.items():
                clean_s = _clean_kinematic_action(str(s_act or ""))
                if not clean_s:
                    continue
                c_name = display_name(chars.get(cid, {}), cid)
                if clean_s.lower().startswith(c_name.lower()):
                    s_clauses.append(clean_s)
                else:
                    s_clauses.append(f"{c_name}: {clean_s}")
            if s_clauses:
                segs.append(_sentence(f"Action: {'; '.join(s_clauses)}"))
        elif isinstance(subj, str) and subj.strip():
            segs.append(_sentence(f"Action: {_clean_kinematic_action(subj)}"))
        elif ph.get("action"):
            segs.append(_sentence(f"Action: {_clean_kinematic_action(ph['action'])}"))
        vfx = _clean_kinematic_action(ph.get("vfx") or ph.get("environment") or "")
        if vfx:
            segs.append(_sentence(f"VFX/Env: {vfx}"))
        sfx = (ph.get("sfx") or "").strip(" .")
        if sfx:
            segs.append(_sentence(f"SFX: {sfx}"))
        blocks.append(" ".join(segs))
    if not blocks:
        return ""
    return "Choreography timeline: " + " ".join(blocks)


def _build_keyframe_staging(shot: dict, chars: dict, slot: str) -> str:
    """Biên dịch chỉ dẫn dàn dựng chi tiết cho từng ảnh Keyframe (`start_staging` / `end_staging`)."""
    key = "start_staging" if slot == "start" else "end_staging"
    stg = shot.get(key)
    if not isinstance(stg, dict) or not stg:
        return ""
    chars = chars or {}
    parts = []
    cam_block = (stg.get("camera_blocking") or "").strip(" .")
    fg_occ = (stg.get("foreground_occlusion") or stg.get("dirty_frame") or "").strip(" .")
    if cam_block and fg_occ:
        parts.append(_sentence(f"Camera & Optics: {cam_block}; foreground scale anchor: {fg_occ}"))
    elif cam_block:
        parts.append(_sentence(f"Camera & Optics: {cam_block}"))
    elif fg_occ:
        parts.append(_sentence(f"Foreground Scale Anchor: {fg_occ}"))
    subj_poses = stg.get("subject_poses")
    if isinstance(subj_poses, dict) and subj_poses:
        p_list = []
        for cid, pose_txt in subj_poses.items():
            clean_p = (str(pose_txt or "")).strip(" .")
            if not clean_p:
                continue
            c_name = display_name(chars.get(cid, {}), cid)
            if clean_p.lower().startswith(c_name.lower()):
                p_list.append(clean_p)
            else:
                p_list.append(f"{c_name}: {clean_p}")
        if p_list:
            parts.append(_sentence(f"Character Staging & Anatomy: {' | '.join(p_list)}"))
    contact_phys = (stg.get("contact_physics") or "").strip(" .")
    if contact_phys:
        parts.append(_sentence(f"Physical Contact & Mass Coupling: {contact_phys}"))
    vfx_env = (stg.get("vfx_environment") or stg.get("vfx") or "").strip(" .")
    if vfx_env:
        parts.append(_sentence(f"Environment & 3D VFX State: {vfx_env}"))
    return " ".join(parts)


def _build_motion_arc(shot: dict, chars: dict = None) -> str:
    """Ghép câu quỹ đạo chuyển động: ưu tiên `timeline_phases` chi tiết theo từng giây, dự phòng 3 pha (Start -> Bridge -> End)."""
    if shot.get("timeline_phases"):
        tl_str = _build_director_timeline(shot, chars)
        if tl_str:
            return tl_str
    start_act = _clean_kinematic_action(shot.get("start_action") or "")
    act = _clean_kinematic_action(shot.get("action") or "")
    end_act = _clean_kinematic_action(shot.get("end_action") or "")
    if re.search(r"\bthen smoothly transition(?:s|ing)\b", act, flags=re.I):
        return _sentence(act)
    if shot.get("generation_mode") == "first_last" and end_act:
        if start_act and start_act.lower() != act.lower() and end_act.lower() != act.lower() and start_act.lower() not in act.lower():
            return _sentence(f"Starting from {start_act}, {act}, then smoothly settling into the final state where {end_act}")
        if end_act.lower() != act.lower() and end_act.lower() not in act.lower():
            return _sentence(f"{act}, then smoothly transitioning so {end_act}")
    return _sentence(act or start_act or end_act)


def _format_cast_lines(shot: dict, chars: dict) -> list:
    """Định dạng danh sách nhân vật có tên (từ 1 đến 20+ người) đồng bộ tuyệt đối giữa Keyframe START, END và Veo Prompt.

    - Khóa vị trí Trái/Giữa/Phải (`On the left / In the center / On the right`) cho các nhân vật tiêu điểm (`subjects`)
      ở CẢ 3 TẦNG để Nano Banana không vẽ ngược bên với Veo.
    - Khi cảnh có từ 4..20+ nhân vật (qua `subjects` hoặc `ensemble_cast` / `table_group`), tự động liệt kê đầy đủ
      100% nhân vật được gọi tên kèm tạo hình rút gọn (`compact_identity`) theo sơ đồ chỗ ngồi quanh bàn/cảnh.
    """
    focal_ids = [cid for cid in (shot.get("subjects") or []) if cid in chars]
    all_cast = [cid for cid in mf.shot_all_cast_ids(shot) if cid in chars]
    lines = []

    # Tầng 1: Nhân vật tiêu điểm (1..3 người đang thực hiện hành động chính) kèm full identity_line
    primary_ids = focal_ids[:3] if len(focal_ids) <= 3 else focal_ids[:2]
    cam_lower = (shot.get("camera") or shot.get("camera_shot") or "").lower()
    sp_mode = (shot.get("spatial_mode") or "").strip().lower()
    if not sp_mode and len(primary_ids) == 2:
        if "over-the-shoulder" in cam_lower or "ots" in cam_lower:
            sp_mode = "ots_left"
        elif "foreground" in cam_lower and "background" in cam_lower:
            sp_mode = "depth_clash"
    if len(primary_ids) == 3:
        pos_tags = ["On the left,", "In the center,", "On the right,"]
    elif len(primary_ids) == 2:
        if sp_mode == "ots_left":
            pos_tags = ["In the close foreground on the left,", "Looming in the midground on the right,"]
        elif sp_mode == "ots_right":
            pos_tags = ["Looming in the midground on the left,", "In the close foreground on the right,"]
        elif sp_mode == "depth_clash":
            pos_tags = ["Charging from the foreground left,", "Bracing in the midground right,"]
        elif sp_mode == "clinched_grapple":
            pos_tags = ["Physically clinched in center-left in an overlapping 3D grapple,", "Locked chest-to-chest in center-right with overlapping body mass,"]
        elif sp_mode == "jaw_clamp":
            pos_tags = ["Driving forward from center-left with jaws clamped deep into its rival's neck,", "Pinned in center-right with neck hide compressed under the bite,"]
        elif sp_mode == "low_angle_3d":
            pos_tags = ["Towering in the left foreground at a 3/4 low-angle perspective,", "Lunging from the right midground across the z-axis depth,"]
        else:
            pos_tags = ["On the left,", "On the right,"]
    else:
        pos_tags = []
    use_pos = bool(shot.get("spatial_lock", True)) and len(primary_ids) in (2, 3)
    for idx, cid in enumerate(primary_ids):
        c = chars[cid]
        if c.get("identity_line"):
            prefix = f"{pos_tags[idx]} " if use_pos and idx < len(pos_tags) else ""
            lines.append(_sentence(f"{prefix}{display_name(c, cid)} is {c['identity_line'].rstrip('.')}"))

    # Tầng 2: Nếu cảnh có >= 4 nhân vật hoặc có khai báo `ensemble_cast` / `table_group` (4..20+ người),
    # xuất sơ đồ chỗ ngồi đầy đủ 100% các nhân vật có tên trong cảnh để không sót bất kỳ ai.
    has_ensemble = len(all_cast) >= 4 or len(all_cast) > len(primary_ids)
    if has_ensemble:
        context_str = f"{shot.get('action', '')} {shot.get('setting', '')} {shot.get('environment', '')}"
        default_layout = (
            "seated together around the main table from left to right"
            if re.search(r"\b(table|cafe|restaurant|banquet|bar|dinner|lunch|party|rooftop)\b", context_str, re.I)
            else "gathered in the scene from left to right"
        )
        layout = (shot.get("seating_layout") or default_layout).strip().rstrip(":")
        primary_set = set(primary_ids)
        roster = [
            display_name(chars[cid], cid) if cid in primary_set else f"{display_name(chars[cid], cid)} ({compact_identity(chars[cid])})"
            for cid in all_cast
        ]
        lines.append(_sentence(f"All {len(roster)} named characters {layout}: {', '.join(roster)}"))

    return lines


def _crowd_atmosphere_line(project: dict, shot: dict) -> str:
    """Sinh câu mô tả tầng quần chúng không tên & các bàn xung quanh (nếu cảnh ở quán xá/không gian đông vui)."""
    raw_shot_crowd = shot.get("background_crowd") if "background_crowd" in shot else shot.get("atmosphere")
    if raw_shot_crowd is False or str(raw_shot_crowd or "").strip().lower() in ("none", "false", "empty"):
        return ""
    if isinstance(raw_shot_crowd, str) and raw_shot_crowd.strip():
        return _sentence(raw_shot_crowd.strip())

    envs = mf.environments_by_id(project)
    env_obj = envs.get(shot.get("environment") or "", {})
    env_crowd = env_obj.get("background_crowd") or env_obj.get("atmosphere") or ""
    if isinstance(env_crowd, str) and env_crowd.strip():
        return _sentence(env_crowd.strip())

    # Tự động kích hoạt không khí quán đông vui nếu cảnh nhóm (>=4 nhân vật) diễn ra tại quán cafe/nhà hàng/bàn tiệc
    all_cast = mf.shot_all_cast_ids(shot)
    env_text = f"{env_obj.get('name', '')} {env_obj.get('identity_line', '')} {shot.get('setting', '')}"
    if len(all_cast) >= 4 and re.search(r"\b(cafe|rooftop|restaurant|bar|pub|diner|banquet|party)\b", env_text, re.I):
        return _sentence(
            "In the background, several neighboring tables are occupied by lively unnamed cafe patrons chatting "
            "and clinking drinks, creating a bustling, vibrant social atmosphere"
        )
    return ""


def _cross_attribute_lock(subjects: list, chars: dict) -> str:
    """Sinh câu khóa phân tách thuộc tính (khẳng định 100%, không dùng từ phủ định) khi cảnh có >=2 nhân vật.

    Ngăn lỗi Veo 3.1 ở chế độ `first_last` bị lây thuộc tính (kính mắt, tóc dài/ngắn) giữa các nhân vật ngồi cạnh nhau.
    """
    if len(subjects) < 2:
        return ""
    with_glasses, bare_eyes = [], []
    long_hair, short_hair = [], []
    short_hair_pat = re.compile(
        r"\b(short|buzz|undercut|crew|fade|middle[- ]part|side[- ]part|parted|messy|cropped|spiky|slicked|curly|wavy)\b"
        r"[^.,;]*\b(hair|haircut|cut)\b|\bbuzz\s+cut\b",
        re.I,
    )
    for cid in subjects:
        c = chars.get(cid, {})
        id_line = (c.get("identity_line") or "").lower()
        if not id_line:
            continue
        name = display_name(c, cid)
        if re.search(r"\b(glasses|spectacles|eyeglasses)\b", id_line):
            with_glasses.append(name)
        else:
            bare_eyes.append(name)
        if re.search(r"\blong\b[^.,;]*\bhair\b", id_line):
            long_hair.append(name)
        elif short_hair_pat.search(id_line):
            short_hair.append(name)
    clauses = []
    if with_glasses and bare_eyes:
        g_verb = "wears" if len(with_glasses) == 1 else "wear"
        if len(bare_eyes) <= 3:
            b_verb = "keeps" if len(bare_eyes) == 1 else "keep"
            clauses.append(f"Only {' and '.join(with_glasses)} {g_verb} glasses while {' and '.join(bare_eyes)} {b_verb} bare eyes")
        else:
            clauses.append(f"Only {' and '.join(with_glasses)} {g_verb} glasses while all other characters keep bare eyes")
    if long_hair and short_hair:
        l_verb = "has" if len(long_hair) == 1 else "have"
        if len(short_hair) <= 3:
            s_verb = "keeps" if len(short_hair) == 1 else "keep"
            clauses.append(f"only {' and '.join(long_hair)} {l_verb} long hair while {' and '.join(short_hair)} {s_verb} short hair")
        else:
            clauses.append(f"only {' and '.join(long_hair)} {l_verb} long hair while all other characters keep short hair")
    if not clauses:
        return ""
    joined = "; ".join(clauses)
    return _sentence(joined[0].upper() + joined[1:])


def _align_first_last_camera(camera_text: str, shot: dict) -> str:
    """Đồng bộ mô tả máy quay trong veo_prompt với cặp Keyframe START/END để tránh lỗi chồng mờ (dissolve) cuối clip.

    Nếu shot ở chế độ `first_last` mà không bật `dynamic_camera` (tức START và END có cùng cỡ cảnh Anchor-Locked),
    loại bỏ lệnh push-in/pull-back/zoom gây mâu thuẫn tiêu cự với frame END.
    """
    cam = (camera_text or "").strip()
    if shot.get("generation_mode") != "first_last" or shot.get("dynamic_camera"):
        return cam
    if re.search(r"\b(push[- ]in|pull[- ]back|zoom[- ]?(?:in|out)?)\b", cam, flags=re.I):
        cleaned = re.sub(
            r",?\s*\b(slow|very slow|gentle|subtle|smooth|dramatic)?\s*(push[- ]in|pull[- ]back|zoom[- ]?(?:in|out)?)[^,.]*",
            "",
            cam,
            flags=re.I,
        ).strip(" ,.")
        return f"{cleaned}, steady locked-off framing, single continuous take" if cleaned else "Steady locked-off framing, single continuous take"
    return cam


def _content_words(text: str) -> set:
    stop = {"a", "an", "the", "in", "on", "at", "of", "with", "and", "or", "to", "from", "by", "for", "as", "into", "under", "over"}
    return {w for w in re.findall(r"[a-z0-9]{2,}", (text or "").lower()) if w not in stop}


def _dedupe_visual_clauses(setting: str, lighting: str, style_line: str, reference_body: str = "",
                           compact_for_keyframe_video: bool = False) -> str:
    """Khử trùng lặp mệnh đề ánh sáng/môi trường giữa setting, lighting, style_line và timeline_phases.

    Theo chuẩn Visual-First Compact Motion Prompting của các studio AI hàng đầu (Kling / Seedance / Veo 3.1):
    khi đã khóa Keyframe START/END và có bảng phân cảnh động học, việc lặp lại cùng một mô tả ánh sáng
    (vd. '2700K amber firelight vs 6500K steel-teal rain rim light') 2–3 lần trong cùng 1 prompt sẽ làm
    Text Attention lấn át Visual & Physics Attention.
    """
    style_words = _content_words(style_line)
    body_words = _content_words(reference_body) if compact_for_keyframe_video else set()

    setting_clean = (setting or "").strip(" ,.")
    if compact_for_keyframe_video and setting_clean and (style_words or body_words):
        s_clauses = [c.strip() for c in re.split(r",\s+", setting_clean) if c.strip()]
        kept_s = []
        ref_union = style_words | body_words
        for idx, cl in enumerate(s_clauses):
            cw = _content_words(cl)
            if idx == 0 or not cw or len(cw & ref_union) / len(cw) < 0.68:
                kept_s.append(cl)
        setting_clean = ", ".join(kept_s)

    setting_words = _content_words(setting_clean)
    ref_for_lighting = style_words | setting_words | body_words

    lighting_clean = (lighting or "").strip(" ,.")
    if lighting_clean and ref_for_lighting:
        l_clauses = [c.strip() for c in re.split(r"[;,]+\s*", lighting_clean) if c.strip()]
        kept_l = []
        for cl in l_clauses:
            cw = _content_words(cl)
            if not cw or len(cw & ref_for_lighting) / len(cw) < 0.68:
                kept_l.append(cl)
                ref_for_lighting |= cw
        lighting_clean = ", ".join(kept_l)

    return _sentence(", ".join(x for x in [setting_clean, lighting_clean] if x))


def build_prompt(project: dict, shot: dict) -> str:
    """Ghép prompt Veo 3.1 có cấu trúc: [Máy quay] + [Nhân vật & Sơ đồ chỗ ngồi 1..N] + [Quỹ đạo chuyển động 3 pha] + [Quần chúng nền & Ánh sáng] + [Âm thanh]."""
    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)
    lang = normalize_lang(project.get("language") or project.get("plan", {}).get("language_code", "vi"))

    raw_cam = shot.get("camera") or shot.get("camera_shot")
    parts = [_sentence(_align_first_last_camera(raw_cam, shot))]

    all_cast = mf.shot_all_cast_ids(shot)
    parts += _format_cast_lines(shot, chars)
    attr_lock = _cross_attribute_lock(all_cast, chars)
    if attr_lock:
        parts.append(attr_lock)

    motion_arc = _build_motion_arc(shot, chars)
    parts.append(motion_arc)

    crowd_line = _crowd_atmosphere_line(project, shot)
    if crowd_line:
        parts.append(crowd_line)

    setting = shot.get("setting")
    if not setting and shot.get("environment") in envs:
        setting = envs[shot["environment"]].get("identity_line") or envs[shot["environment"]].get("name")
    style_str = project.get("style_line") or project.get("visual_style") or ""
    is_kf_timeline = shot.get("generation_mode") in ("first_frame", "first_last") and bool(shot.get("timeline_phases"))
    parts.append(_dedupe_visual_clauses(setting, shot.get("lighting") or "", style_str,
                                        reference_body=motion_arc, compact_for_keyframe_video=is_kf_timeline))
    parts.append(_sentence(style_str))

    audio = mf.shot_audio(shot)
    sfx = audio.get("sfx", "")
    if audio["mode"] == "veo_dialogue" and audio.get("line"):
        speaker = display_name(chars.get(audio.get("speaker"), {}), audio.get("speaker") or "The character")
        delivery = f", {audio['delivery']}" if audio.get("delivery") else ""
        parts.append(f'{speaker} speaks to camera in {LANGUAGE_NAMES_EN.get(lang, lang)}{delivery}: "{audio["line"]}"')
        others = [display_name(chars.get(c, {}), c) for c in shot.get("subjects", []) if c != audio.get("speaker")]
        if others:
            verb = "listens" if len(others) == 1 else "listen"
            parts.append(_sentence(f"{' and '.join(others)} {verb} with mouth closed"))
    elif audio["mode"] == "veo_narration" and audio.get("line"):
        parts.append(f'A calm narrator voiceover says in {LANGUAGE_NAMES_EN.get(lang, lang)}: "{audio["line"]}"')
    if sfx:
        label = "Ambient sound only" if audio["mode"] in ("sfx_only", "voiceover_external") else "Sound"
        parts.append(_sentence(f"{label}: {sfx}"))
    elif audio["mode"] in ("sfx_only", "voiceover_external"):
        parts.append("Natural ambient sound only.")
    parts.append("No subtitles, no on-screen text.")
    return re.sub(r"\s{2,}", " ", " ".join(p for p in parts if p)).strip()


def build_first_frame_prompt(project: dict, shot: dict) -> str:
    """Dựng prompt ảnh Keyframe mở đầu (`first_frame_prompt`) đồng bộ vị trí Trái/Phải, đủ 1..N nhân vật và quần chúng nền."""
    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)
    props = mf.props_by_id(project)

    cam = re.sub(
        r"\b(slow|very slow|gentle|subtle|smooth)?\s*(push[- ]in|pull[- ]back|pan|tilt|track(?:ing)?|dolly|orbit|zoom)\b[^,.]*",
        "",
        shot.get("camera") or shot.get("camera_shot") or "",
        flags=re.I,
    ).strip(" ,.")
    pose = _clean_kinematic_action(shot.get("start_action") or shot.get("action") or "")
    cam_head = (cam or shot.get("camera") or shot.get("camera_shot") or "").rstrip(".")
    parts = [_sentence(f"{cam_head}: {pose}" if cam_head and pose else (cam_head or pose))]
    if shot.get("grid_panel_start_path") and shot.get("use_grid_layout_ref", True):
        parts.append(
            "Hero 1080p keyframe upgrade from the attached storyboard layout reference panel: preserve the panel's "
            "camera composition and color palette while rendering full high-frequency skin/scale textures and sharp anatomical detail from the character references."
        )

    all_cast = mf.shot_all_cast_ids(shot)
    parts += _format_cast_lines(shot, chars)
    attr_lock = _cross_attribute_lock(all_cast, chars)
    if attr_lock:
        parts.append(attr_lock)
    start_stg_line = _build_keyframe_staging(shot, chars, "start")
    if start_stg_line:
        parts.append(start_stg_line)

    for pid in shot.get("props", []):
        p = props.get(pid, {})
        if p.get("name"):
            parts.append(_sentence(f"Visible prop: {p['name']}"))

    crowd_line = _crowd_atmosphere_line(project, shot)
    if crowd_line:
        parts.append(crowd_line)

    setting = shot.get("setting")
    if not setting and shot.get("environment") in envs:
        setting = envs[shot["environment"]].get("identity_line") or envs[shot["environment"]].get("name")
    style_str = project.get("style_line") or project.get("visual_style") or ""
    parts.append(_dedupe_visual_clauses(setting, shot.get("lighting") or "", style_str,
                                        reference_body=start_stg_line, compact_for_keyframe_video=bool(start_stg_line)))
    parts.append(_sentence(style_str))
    parts.append("Single still keyframe, exact composition and lighting, no text, no subtitles.")
    return re.sub(r"\s{2,}", " ", " ".join(p for p in parts if p)).strip()


def build_last_frame_prompt(project: dict, shot: dict) -> str:
    """Dựng prompt ảnh Keyframe kết thúc (`last_frame_prompt`) theo cấu trúc Surgical Pose Edit khóa chặt góc máy, vị trí 1..N nhân vật và nền."""
    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)

    end_pose = _clean_kinematic_action(shot.get("end_action") or shot.get("action") or "")
    cam_raw = shot.get("camera") or shot.get("camera_shot") or ""
    impact_re = re.compile(
        r"\b(slam|slams|crash|crashes|shatter|shatters|collapse|collapses|knock|knocks|pin|pins|crush|crushes|"
        r"hurl|hurls|throw|throws|erupt|erupts|explode|explodes|topple|topples|drag|drags|bowl|bowls|"
        r"collide|collides|slash|slashes|clamp|clamps|wrench|wrenches|stomp|stomps|lunge|lunges|recoil|recoils)\b",
        re.I,
    )
    is_macro_ecu = bool(re.search(r"\b(extreme\s+close[- ]up|macro|ecu)\b", cam_raw, re.I))
    is_displacement = (not is_macro_ecu) and (
        bool(shot.get("physical_displacement"))
        or bool(impact_re.search(f"{shot.get('action', '')} {shot.get('end_action', '')}"))
    )
    if shot.get("dynamic_camera") and cam_raw:
        anchor_rule = (
            f"Surgical camera and pose edit from the attached start frame reference: complete the camera trajectory "
            f"({cam_raw.rstrip('.')}) while preserving the exact same background environment, lighting, and left-to-right character positions."
        )
        tail_rule = "Single still keyframe at the final camera position, no text, no subtitles."
    elif is_displacement:
        anchor_rule = (
            "Surgical action-impact edit from the attached start frame reference: update the subjects' full-body spatial displacement, "
            "knocked-down or lunging combat postures, and shattered environmental debris/water splashes to match the target final state, "
            "while locking the exact same camera lens, perspective, lighting scheme, and left-to-right character identities."
        )
        tail_rule = "Single still keyframe showing the full physical aftermath, identical camera framing to start frame, no text, no subtitles."
    else:
        anchor_rule = (
            "Surgical pose edit from the attached start frame reference: change ONLY the character pose and expression "
            "to match the target state while locking the exact same camera angle, lens, background environment, tabletop props, "
            "lighting, and left-to-right character positions."
        )
        tail_rule = "Single still keyframe, identical framing to start frame, no text, no subtitles."
    if shot.get("waypoint_subshot") and shot.get("waypoint_index", 1) < shot.get("waypoint_total", 1):
        lead = _sentence(f"Intermediate waypoint {shot['waypoint_index']} ({shot.get('shot_id', '')}): {end_pose}")
    else:
        lead = _sentence(f"Final state at the end of the shot: {end_pose}")
    parts = [
        lead,
        anchor_rule,
    ]
    all_cast = mf.shot_all_cast_ids(shot)
    parts += _format_cast_lines(shot, chars)
    attr_lock = _cross_attribute_lock(all_cast, chars)
    if attr_lock:
        parts.append(attr_lock)
    end_stg_line = _build_keyframe_staging(shot, chars, "end")
    if end_stg_line:
        parts.append(end_stg_line)

    crowd_line = _crowd_atmosphere_line(project, shot)
    if crowd_line:
        parts.append(crowd_line)

    setting = shot.get("setting")
    if not setting and shot.get("environment") in envs:
        setting = envs[shot["environment"]].get("identity_line") or envs[shot["environment"]].get("name")
    style_str = project.get("style_line") or project.get("visual_style") or ""
    parts.append(_dedupe_visual_clauses(setting, shot.get("lighting") or "", style_str,
                                        reference_body=end_stg_line, compact_for_keyframe_video=bool(end_stg_line)))
    parts.append(_sentence(style_str))
    parts.append(tail_rule)
    return re.sub(r"\s{2,}", " ", " ".join(p for p in parts if p)).strip()


def effective_negative_prompt(project: dict, shot: dict) -> str:
    items = [project.get("negative_prompt", ""), shot.get("negative_prompt", "")]
    if shot.get("generation_mode") == "first_last":
        items.append("cross-dissolve, double exposure, ghosting, mid-clip jump cut, attribute swapping")
    return ", ".join(x.strip(" ,") for x in items if x and x.strip(" ,"))


def _strip_accents(text: str) -> str:
    import unicodedata

    s = (text or "").replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")


_NON_PERSON_PROPER = {
    "viet nam", "ha noi", "sai gon", "da nang", "trung quoc", "han quoc", "nhat ban",
    "dai loan", "thai lan", "google flow", "youtube", "tiktok", "top top", "facebook", "instagram",
}

_VN_CAP_WORD = (
    r"[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
    r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+"
)
_MULTI_WORD_NAME_RE = re.compile(rf"\b({_VN_CAP_WORD}(?:\s+{_VN_CAP_WORD}){{1,3}})\b")
_HONORIFIC_NAME_RE = re.compile(
    rf"\b(?:cu|thằng|anh|chị|em|bạn|ông|bà|cô|chú|vợ chồng|nhà)\s+({_VN_CAP_WORD}(?:\s+{_VN_CAP_WORD}){{0,3}})\b"
)
_GROUP_KEYWORDS_RE = re.compile(
    r"\b(cả hội|nguyên bàn|cả bọn|cả lũ|mọi người|từng thằng|toàn mặt chúng mày|"
    r"all friends|whole group|everyone at the table|friends are chatting)\b",
    re.I,
)


def _char_name_keys(c: dict, cid: str = "") -> set:
    """Tập khóa tên không dấu (họ tên đầy đủ, tên ngắn, tên gọi cuối) của 1 nhân vật để đối chiếu với kịch bản."""
    keys = set()
    for raw in [c.get("name"), c.get("short_name"), *(c.get("aliases") or [])]:
        if not raw:
            continue
        norm = _strip_accents(str(raw)).strip().lower()
        if norm:
            keys.add(norm)
            parts = norm.split()
            if len(parts) >= 2:
                keys.add(parts[-1])
                keys.add(" ".join(parts[-2:]))
                keys.add(" ".join(parts[:2]))
    if cid:
        clean_id = re.sub(r"^char_", "", _strip_accents(cid).lower()).replace("_", " ").strip()
        if clean_id:
            keys.add(clean_id)
    return keys


def _mentioned_char_ids_in_text(text: str, chars: dict) -> list:
    """Tìm tất cả ID nhân vật đã khai báo trong `chars` được gọi tên trực tiếp (viết hoa chữ cái đầu) trong `text`."""
    if not text or not chars:
        return []
    cap_tokens = set()
    for m in re.finditer(rf"\b({_VN_CAP_WORD}(?:\s+{_VN_CAP_WORD}){{0,3}})\b", text):
        phrase = _strip_accents(m.group(1)).lower()
        cap_tokens.add(phrase)
        words = phrase.split()
        for w in words:
            cap_tokens.add(w)
        if len(words) >= 2:
            cap_tokens.add(" ".join(words[-2:]))

    matched = []
    tail_text = re.sub(r"(?:^|[.!?]\s+)\S+", "", text)
    tail_caps = {_strip_accents(m.group(1)).lower() for m in re.finditer(rf"\b({_VN_CAP_WORD})\b", tail_text)}
    for cid, c in chars.items():
        primary_names = {
            _strip_accents(str(x)).strip().lower()
            for x in [c.get("name"), c.get("short_name")]
            if x
        }
        all_names = primary_names | {
            _strip_accents(str(x)).strip().lower()
            for x in (c.get("aliases") or [])
            if x
        }
        if any(fn in cap_tokens for fn in all_names if " " in fn):
            matched.append(cid)
            continue
        for fn in primary_names:
            last_tok = fn.split()[-1]
            if fn in tail_caps or last_tok in tail_caps:
                matched.append(cid)
                break
    return matched


def _find_undeclared_proper_names(project: dict, chars: dict) -> list:
    """Quét lời dẫn (`beats.narration`) và lời thoại (`shot.audio.line`) để tìm các tên người được nhắc tới nhưng chưa tạo `characters`."""
    known_keys = set()
    for cid, c in chars.items():
        known_keys |= _char_name_keys(c, cid)

    texts = [b.get("narration", "") for b in project.get("beats", [])]
    for s in project.get("shots", []):
        texts.append(mf.shot_audio(s).get("line", ""))

    undeclared = []
    seen_norm = set()
    for t in texts:
        if not t:
            continue
        candidates = [m.group(1) for m in _MULTI_WORD_NAME_RE.finditer(t)]
        candidates += [m.group(1) for m in _HONORIFIC_NAME_RE.finditer(t)]
        for cand in candidates:
            norm = _strip_accents(cand).strip().lower()
            if not norm or norm in _NON_PERSON_PROPER or norm in seen_norm:
                continue
            parts = norm.split()
            if norm in known_keys or (len(parts) == 1 and parts[0] in known_keys):
                continue
            seen_norm.add(norm)
            undeclared.append(cand)
    return undeclared


def lint_shot(project: dict, shot: dict, cfg: dict) -> list:
    """Trả về danh sách {level, code, msg}. level: error | warn | info."""
    out = []

    def add(level, code, msg):
        out.append({"level": level, "code": code, "msg": msg})

    pcfg = cfg["prompt"]
    prompt = shot.get("veo_prompt") or ""
    chars = mf.characters_by_id(project)
    lang = normalize_lang(project.get("language") or project.get("plan", {}).get("language_code", "vi"))
    mode = shot.get("generation_mode") or "text"

    if not prompt.strip():
        add("error", "EMPTY_PROMPT", "Chưa có veo_prompt (chạy build-prompts nếu đã điền trường có cấu trúc).")
        return out

    all_cast = mf.shot_all_cast_ids(shot)
    # Tự động nới trần độ dài prompt khi cảnh có đông nhân vật có tên (4..20+ người), cầu nối chuyển động hoặc quần chúng nền
    tl_phases = shot.get("timeline_phases") if isinstance(shot.get("timeline_phases"), list) else []
    extra_cast_allowance = (
        max(0, (len(all_cast) - 1) * 95)
        + (160 if _crowd_atmosphere_line(project, shot) else 0)
        + (110 if shot.get("end_action") else 0)
        + (1600 + len(tl_phases) * 350 if tl_phases else 0)
    )
    max_chars_eff = pcfg["max_chars"] + extra_cast_allowance
    warn_chars_eff = pcfg["warn_chars"] + extra_cast_allowance

    n = len(prompt)
    if n > max_chars_eff:
        add("warn", "PROMPT_TOO_LONG", f"{n} ký tự > {max_chars_eff}. Prompt dài làm model bỏ qua chi tiết; giữ 1–2 hành động chính.")
    elif n > warn_chars_eff:
        add("info", "PROMPT_LONG", f"{n} ký tự — cân nhắc rút gọn (mục tiêu 400–{warn_chars_eff}).")
    elif n < pcfg["min_chars"]:
        add("warn", "PROMPT_TOO_SHORT", f"{n} ký tự — thiếu máy quay/ánh sáng/âm thanh.")

    junk = sorted({m.group(0) for m in JUNK_TOKENS.finditer(prompt)})
    if junk:
        add("warn", "JUNK_TOKENS", f"Token vô nghĩa với Veo: {', '.join(junk)}.")
    style_str = f"{project.get('visual_style', '')} {project.get('style_line', '')}".lower()
    if "live-action" in style_str or "photorealistic" in style_str:
        fantasy_traps = re.findall(r"\b(glowing\s+(?:\w+\s+)?eyes|blue-violet\s+lightning|purple\s+lightning|neon\s+\w+)\b", prompt, flags=re.I)
        if fantasy_traps:
            add("warn", "FANTASY_LIGHTING_TRAP",
                f"Phim live-action nhưng prompt chứa cụm từ gợi hiệu ứng giả tưởng/hoạt hình ({sorted(set(fantasy_traps))}) "
                "→ dễ sinh mắt đèn LED hoặc tinh thể tím giả tạo. Hãy thay bằng 'wet dark eyes with firelight catchlights' và '2700K amber firelight vs 6500K cold steel-teal rain rim light'.")
    negs = [m.group(0) for m in NEGATION.finditer(prompt)]
    if len(negs) >= 3:
        add("warn", "TOO_MANY_NEGATIONS", f"{len(negs)} cụm phủ định ({', '.join(negs[:5])}…). Chuyển sang negative_prompt và mô tả điều MUỐN thấy.")
    phases = TIMECODE.findall(prompt)
    max_phases_eff = max(pcfg["max_timecoded_phases"], len(tl_phases) + 2) if tl_phases else pcfg["max_timecoded_phases"]
    if len(phases) > max_phases_eff:
        add("warn", "TOO_MANY_PHASES", f"{len(phases)} pha có mốc giờ. Veo không bám mốc giờ chính xác; 1 clip nên có 1–2 hành động.")

    if tl_phases:
        focal_subjs = [cid for cid in (shot.get("subjects") or []) if cid in chars]
        for p_idx, ph in enumerate(tl_phases, 1):
            if not isinstance(ph, dict):
                continue
            t_lbl = ph.get("time") or f"#{p_idx}"
            if not ph.get("camera"):
                add("warn", "MISSING_PHASE_CAMERA", f"Pha [{t_lbl}] thiếu trường 'camera' (chuyển động ống kính/tiêu cự tại mốc giây đó).")
            if not (ph.get("vfx") or ph.get("environment")):
                add("warn", "MISSING_PHASE_VFX", f"Pha [{t_lbl}] thiếu trường 'vfx' (hiệu ứng vật lý/môi trường 3D tại mốc giây đó).")
            ph_sub = ph.get("subjects")
            if len(focal_subjs) >= 2 and isinstance(ph_sub, dict):
                missing_s = [cid for cid in focal_subjs if not (ph_sub.get(cid) or "").strip()]
                if missing_s:
                    add("warn", "PASSIVE_SUBJECT_IN_PHASE",
                        f"Pha [{t_lbl}] thiếu mô tả hành động riêng cho {missing_s} — mọi nhân vật trong khung hình phải có hành động/phản ứng rõ ràng theo từng giây.")
        if mode == "first_last" and (not shot.get("start_staging") or not shot.get("end_staging")):
            add("info", "MISSING_KEYFRAME_STAGING",
                "Shot có timeline_phases chi tiết nhưng chưa khai báo đầy đủ start_staging/end_staging cho ảnh Keyframe START/END.")

    subjects = shot.get("subjects", [])
    primary_set = set(subjects[:3] if len(subjects) <= 3 else subjects[:2])
    for cid in all_cast:
        c = chars.get(cid)
        if not c:
            add("error", "UNKNOWN_SUBJECT", f"Subject '{cid}' không có trong characters.")
            continue
        if not c.get("identity_line"):
            add("warn", "NO_IDENTITY_LINE", f"{cid} chưa có identity_line (mô tả chuẩn dán nguyên văn mọi shot).")
        else:
            full_id = c["identity_line"].strip().rstrip(".")
            comp_id = compact_identity(c)
            if cid in primary_set:
                if full_id not in prompt and comp_id not in prompt:
                    add("warn", "IDENTITY_LINE_DRIFT", f"Prompt không chứa nguyên văn identity_line của {cid} → mô tả trôi giữa các shot.")
            elif comp_id not in prompt and full_id not in prompt:
                add("warn", "IDENTITY_LINE_DRIFT", f"Nhân vật trong cảnh '{cid}' chưa có mô tả ngoại hình trong prompt.")
        if mode in ("text",) or (mode == "ingredients" and not (shot.get("reference_images") or c.get("reference_images"))):
            add("warn", "NO_IDENTITY_REFERENCE", f"{cid} xuất hiện nhưng shot không dùng ảnh tham chiếu (mode={mode}). Danh tính sẽ trôi giữa các clip.")

    # Kiểm tra nếu cảnh mô tả cả bàn/cả nhóm nhưng chỉ khai báo lèo tèo 1-2 người
    beat_id = shot.get("beat")
    beat_nar = next((b.get("narration", "") for b in project.get("beats", []) if b.get("beat_id") == beat_id), "")
    combined_context = f"{shot.get('action', '')} {shot.get('end_action', '')} {beat_nar}"
    cam_lower = (shot.get("camera") or shot.get("camera_shot") or "").lower()
    is_solo_studio = "podcast_studio" in (shot.get("environment") or "").lower() or "bedroom" in (shot.get("environment") or "").lower()
    is_wide_or_table = bool(re.search(r"\b(wide|group|table|two-shot|rooftop|cafe)\b", f"{cam_lower} {shot.get('action', '')}", re.I)) and not is_solo_studio
    if len(chars) >= 4 and len(all_cast) <= 2 and is_wide_or_table and _GROUP_KEYWORDS_RE.search(combined_context):
        add("warn", "GROUP_SCENE_UNDERPOPULATED",
            f"Nội dung cảnh/beat nói về cả nhóm/bàn đông người nhưng shot chỉ khai báo {len(all_cast)} nhân vật ({all_cast}). "
            f"Dự án có {len(chars)} nhân vật có tên — hãy đưa đầy đủ các nhân vật phụ trong bàn vào `ensemble_cast` (hoặc `subjects`) "
            "và thêm `background_crowd` nếu ở quán đông vui.")

    raw_mids = shot.get("mid_actions") if isinstance(shot.get("mid_actions"), list) else []
    wp_total = int(shot.get("waypoint_total", 1) or 1)
    if (len(raw_mids) >= 3 or wp_total >= 4) and not shot.get("allow_dense_waypoints"):
        lvl = "warn" if (len(raw_mids) >= 4 or wp_total >= 5) else "info"
        add(lvl, "TOO_MANY_WAYPOINTS",
            f"Shot chia thành {max(len(raw_mids) + 1, wp_total)} đoạn keyframe tĩnh liên tiếp — tạo quá nhiều frame tĩnh sát nhau "
            "làm vận tốc bị reset về 0 tại mỗi điểm nối (giật cục Stop-Motion). Nên dùng `timeline_phases` (3 pha động học trên 1 cặp START–END) hoặc cắt góc máy mới.")

    if mode in ("first_frame", "first_last") and not shot.get("first_frame_path"):
        add("error", "MISSING_FIRST_FRAME", f"mode={mode} nhưng chưa có first_frame_path.")
    if mode in ("first_frame", "first_last") and (
        shot.get("first_frame_source") == "storyboard_grid_draft" or shot.get("last_frame_source") == "storyboard_grid_draft"
    ):
        add("info", "STORYBOARD_GRID_DRAFT_KEYFRAME",
            "Keyframe hiện tại đang là ô cắt từ ảnh lưới Storyboard Grid (độ phân giải gốc thấp) — nên chạy `flow-generate --kind frames` "
            "để nâng cấp lên Hero Keyframe 1080p sắc nét trước khi tạo video.")
    if mode == "first_last":
        if not shot.get("last_frame_path"):
            add("error", "MISSING_LAST_FRAME", "mode=first_last nhưng chưa có last_frame_path.")
        add("info", "FIRST_LAST_FRAMING", "First/Last frame phải cùng cỡ cảnh, góc máy, ánh sáng — khác nhau sẽ gây biến hình.")
        raw_cam_check = (shot.get("camera") or shot.get("camera_shot") or "") if tl_phases else prompt
        if not shot.get("dynamic_camera") and re.search(r"\b(push[- ]in|pull[- ]back|zoom[- ]?(?:in|out)?)\b", raw_cam_check, flags=re.I):
            add("warn", "FIRST_LAST_CAMERA_MISMATCH",
                "veo_prompt có lệnh push-in/pull-back/zoom nhưng Keyframe START/END cùng cỡ cảnh (dynamic_camera=False) "
                "→ dễ gây chồng mờ (dissolve) ở giây thứ 6. Chạy lại `build-prompts` để đồng bộ hoặc đặt `dynamic_camera: true`.")
    if mode == "extend" and not shot.get("extends"):
        add("error", "MISSING_EXTEND_PARENT", "mode=extend cần trường `extends` (shot_id clip gốc).")

    audio = mf.shot_audio(shot)
    if audio["mode"] not in AUDIO_MODES:
        add("error", "BAD_AUDIO_MODE", f"audio.mode '{audio['mode']}' không hợp lệ ({', '.join(AUDIO_MODES)}).")
    line = audio.get("line", "")
    if line and audio["mode"] in ("veo_dialogue", "veo_narration"):
        rates = LANGUAGE_RATES[lang]
        units = count_speech_units(line, lang)
        if units > rates["hard_max_per_8s"]:
            add("error", "LINE_TOO_LONG", f"Thoại {units} {rates['unit']} > {rates['hard_max_per_8s']} cho 8s.")
        elif units > rates["rec_max_per_8s"]:
            add("warn", "LINE_LONG", f"Thoại {units}/{rates['rec_max_per_8s']} {rates['unit']} — sát ngưỡng 8s.")
    voice = shot_voice(project, shot)
    if line and audio["mode"] in ("veo_dialogue", "veo_narration"):
        if not voice:
            who = audio.get("speaker") or "người dẫn (narrator_voice)"
            add("warn", "NO_FIXED_VOICE", f"Lời nói trong Veo chưa gắn giọng cố định cho {who} → mỗi clip một giọng. "
                                           "Đặt `voice` cho nhân vật / `narrator_voice` cho dự án rồi gắn giọng đó trên Flow.")
        if audio["mode"] == "veo_narration":
            add("info", "NARRATION_IN_VEO", "Lời dẫn nằm trong clip: sửa 1 chữ phải tạo lại clip, không kéo lời qua nhiều shot được. "
                                             "Phim nhiều lời dẫn nên dùng voiceover_external (cùng tên giọng).")
    if voice and voice not in KNOWN_VOICES:
        add("info", "UNKNOWN_VOICE", f"Giọng '{voice}' không có trong danh sách đã biết — kiểm tra lại tên trên Flow.")
    if len(all_cast) >= 2 and mode == "ingredients":
        add("info", "MULTI_SUBJECT_COMPOSITION", f"Cảnh có {len(all_cast)} nhân vật dùng mode=ingredients: nếu cần kiểm soát "
                                                 "chặt vị trí trái/phải (quy tắc 180°) và hướng nhìn, nên dựng first_frame trước.")
    return out


def lint_project(project: dict, cfg: dict) -> list:
    """Kiểm tra cấu trúc tổng thể của dự án (nhịp truyện beat, đầy đủ 1..N nhân vật được gọi tên, liên kết đạo cụ/bối cảnh)."""
    out = []

    def add(level, code, msg):
        out.append({"level": level, "code": code, "msg": msg})

    shots = [s for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    chars = mf.characters_by_id(project)

    # 1. Quét toàn bộ kịch bản xem có nhân vật nào được gọi tên riêng nhưng chưa tạo trong `manifest.characters`
    undeclared_names = _find_undeclared_proper_names(project, chars)
    if undeclared_names:
        add("warn", "UNDECLARED_NAMED_CHARACTER",
            f"Kịch bản/lời dẫn nhắc tên riêng {undeclared_names} nhưng chưa tạo trong `manifest.characters`. "
            "Nguyên tắc bắt buộc: kêu tên ai trong truyện thì người đó phải có hồ sơ tạo hình riêng (không giới hạn 5 hay 10–20 người).")

    # 2. Quét từng beat xem nhân vật đã tạo được gọi tên trong lời dẫn có mặt trong các shot của beat đó chưa
    for b in project.get("beats", []):
        bid = b.get("beat_id", "")
        nar = b.get("narration", "")
        mentioned_cids = _mentioned_char_ids_in_text(nar, chars)
        if not mentioned_cids:
            continue
        beat_shots = [s for s in shots if s.get("beat") == bid]
        if not beat_shots:
            continue
        present_cids = set()
        for s in beat_shots:
            present_cids.update(mf.shot_all_cast_ids(s))
        missing_in_beat = [cid for cid in mentioned_cids if cid not in present_cids]
        if missing_in_beat:
            missing_labels = [f"{display_name(chars[c], c)} ({c})" for c in missing_in_beat]
            add("warn", "NAMED_CHARACTER_MISSING_IN_SCENE",
                f"Beat '{bid}' gọi tên {', '.join(missing_labels)} nhưng chưa có mặt trong `subjects` hoặc `ensemble_cast` "
                f"của các shot {[s['shot_id'] for s in beat_shots]}. Kêu tên ai thì người đó phải xuất hiện trong cảnh!")

    if len(shots) >= 6 and project.get("audio_strategy") == "voiceover_external" and not project.get("beats"):
        add("warn", "NO_BEATS_DEFINED",
            f"Dự án có {len(shots)} shot dùng voiceover_external nhưng chưa định nghĩa `beats` — lời dẫn sẽ bị "
            "đóng khung theo từng shot (không có L-cut/J-cut trải qua nhiều góc máy).")

    if len(shots) >= 6:
        veo_dlg = [s["shot_id"] for s in shots if mf.shot_audio(s)["mode"] == "veo_dialogue"]
        if len(veo_dlg) / len(shots) > 0.65:
            add("warn", "EXCESSIVE_VEO_DIALOGUE",
                f"{len(veo_dlg)}/{len(shots)} shot ({len(veo_dlg)/len(shots):.0%}) dùng `veo_dialogue` (nhép miệng trực tiếp). "
                "Nên áp dụng cấu trúc Hybrid 50/50: chỉ giữ `veo_dialogue` cho cảnh cận nhân vật nói câu đắt giá, "
                "còn lại chuyển sang cảnh phản ứng/đặc tả đạo cụ (`voiceover_external` + `first_frame`/`first_last`) "
                "để giảm 50% thời gian render và tránh lỗi méo miệng.")
        ing_only = [s["shot_id"] for s in shots if s.get("generation_mode") == "ingredients" and not s.get("first_frame_path")]
        if len(ing_only) / len(shots) > 0.70:
            add("info", "PREFER_KEYFRAME_FIRST",
                f"{len(ing_only)}/{len(shots)} shot đang dùng `ingredients` không có Keyframe mở đầu. "
                "Nên ưu tiên chế độ `first_frame` / `first_last` (tạo ảnh Keyframe 0 credit trên Nano Banana trước) "
                "để khóa bố cục và giảm tỷ lệ tạo lại.")

    props = mf.props_by_id(project)
    if props:
        used_props = set()
        for s in shots:
            for pid in s.get("props", []):
                if pid in props:
                    used_props.add(pid)
            act = (s.get("action") or "").lower()
            for pid, p_obj in props.items():
                pname = (p_obj.get("name") or "").lower()
                if pname and pname in act:
                    used_props.add(pid)
        unused = [pid for pid in props if pid not in used_props]
        if unused:
            add("info", "UNLINKED_PROPS",
                f"Đạo cụ {unused} đã khai báo nhưng chưa gắn vào `shot.props` hoặc `shot.action` của shot nào.")

    # Kiểm tra quy tắc 30 độ / chống trùng góc máy ngang (Flat Two-Shot Streak) cho phim hành động/nhiều shot
    flat_streak = []
    for s in shots:
        cam_s = (s.get("camera") or s.get("camera_shot") or "").lower()
        sp_m = (s.get("spatial_mode") or "").lower()
        is_macro = bool(re.search(r"\b(extreme close-up|macro|insert|detail|eye|foot|claw|jaws)\b", cam_s))
        is_ots_or_pov = bool(re.search(r"\b(over-the-shoulder|ots|pov|ground-level|ankle-level|bird|overhead|3/4)\b", cam_s)) or sp_m in (
            "ots_left", "ots_right", "depth_clash", "clinched_grapple", "jaw_clamp", "low_angle_3d"
        )
        if len(s.get("subjects", [])) >= 2 and not is_macro and not is_ots_or_pov:
            flat_streak.append(s["shot_id"])
            if len(flat_streak) >= 3:
                add("info", "MONOTONOUS_CAMERA_COVERAGE",
                    f"Các shot {flat_streak[-3:]} liên tiếp đều dùng góc máy ngang 2 chủ thể (flat two-shot) -> dễ gây cảm giác nhảy hình (jump-cut) và đánh nhau tại chỗ. "
                    "Hãy xen kẽ góc chụp qua vai theo chiều sâu (`Over-the-shoulder` / `spatial_mode: ots_left`), góc sát đất `1.2m Ground-level POV`, hoặc cú cắt đặc tả `Extreme close-up Macro` (1.2s–1.8s).")
        else:
            flat_streak = []
    return out


def complexity_score(shot: dict, index: int, total: int) -> tuple:
    cam_text = " ".join(str(shot.get(k) or "") for k in ("camera", "camera_shot"))
    act_text = str(shot.get("action") or "")
    if not act_text:
        act_text = re.split(r"saying[^:]*:|says[^:]*:", shot.get("veo_prompt") or "", flags=re.I)[0]
    act_clean = re.sub(r"\b(push[- ]in|pull[- ]back)\b", "", act_text, flags=re.I)
    text = f"{act_text} {cam_text}"
    score, reasons = 1, []
    if INTERACTION_WORDS.search(act_clean):
        score += 4
        reasons.append("tương tác vật lý / tay cầm nắm")
    if len(shot.get("subjects", [])) >= 2 or re.search(r"two-shot|over-the-shoulder", text, re.I):
        score += 3
        reasons.append("nhiều chủ thể trong khung")
    if DETAIL_WORDS.search(text):
        score += 2
        reasons.append("cận chi tiết giải phẫu")
    if index == 0 or index == total - 1 or shot.get("is_hook"):
        score += 3
        reasons.append("hook / cảnh kết")
    if (mf.shot_audio(shot)["mode"]) == "veo_dialogue":
        score += 2
        reasons.append("nhép miệng")
    if shot.get("waypoint_subshot") and mf.shot_audio(shot)["mode"] != "veo_dialogue":
        score = max(1, score - 4)
        reasons.append("đã chia nhỏ bằng waypoint trung gian (1 vi chuyển động)")
    elif (
        shot.get("generation_mode") in ("first_frame", "first_last")
        and mf.shot_audio(shot)["mode"] != "veo_dialogue"
        and not INTERACTION_WORDS.search(act_clean)
    ):
        discount = 3 if shot.get("generation_mode") == "first_last" else 2
        score = max(1, score - discount)
        reasons.append("đã khóa bố cục bằng keyframe (in-betweening)")
    return min(10, score), reasons or ["cảnh đơn giản"]


def route_model(score: int, cfg: dict) -> dict:
    tier = "quality" if score >= cfg["credits"]["quality_threshold"] else "fast"
    m = cfg["models"]["video"][tier]
    return {"tier": tier, "label": m["label"], "credits": m["credits"]}


def build_storyboard_grid_prompt(project: dict, rows: int = 3, cols: int = 3, panels: list = None) -> str:
    """Dựng prompt 1 ảnh Storyboard Grid tổng hợp (vd: 3x3 = 9 ô hoặc 2x2 = 4 ô cùng tỷ lệ khung hình dự án)."""
    from . import storyboard as sb

    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)
    aspect = project.get("aspect_ratio", "16:9")
    n_panels = rows * cols
    if not panels:
        panels = sb.default_grid_panels(project, rows=rows, cols=cols)

    header = (
        f"Seamless edge-to-edge {cols}x{rows} cinematic storyboard contact sheet "
        f"({n_panels} equal {aspect} widescreen panels arranged in {rows} rows of {cols} columns, "
        f"reading left-to-right from top row to bottom row, separated by thin 2px solid black divider lines, "
        f"zero outer margin, no text, no numbers, no labels)."
    )

    cast_bits = []
    for idx, cid in enumerate(chars, 1):
        c = chars[cid]
        cname = display_name(c, cid)
        id_line = (c.get("identity_line") or "").strip().rstrip(".")
        if id_line:
            cast_bits.append(f"{cname} (reference {idx}: {id_line})")
    cast_header = f"Shared Cast across all {n_panels} panels: " + "; ".join(cast_bits) + "." if cast_bits else ""

    env_line = ""
    if envs:
        first_env = next(iter(envs.values()))
        env_line = (first_env.get("identity_line") or first_env.get("name") or "").strip().rstrip(".")
    style_line = (project.get("style_line") or project.get("visual_style") or "").strip().rstrip(".")
    world_header = f"Shared World & Lighting: {env_line}. {style_line}." if env_line or style_line else ""

    col_names = {1: ["Center"], 2: ["Left", "Right"], 3: ["Left", "Center", "Right"], 4: ["Col 1", "Col 2", "Col 3", "Col 4"]}
    c_labels = col_names.get(cols, [f"Col {i+1}" for i in range(cols)])

    panel_lines = []
    for p in panels[:n_panels]:
        r_idx = int(p.get("row", (p["index"] - 1) // cols + 1))
        c_idx = int(p.get("col", (p["index"] - 1) % cols + 1))
        c_lbl = c_labels[c_idx - 1] if 1 <= c_idx <= len(c_labels) else f"Col {c_idx}"
        desc = (p.get("description") or "").strip().rstrip(".")
        panel_lines.append(f"Panel {p['index']} (Row {r_idx} {c_lbl}): {desc}.")

    footer = (
        f"100% consistent character anatomy, scale, and Chiaroscuro lighting across all {n_panels} panels. "
        f"Strictly {n_panels} clean {aspect} frames in a {cols}x{rows} grid; no text, no captions, no numbers, no watermarks."
    )
    parts = [header, cast_header, world_header, " ".join(panel_lines), footer]
    return re.sub(r"\s{2,}", " ", " ".join(x for x in parts if x)).strip()
