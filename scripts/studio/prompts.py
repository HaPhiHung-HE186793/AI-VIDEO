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

# Hệ thống Đạo diễn Đa Thể Loại Toàn Diện (Universal Genre Director Profiles)
GENRE_PROFILES = {
    "action_blockbuster": {
        "label": "Hành động / Đại chiến IMAX (Action / Monster / Blockbuster)",
        "style_line": (
            "Live-action IMAX 65mm anamorphic cinematography, physical contact mass coupling, "
            "Chiaroscuro 2700K warm firelight vs 6500K cold steel-teal rim lighting, 180-degree shutter natural motion blur, fine 35mm film grain"
        ),
        "negative_prompt": (
            "plastic CGI skin, weightless floating motion, slow-motion hovering, glowing LED eyes, purple neon lightning, "
            "cartoon cel-shading, extra limbs, morphing anatomy, subtitles, watermark"
        ),
        "lut_preset": "blockbuster",
        "music_mood": "combat",
        "avg_shot_sec": 3.2,
        "char_type": "creature",
    },
    "wuxia_xianxia": {
        "label": "Cổ trang / Kiếm hiệp / Tiên hiệp (Wuxia / Xianxia / Eastern Fantasy)",
        "style_line": (
            "Prestige Eastern cinema anamorphic 50mm lens, flowing silk garment physics in mountain wind, "
            "atmospheric ink-wash mist, warm lantern gold key light against deep jade-cyan moonlight shadows, tactile martial choreography"
        ),
        "negative_prompt": (
            "modern clothing, plastic mannequin face, stiff cape, western architecture, neon cyberpunk signs, "
            "floating disembodied swords, deformed hands, extra fingers, subtitles, watermark"
        ),
        "lut_preset": "wuxia_jade",
        "music_mood": "combat",
        "avg_shot_sec": 3.5,
        "char_type": "human",
    },
    "cyberpunk_scifi": {
        "label": "Khoa học viễn tưởng / Cyberpunk (Sci-Fi / Cyberpunk)",
        "style_line": (
            "Anamorphic Panavision sci-fi cinematography, wet asphalt reflections, volumetric sodium-vapor amber and cyan-teal "
            "holographic rim lighting, rain-streaked optical lens flare, grounded hard-surface mechanical detail"
        ),
        "negative_prompt": (
            "flat daylight, cartoon 2D illustration, blurry low-res textures, medieval props, rubbery armor, "
            "morphing helmet visor, extra fingers, subtitles, watermark"
        ),
        "lut_preset": "cyberpunk_neon",
        "music_mood": "tension",
        "avg_shot_sec": 3.5,
        "char_type": "human",
    },
    "horror_thriller": {
        "label": "Kinh dị / Giật gân / Trinh thám (Horror / Psychological Thriller)",
        "style_line": (
            "A24 psychological thriller 35mm cinematography, deep low-key chiaroscuro shadows, practical flickering tungsten bulb "
            "and cold moonlight shafts, claustrophobic shallow depth of field, raw unsettling realism"
        ),
        "negative_prompt": (
            "bright cheerful lighting, oversaturated colors, comedic expressions, glossy beauty filter, "
            "cartoon monster, morphing walls, subtitles, watermark"
        ),
        "lut_preset": "noir_thriller",
        "music_mood": "tension",
        "avg_shot_sec": 4.2,
        "char_type": "human",
    },
    "romance_kdrama": {
        "label": "Ngôn tình / Tâm lý / Điện ảnh Lãng mạn (Romance / K-Drama / Slice of Life)",
        "style_line": (
            "Prestige romantic cinema 85mm f/1.4 portrait lens, creamy bokeh, soft golden-hour backlight and warm practical lamps, "
            "natural translucent skin micro-texture, subtle emotional micro-expressions"
        ),
        "negative_prompt": (
            "harsh horror shadows, distorted facial features, uncanny valley grin, plastic doll skin, "
            "jerky fast camera shake, extra fingers, subtitles, watermark"
        ),
        "lut_preset": "romance_pastel",
        "music_mood": "podcast_lofi",
        "avg_shot_sec": 4.8,
        "char_type": "human",
    },
    "anime_2d_3d": {
        "label": "Hoạt hình Anime 2D / 3D Donghua (Theatrical Anime / Stylized Animation)",
        "style_line": (
            "Theatrical 2D anime cinematography, hand-drawn key animation line art with multi-plane camera parallax, "
            "dramatic rim lighting, expressive sakuga motion arcs, rich painted background art"
        ),
        "negative_prompt": (
            "photorealistic human skin pores, live-action footage, uncanny 3D wax doll, inconsistent line weight, "
            "blurry smeared faces, extra limbs, subtitles, watermark"
        ),
        "lut_preset": "anime_vibrant",
        "music_mood": "wonder",
        "avg_shot_sec": 3.5,
        "char_type": "cartoon",
    },
    "sitcom_podcast": {
        "label": "Sitcom / Podcast / Hài đời thường (Ensemble Sitcom / Visual Podcast)",
        "style_line": (
            "Warm cinematic ensemble comedy coverage, 35mm medium two-shots and over-the-shoulder angles, "
            "cozy practical tungsten cafe lighting, expressive natural body language and lip-sync"
        ),
        "negative_prompt": (
            "attribute swapping between characters, extra arms, floating coffee cups, dark horror shadows, "
            "lip-sync on non-speaking listeners, subtitles, watermark"
        ),
        "lut_preset": "warm_dawn",
        "music_mood": "podcast_lofi",
        "avg_shot_sec": 4.2,
        "char_type": "human",
    },
    "nature_documentary": {
        "label": "Tài liệu Thiên nhiên / Khoa học (BBC Natural History / Science Documentary)",
        "style_line": (
            "Photorealistic BBC Planet Earth III natural history cinematography, 400mm f/2.8 telephoto lens compression, "
            "authentic animal biomechanics, wet skin and feather micro-detail, natural atmospheric daylight"
        ),
        "negative_prompt": (
            "cartoon animation, anthropomorphic clothing, glowing fantasy eyes, CGI plastic sheen, "
            "weightless sliding feet, morphing species, subtitles, watermark"
        ),
        "lut_preset": "documentary",
        "music_mood": "wonder",
        "avg_shot_sec": 4.5,
        "char_type": "creature",
    },
    "commercial_product": {
        "label": "TVC Quảng cáo / Sản phẩm Cao cấp (Luxury Commercial / Product Macro)",
        "style_line": (
            "High-end commercial macro cinematography, Arri Alexa Mini LF with 100mm macro probe lens, "
            "precision studio specular rim lighting, crisp fluid and surface micro-physics, razor-sharp focus falloff"
        ),
        "negative_prompt": (
            "warped product logo, melting geometry, muddy lighting, amateur handheld blur, "
            "deformed hands holding product, extra fingers, subtitles, watermark"
        ),
        "lut_preset": "blockbuster",
        "music_mood": "wonder",
        "avg_shot_sec": 2.6,
        "char_type": "human",
    },
    "historical_epic": {
        "label": "Sử thi / Lịch sử / Chiến tranh (Historical Epic / Period Drama)",
        "style_line": (
            "Epic historical cinema 65mm film look, authentic period armor and weathered fabric textures, "
            "natural torchlight and volumetric battlefield smoke, grounded physical weight, 35mm organic grain"
        ),
        "negative_prompt": (
            "modern wristwatches, plastic props, neon lighting, synthetic polyester clothes, "
            "weightless sword swings, extra limbs, subtitles, watermark"
        ),
        "lut_preset": "wuxia_jade",
        "music_mood": "combat",
        "avg_shot_sec": 4.0,
        "char_type": "human",
    },
}


def resolve_genre_profile(project: dict) -> dict:
    """Xác định hồ sơ đạo diễn theo thể loại (`genre`) của dự án (khai báo tường minh hoặc tự nhận diện)."""
    explicit = (project.get("genre") or "").strip().lower()
    if explicit in GENRE_PROFILES:
        return {"genre": explicit, **GENRE_PROFILES[explicit]}
    blob = " ".join(
        str(project.get(k) or "") for k in ("project_name", "project_slug", "title", "visual_style", "style_line")
    ).lower()
    if any(w in blob for w in ("wuxia", "xianxia", "kiếm hiệp", "tiên hiệp", "cổ trang", "cultivator", "jianghu")):
        key = "wuxia_xianxia"
    elif any(w in blob for w in ("cyberpunk", "sci-fi", "scifi", "mecha", "spaceship", "neon city")):
        key = "cyberpunk_scifi"
    elif any(w in blob for w in ("horror", "thriller", "kinh dị", "ám ảnh", "ghost", "haunted")):
        key = "horror_thriller"
    elif any(w in blob for w in ("romance", "kdrama", "ngôn tình", "lãng mạn", "tình yêu", "love story")):
        key = "romance_kdrama"
    elif any(w in blob for w in ("anime", "2d animation", "cartoon", "cel-shaded", "hoạt hình", "manga")):
        key = "anime_2d_3d"
    elif any(w in blob for w in ("podcast", "sitcom", "cafe", "bàn tiệc", "tâm sự", "comedy")):
        key = "sitcom_podcast"
    elif any(w in blob for w in ("tvc", "commercial", "product", "quảng cáo", "luxury")):
        key = "commercial_product"
    elif any(w in blob for w in ("historical", "lịch sử", "chiến tranh", "dynasty", "sử thi")):
        key = "historical_epic"
    elif any(w in blob for w in ("battle", "combat", "vs", "showdown", "clash", "đại chiến")):
        key = "action_blockbuster"
    else:
        key = "nature_documentary"
    return {"genre": key, **GENRE_PROFILES[key]}


def apply_genre_profile(project: dict, genre_key: str, overwrite: bool = False) -> dict:
    """Áp dụng chuẩn Đạo diễn Hình ảnh & Âm thanh của thể loại `genre_key` vào `project_manifest.json`."""
    gkey = (genre_key or "").strip().lower()
    if gkey not in GENRE_PROFILES:
        raise ValueError(f"Thể loại '{genre_key}' không hợp lệ. Chọn trong: {', '.join(GENRE_PROFILES)}")
    prof = GENRE_PROFILES[gkey]
    project["genre"] = gkey
    if overwrite or not project.get("visual_style") or project.get("visual_style") == "cinematic photorealistic":
        project["visual_style"] = prof["style_line"]
    if overwrite or not project.get("style_line") or project.get("style_line") == "cinematic photorealistic":
        project["style_line"] = prof["style_line"]
    if overwrite or not project.get("negative_prompt"):
        project["negative_prompt"] = prof["negative_prompt"]
    if overwrite or not project.get("music_mood"):
        project["music_mood"] = prof["music_mood"]
    if overwrite or not project.get("lut_preset"):
        project["lut_preset"] = prof["lut_preset"]
    return {"genre": gkey, **prof}

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


def strip_transient_vfx_for_keyframe(text: str) -> str:
    """Khử các hiệu ứng hạt thoáng qua (giọt nước nhỏ thành dòng từ cằm, vòng sóng âm lơ lửng) khỏi prompt Keyframe tĩnh.

    Nếu đưa 'water droplets dripping from its chin' hoặc 'concentric acoustic shockwave rings' vào ảnh tĩnh START/END,
    Nano Banana sẽ vẽ các tia nước liền mạch hoặc vòng tròn trắng lơ lửng; khi vào Veo `first_last`, mô hình buộc phải
    giữ nguyên tia nước đó suốt 3–4 giây như vòi nước tĩnh. Hàm này chuyển chúng về trạng thái bề mặt bền vững.
    """
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(
        r"\bwater\s+droplets\s+dripping\s+from\s+(?:its|his|her|the)?\s*([a-z]+)(?:\s+into\s+[^,.;]+)?",
        r"wet glistening \1 above the rippling water surface",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(?:dripping|pouring)\s+(?:streams?\s+of\s+)?water\s+from\s+(?:its|his|her|the)?\s*([a-z]+)",
        r"wet glistening \1",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(?:concentric\s+)?(?:cymatic\s+|acoustic\s+|sound[- ]?wave\s+|shockwave\s+)+(?:rings|circles|waves)\b[^,.;]*",
        "natural surface ripples and mist",
        s,
        flags=re.I,
    )
    return s


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
            clean_p = strip_transient_vfx_for_keyframe((str(pose_txt or "")).strip(" ."))
            if not clean_p:
                continue
            c_name = display_name(chars.get(cid, {}), cid)
            if clean_p.lower().startswith(c_name.lower()):
                p_list.append(clean_p)
            else:
                p_list.append(f"{c_name}: {clean_p}")
        if p_list:
            parts.append(_sentence(f"Character Staging & Anatomy: {' | '.join(p_list)}"))
    contact_phys = strip_transient_vfx_for_keyframe((stg.get("contact_physics") or "").strip(" ."))
    if contact_phys:
        parts.append(_sentence(f"Physical Contact & Mass Coupling: {contact_phys}"))
    vfx_env = strip_transient_vfx_for_keyframe((stg.get("vfx_environment") or stg.get("vfx") or "").strip(" ."))
    if vfx_env:
        parts.append(_sentence(f"Environment & 3D VFX State: {vfx_env}"))
    return " ".join(parts)


def _build_motion_arc(shot: dict, chars: dict = None) -> str:
    """Ghép câu quỹ đạo chuyển động: ưu tiên `timeline_phases` chi tiết theo từng giây, dự phòng 3 pha (Start/Entry -> Bridge -> End/Exit)."""
    if shot.get("timeline_phases"):
        tl_str = _build_director_timeline(shot, chars)
        if tl_str:
            return tl_str
    start_act = _clean_kinematic_action(shot.get("start_action") or shot.get("entry_state") or "")
    act = _clean_kinematic_action(shot.get("action") or "")
    end_act = _clean_kinematic_action(shot.get("end_action") or shot.get("exit_state") or "")
    if re.search(r"\bthen smoothly transition(?:s|ing)\b", act, flags=re.I):
        return _sentence(act)
    if shot.get("generation_mode") == "first_last" and end_act:
        if start_act and start_act.lower() != act.lower() and end_act.lower() != act.lower() and start_act.lower() not in act.lower():
            return _sentence(f"Starting from {start_act}, {act}, then smoothly settling into the final state where {end_act}")
        if end_act.lower() != act.lower() and end_act.lower() not in act.lower():
            return _sentence(f"{act}, then smoothly transitioning so {end_act}")
    return _sentence(act or start_act or end_act)


def _format_cast_lines(shot: dict, chars: dict, project: dict = None) -> list:
    """Định dạng danh sách nhân vật có tên (từ 1 đến 20+ người) đồng bộ tuyệt đối giữa Keyframe START, END và Veo Prompt.

    - Khóa vị trí Trái/Giữa/Phải (`On the left / In the center / On the right`) cho các nhân vật tiêu điểm (`subjects`)
      ở CẢ 3 TẦNG để Nano Banana không vẽ ngược bên với Veo.
    - Hỗ trợ biến thể trang phục / trạng thái theo cảnh (`character_states` / `wardrobe_variants` chuẩn `OmniChar`).
    - Khi cảnh có từ 4..20+ nhân vật (qua `subjects` hoặc `ensemble_cast` / `table_group`), tự động liệt kê đầy đủ
      100% nhân vật được gọi tên kèm tạo hình rút gọn (`compact_identity`) theo sơ đồ chỗ ngồi quanh bàn/cảnh.
    """
    proj_ctx = project if isinstance(project, dict) else {"characters": list(chars.values())}
    focal_ids = [cid for cid in (shot.get("subjects") or []) if cid in chars]
    all_cast = [cid for cid in mf.shot_all_cast_ids(shot) if cid in chars]
    lines = []

    # Tầng 1: Nhân vật tiêu điểm (1..3 người đang thực hiện hành động chính) kèm full identity_line + state override
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
            state_desc = mf.resolve_character_state(proj_ctx, shot, cid)
            state_suffix = f" (current state/wardrobe: {state_desc})" if state_desc else ""
            lines.append(_sentence(f"{prefix}{display_name(c, cid)} is {c['identity_line'].rstrip('.')}{state_suffix}"))

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
        roster = []
        for cid in all_cast:
            if cid in primary_set:
                roster.append(display_name(chars[cid], cid))
            else:
                st = mf.resolve_character_state(proj_ctx, shot, cid)
                comp = compact_identity(chars[cid])
                desc = f"{comp}; {st}" if (comp and st) else (comp or st)
                roster.append(f"{display_name(chars[cid], cid)} ({desc})" if desc else display_name(chars[cid], cid))
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
    parts += _format_cast_lines(shot, chars, project=project)
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
    if isinstance(shot.get("start_staging"), str) and shot["start_staging"].strip():
        return shot["start_staging"].strip()
    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)
    props = mf.props_by_id(project)

    cam = re.sub(
        r"\b(slow|very slow|gentle|subtle|smooth)?\s*(push[- ]in|pull[- ]back|pan|tilt|track(?:ing)?|dolly|orbit|zoom)\b[^,.]*",
        "",
        shot.get("camera") or shot.get("camera_shot") or "",
        flags=re.I,
    ).strip(" ,.")
    pose = strip_transient_vfx_for_keyframe(
        _clean_kinematic_action(shot.get("start_action") or shot.get("entry_state") or shot.get("action") or "")
    )
    cam_head = (cam or shot.get("camera") or shot.get("camera_shot") or "").rstrip(".")
    parts = [_sentence(f"{cam_head}: {pose}" if cam_head and pose else (cam_head or pose))]
    if shot.get("grid_panel_start_path") and shot.get("use_grid_layout_ref", True):
        parts.append(
            "Hero 1080p keyframe upgrade from the attached storyboard layout reference panel: preserve the panel's "
            "camera composition and color palette while rendering full high-frequency skin/scale textures and sharp anatomical detail from the character references."
        )

    all_cast = mf.shot_all_cast_ids(shot)
    parts += _format_cast_lines(shot, chars, project=project)
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

    end_pose = strip_transient_vfx_for_keyframe(
        _clean_kinematic_action(shot.get("end_action") or shot.get("exit_state") or shot.get("action") or "")
    )
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
    parts += _format_cast_lines(shot, chars, project=project)
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
    if not items[0] and project.get("genre") in GENRE_PROFILES:
        items[0] = GENRE_PROFILES[project["genre"]].get("negative_prompt", "")
    if shot.get("generation_mode") == "first_last":
        items.append(
            "cross-dissolve, double exposure, ghosting, mid-clip jump cut, attribute swapping, "
            "film strip border, kodak frame text, concentric sound rings, cartoon shockwave circles"
        )
    return ", ".join(x.strip(" ,") for x in items if x and x.strip(" ,"))


def infer_shot_eyeline(shot: dict) -> str:
    """Suy luận hướng nhìn ngang (`left` | `right` | ``) của chủ thể trong shot (phục vụ kiểm tra Eyeline Match 180°)."""
    explicit = str(shot.get("eyeline") or shot.get("screen_direction") or "").strip().lower()
    if explicit in ("left", "looking_left", "screen_left", "right_to_left"):
        return "left"
    if explicit in ("right", "looking_right", "screen_right", "left_to_right"):
        return "right"
    blob = f"{shot.get('start_action', '')} {shot.get('action', '')}"
    m = re.search(
        r"\b(?:looking|gazing|staring|glancing|facing)\s+(?:off[- ]?screen\s+|to\s+the\s+|toward\s+the\s+|screen\s+)?(left|right)\b",
        blob,
        flags=re.I,
    )
    return m.group(1).lower() if m else ""


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
    c_states = shot.get("character_states") if isinstance(shot.get("character_states"), dict) else {}
    state_allowance = sum(len(mf.resolve_character_state(project, shot, cid)) + 34 for cid in all_cast if mf.resolve_character_state(project, shot, cid))
    extra_cast_allowance = (
        max(0, (len(all_cast) - 1) * 95)
        + state_allowance
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

    for st_cid in c_states:
        if st_cid not in chars:
            add("warn", "UNKNOWN_CHARACTER_STATE", f"character_states khai báo cho '{st_cid}' nhưng nhân vật này không có trong `characters`.")
        elif st_cid not in all_cast:
            add("info", "UNUSED_CHARACTER_STATE", f"character_states khai báo cho '{st_cid}' nhưng nhân vật không có trong `subjects`/`ensemble_cast` của shot.")

    # Kiểm tra mâu thuẫn vị trí Trái/Phải ngay trong nội bộ 1 shot (subjects[0] mặc định bên Trái nhưng start_staging lại đặt bên Phải)
    focal_valid = [cid for cid in subjects if cid in chars]
    if len(focal_valid) >= 2 and bool(shot.get("spatial_lock", True)):
        raw_stg = shot.get("start_staging")
        stg_poses = (raw_stg.get("subject_poses") if isinstance(raw_stg, dict) else None) or {}
        if isinstance(stg_poses, dict):
            left_cid, right_cid = focal_valid[0], focal_valid[1]
            left_pose = str(stg_poses.get(left_cid) or "")
            right_pose = str(stg_poses.get(right_cid) or "")
            if re.search(r"\b(?:positioned|standing|sitting|anchored|looming)\s+(?:in\s+the\s+foreground\s+|in\s+the\s+midground\s+)?on\s+the\s+right\b", left_pose, re.I) or re.search(
                r"\b(?:positioned|standing|sitting|anchored|looming)\s+(?:in\s+the\s+foreground\s+|in\s+the\s+midground\s+)?on\s+the\s+left\b", right_pose, re.I
            ):
                add("warn", "SPATIAL_AXIS_CONTRADICTION",
                    f"Mâu thuẫn trục Trái/Phải trong shot: `subjects` đặt [{left_cid} (Trái), {right_cid} (Phải)] nhưng `start_staging.subject_poses` lại mô tả ngược bên. "
                    "Hãy đồng bộ thứ tự `subjects` với mô tả vị trí trong `start_staging`.")

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
        start_poses = (shot.get("start_staging") or {}).get("subject_poses") or {}
        end_poses = (shot.get("end_staging") or {}).get("subject_poses") or {}
        for cid, sp_txt in start_poses.items():
            ep_txt = end_poses.get(cid, "")
            if not sp_txt or not ep_txt:
                continue
            sp_l, ep_l = str(sp_txt).lower(), str(ep_txt).lower()
            s_dir = "right" if re.search(r"\bfacing\s+(?:3/4\s+|sharply\s+)?right\b", sp_l) else (
                "left" if re.search(r"\bfacing\s+(?:3/4\s+|sharply\s+)?left\b", sp_l) else ""
            )
            e_dir = "right" if re.search(r"\bfacing\s+(?:3/4\s+|sharply\s+)?right\b", ep_l) else (
                "left" if re.search(r"\bfacing\s+(?:3/4\s+|sharply\s+)?left\b", ep_l) else ""
            )
            if s_dir and e_dir and s_dir != e_dir and not shot.get("allow_torso_turn"):
                add("warn", "FIRST_LAST_TORSO_FLIP",
                    f"Chủ thể {cid} đổi hướng mặt từ '{s_dir}' ở start_staging sang '{e_dir}' ở end_staging trong chế độ `first_last` "
                    "→ Veo 3.1 sẽ bị xoay/vặn thân phi vật lý ở giữa clip. Giữ cùng hướng trục thân hoặc cắt sang shot mới.")

    cam_lens_txt = (shot.get("camera") or shot.get("camera_shot") or "").lower()
    act_full_txt = f"{shot.get('action', '')} {shot.get('end_action', '')}".lower()
    if (
        re.search(r"\b(14mm|16mm|18mm|20mm|24mm|28mm|wide\s+shot|extreme\s+wide)\b", cam_lens_txt)
        and re.search(
            r"\b(jaws?\s+clamp(?:ed|s|ing)?|clamp(?:ed|s|ing)?\s+(?:its|his|her|the)?\s*jaws?|neck\s+clamp|teeth\s+sink(?:ing|s)?|bite(?:s|ing)?\s+deep)\b",
            act_full_txt,
        )
    ):
        add("info", "BITE_IMPACT_WIDE_LENS",
            "Cảnh mô tả cú cắn/ngoạm sâu vào da thịt nhưng đang dùng ống kính góc rộng (24mm–28mm / Wide) "
            "→ vùng răng tiếp xúc quá nhỏ (<5% khung hình) dễ gây cảm giác 'trượt bề mặt'. Nên dùng 50mm–85mm Close-Up để thấy rõ răng cắm ngập vào cơ cổ.")
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
    causal = (shot.get("causal_link") or "").strip()
    if causal and re.match(r"^(and\s+then|và\s+rồi|sau\s+đó)\b", causal, flags=re.I):
        add("warn", "WEAK_CAUSAL_CONNECTOR",
            f"Trường `causal_link` đang mở đầu bằng '{causal[:20]}...' (liệt kê tuyến tính). "
            "Theo chuẩn Đạo diễn Top 0.1%, hãy bắt đầu bằng 'THEREFORE:' (Vì vậy — hệ quả tất yếu) hoặc 'BUT:' (Nhưng — bước ngoặt cản trở).")
    return out


_GROUNDED_POSTURE_RE = re.compile(
    r"\b(pinned|knocked\s+down|collapsed|prone|on\s+(?:its|his|her)\s+(?:right\s+|left\s+)?(?:flank|side|back)|"
    r"slammed\s+(?:onto|into)\s+the\s+(?:mud|ground|floor|earth)|flat\s+on\s+the\s+(?:ground|mud))\b",
    re.I,
)
_UPRIGHT_START_RE = re.compile(
    r"\b(standing\s+tall|charging\s+forward\s+from\s+a\s+standing|pacing\s+upright|circling\s+each\s+other\s+upright|"
    r"standing\s+upright|towering\s+upright)\b",
    re.I,
)
_RECOVERY_BRIDGE_RE = re.compile(
    r"\b(rising|push(?:es|ing)\s+up|kip[- ]?up|struggl(?:es|ing)\s+(?:up|to\s+rise)|from\s+prone|from\s+the\s+mud|"
    r"pinned|on\s+(?:its|his|her)\s+(?:right\s+|left\s+)?(?:flank|side)|grounded|kick(?:s|ing)\s+free|thrash(?:es|ing)|"
    r"regain(?:s|ing)\s+footing|scramble(?:s|ing)\s+up)\b",
    re.I,
)


def _detect_fsm_posture_discontinuity(prev: dict, cur: dict, chars: dict) -> str:
    """Phát hiện lỗi đứt gãy trạng thái vật lý (State Amnesia) giữa cuối shot trước và đầu shot sau."""
    if cur.get("allow_posture_jump"):
        return ""
    raw_prev_end = prev.get("end_staging")
    raw_cur_start = cur.get("start_staging")
    prev_end_poses = (raw_prev_end.get("subject_poses") if isinstance(raw_prev_end, dict) else None) or {}
    cur_start_poses = (raw_cur_start.get("subject_poses") if isinstance(raw_cur_start, dict) else None) or {}
    common_cids = [c for c in (prev.get("subjects") or []) if c in (cur.get("subjects") or []) and c in chars]
    for cid in common_cids:
        c_name = display_name(chars.get(cid, {}), cid)
        p_txt = str(prev_end_poses.get(cid) or "")
        if not p_txt:
            raw_end = f"{prev.get('exit_state', '')} {prev.get('end_action', '')}"
            if c_name.lower() in raw_end.lower():
                p_txt = raw_end
        c_txt = str(cur_start_poses.get(cid) or "")
        if not c_txt:
            raw_start = f"{cur.get('entry_state', '')} {cur.get('start_action', '')} {cur.get('action', '')}"
            if c_name.lower() in raw_start.lower():
                c_txt = raw_start
        if p_txt and c_txt and _GROUNDED_POSTURE_RE.search(p_txt) and _UPRIGHT_START_RE.search(c_txt) and not _RECOVERY_BRIDGE_RE.search(c_txt):
            return (
                f"Đứt gãy trạng thái cơ học (FSM State Discontinuity) của {c_name} ({cid}) giữa {prev.get('shot_id')} và {cur.get('shot_id')}: "
                f"cuối {prev.get('shot_id')} nhân vật đang bị quật ngã/nằm dưới đất ('{p_txt[:80]}...'), nhưng đầu {cur.get('shot_id')} "
                f"lại đứng thẳng tấn công ngay ('{c_txt[:80]}...') mà thiếu pha chống chân đứng dậy hoặc phản đòn từ mặt đất."
            )
    return ""


_ZONE_DISPLACEMENT_BRIDGE_RE = re.compile(
    r"\b(push(?:es|ed|ing)?|shov(?:es|ed|ing)|hurl(?:s|ed|ing)?|throw(?:s|n|ing)?|flung|fling(?:s|ing)?|"
    r"chas(?:es|ed|ing)|pursu(?:es|ed|ing)|retreat(?:s|ed|ing)?|sprint(?:s|ed|ing)?|run(?:s|ning)?|"
    r"leap(?:s|ed|ing)?|jump(?:s|ed|ing)?|tumbl(?:es|ed|ing)|slid(?:es|ing)|drag(?:s|ged|ging)?|"
    r"crash(?:es|ed|ing)?\s+into|fall(?:s|ing)?\s+into|splash(?:es|ed|ing)?\s+into|"
    r"into\s+the\s+(?:sea|ocean|surf|water|swamp|marsh|mud)|down\s+the\s+(?:bank|slope|ridge)|"
    r"off\s+the\s+(?:bank|ledge|cliff|shore)|across\s+the\s+(?:shoreline|boundary|bank))\b",
    re.I,
)


def _detect_unbridged_arena_teleport(prev: dict, cur: dict) -> str:
    """Phát hiện lỗi nhảy cóc địa hình (Arena Teleportation) khi đổi vùng đấu trường mà thiếu cầu nối dịch chuyển vật lý."""
    if cur.get("allow_arena_cut"):
        return ""
    prev_zone = str(prev.get("arena_stage") or prev.get("environment") or "").strip()
    cur_zone = str(cur.get("arena_stage") or cur.get("environment") or "").strip()
    if not prev_zone or not cur_zone or prev_zone == cur_zone:
        return ""
    bridge_blob = " ".join(
        str(x or "")
        for x in (
            prev.get("action"),
            prev.get("end_action"),
            prev.get("exit_state"),
            cur.get("causal_link"),
            cur.get("entry_state"),
            cur.get("start_action"),
            cur.get("action"),
        )
    )
    if not _ZONE_DISPLACEMENT_BRIDGE_RE.search(bridge_blob):
        return (
            f"Chuyển đổi địa hình đột ngột (Unbridged Arena Teleport) giữa {prev.get('shot_id')} ('{prev_zone}') và "
            f"{cur.get('shot_id')} ('{cur_zone}') mà thiếu Cầu nối Dịch chuyển Vật lý (đẩy lùi, quăng xuống biển/đầm lầy, "
            "vừa chạy vừa đánh, hoặc nhảy theo truy kích). Hai vùng địa hình phải liền kề và chuyển tiếp bằng lực tác động vật lý!"
        )
    return ""


def lint_project(project: dict, cfg: dict) -> list:
    """Kiểm tra cấu trúc tổng thể của dự án (nhịp truyện beat, đầy đủ 1..N nhân vật được gọi tên, liên kết đạo cụ/bối cảnh)."""
    out = []

    def add(level, code, msg):
        out.append({"level": level, "code": code, "msg": msg})

    shots = [s for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    chars = mf.characters_by_id(project)

    # 0. Kiểm tra Ngân sách Shot Duy nhất theo Chuẩn Đạo diễn Top 0.1% (Cấm kéo giãn/lặp lại clip ít ỏi ở hậu kỳ)
    plan_obj = project.get("plan") or {}
    target_dur = float(plan_obj.get("target_duration_sec") or 0.0)
    avg_shot_plan = float(plan_obj.get("avg_edited_shot_sec") or 4.2)
    if target_dur >= 60.0 and shots and not project.get("allow_underbudgeted_shots"):
        expected_unique_shots = max(1, int(round(target_dur / max(2.5, avg_shot_plan))))
        min_acceptable_shots = max(1, int(expected_unique_shots * 0.72))
        if len(shots) < min_acceptable_shots:
            add("warn", "UNDERBUDGETED_SHOT_COUNT",
                f"Dự án đặt thời lượng mục tiêu {target_dur:.0f}s nhưng chỉ có {len(shots)} shot kịch bản "
                f"(chuẩn Đạo diễn Top 0.1% cần ~{expected_unique_shots} shot duy nhất với nhịp {avg_shot_plan:.1f}s/shot, tối thiểu {min_acceptable_shots} shot). "
                "Tuyệt đối không dùng ít clip rồi lặp lại/chia nhỏ ở hậu kỳ; hãy bổ sung đủ các Hồi (Acts), Hiệp giao tranh (Exchanges) và Shot chuyển tiếp mới.")

    if len(shots) >= 25:
        arenas = {str(s.get("arena_stage") or s.get("environment") or "").strip() for s in shots if s.get("arena_stage") or s.get("environment")}
        if len(arenas) <= 1:
            add("info", "STATIC_ARENA_FATIGUE",
                f"Dự án dài ({len(shots)} shots) nhưng toàn bộ diễn ra trong 1 bối cảnh/đấu trường duy nhất ({list(arenas)}). "
                "Theo chuẩn Đạo diễn Top 0.1%, cứ mỗi 12–15 shots (60s–75s) nên dịch chuyển sang tiểu đấu trường mới (`arena_stage` / `environment`) với địa hình và chướng ngại vật mới.")

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

    # 4. Kiểm tra Quy tắc Trục Điện Ảnh 180 Độ (180-Degree Axis) & Hướng Nhìn (Eyeline Match) giữa các shot liên tiếp cùng cảnh
    for prev, cur in zip(shots, shots[1:]):
        same_scene = (
            (prev.get("scene_id") and prev.get("scene_id") == cur.get("scene_id"))
            or prev.get("transition_to_next") == "INTRA_SCENE_CONTINUE"
            or bool(cur.get("chain_from_prev"))
        )
        if not same_scene:
            continue
        p_subjs = [c for c in (prev.get("subjects") or []) if c in chars][:2]
        c_subjs = [c for c in (cur.get("subjects") or []) if c in chars][:2]
        cam_pair = f"{prev.get('camera', '')} {cur.get('camera', '')}"
        has_bridge_cam = bool(re.search(r"\b(orbit|360|overhead|bird'?s[- ]eye|pov)\b", cam_pair, re.I))

        if (
            len(p_subjs) == 2
            and len(c_subjs) == 2
            and p_subjs[0] == c_subjs[1]
            and p_subjs[1] == c_subjs[0]
            and bool(prev.get("spatial_lock", True))
            and bool(cur.get("spatial_lock", True))
            and not cur.get("axis_cross_motivating_movement")
            and not cur.get("allow_axis_flip")
            and not has_bridge_cam
        ):
            add("warn", "AXIS_180_VIOLATION",
                f"Vi phạm quy tắc trục 180 độ giữa {prev['shot_id']} ({p_subjs[0]} trái / {p_subjs[1]} phải) và {cur['shot_id']} "
                f"({c_subjs[0]} trái / {c_subjs[1]} phải) trong cùng cảnh: đảo vị trí Trái/Phải đột ngột làm người xem mất phương hướng không gian. "
                f"Hãy giữ nguyên thứ tự `subjects: {p_subjs}` hoặc dùng máy quay `orbit` / đặt `axis_cross_motivating_movement: true`.")

        if len(p_subjs) == 1 and len(c_subjs) == 1 and p_subjs[0] != c_subjs[0] and not cur.get("allow_same_eyeline"):
            eye_a = infer_shot_eyeline(prev)
            eye_b = infer_shot_eyeline(cur)
            if eye_a and eye_b and eye_a == eye_b:
                add("warn", "EYELINE_MISMATCH",
                    f"Lệch hướng nhìn (Eyeline Mismatch) giữa 2 cảnh cận đối diện {prev['shot_id']} ({p_subjs[0]} nhìn sang {eye_a}) "
                    f"và {cur['shot_id']} ({c_subjs[0]} cũng nhìn sang {eye_b}): hai nhân vật đối thoại/đối đầu phải nhìn ngược hướng nhau "
                    "trên màn ảnh (người này nhìn phải thì người kia nhìn trái).")

        fsm_err = _detect_fsm_posture_discontinuity(prev, cur, chars)
        if fsm_err:
            add("warn", "FSM_POSTURE_DISCONTINUITY", fsm_err)

        teleport_err = _detect_unbridged_arena_teleport(prev, cur)
        if teleport_err:
            add("warn", "UNBRIDGED_ARENA_TELEPORT", teleport_err)
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


def build_director_choreography_blueprint(duration_sec: int, genre_key: str = "action_blockbuster", avg_shot_sec: float = 0.0) -> dict:
    """Sinh Kiến trúc Biên đạo & Kịch bản Đạo diễn theo Chuẩn Top 0.1% Thế giới.

    Hỗ trợ cả 2 chế độ:
    1. Chế độ Thời lượng Cố định (`fixed_duration_blueprint`): Phân rã `duration_sec` thành Số Hồi (`Acts`),
       Số Đấu trường (`Arenas`), Số Hiệp giao tranh (`Exchanges`), Tế bào 4-5 Shot (`Action-Reaction Cell`) và
       Số Shot Duy nhất Bắt buộc (`1 Shot = 1 Biến cố Vi mô Mới`, cấm lặp clip ở hậu kỳ).
    2. Chế độ Đạo diễn Tự Định cỡ (`autonomous_runtime_tiers`): Đề xuất 4 Gói Thời lượng Chuẩn từ 60s đến 60 phút.
    """
    import math

    gprof = GENRE_PROFILES.get(genre_key) or GENRE_PROFILES["action_blockbuster"]
    asl = float(avg_shot_sec or gprof.get("avg_shot_sec") or 4.0)
    dur = max(15, int(duration_sec or 60))
    unique_shots = max(4, math.ceil(dur / asl))
    act_count = 3 if dur <= 180 else (5 if dur <= 900 else 8)
    arenas_count = max(1, math.ceil(dur / 60.0)) if dur <= 600 else max(8, math.ceil(dur / 120.0))
    exchanges_count = max(2, round(dur / 20.0))
    reversals_count = max(1, act_count)

    act_sec = round(dur / act_count, 1)
    shots_per_act = max(1, round(unique_shots / act_count))
    act_archetypes_5 = [
        (
            "Act I — Dry Land Encounter, Probing & First Takedown (Đất liền Bìa rừng)",
            "ZONE_1_DRY_COASTAL_CLEARING",
            "Chạm mặt trên đất liền (hậu cảnh đã thấy đầm lầy & biển kế bên); gầm thăm dò, lao vào vật ngã, dùng vai đánh lùi nhau ra để đo sức",
            "L0_dry_dust_to_first_claw_scratches",
            "Bridge 1->2: Vasto bị sức nặng của Rex ép lùi, vừa đánh trả vừa rút chạy dọc triền dốc xuống Đầm lầy bùn ven bờ để hãm tốc độ Rex; Rex lao theo truy kích",
        ),
        (
            "Act II — Muddy Marsh Skirmish & Traction Loss (Đầm lầy Bùn ven bờ)",
            "ZONE_2_COASTAL_MUDDY_MARSH",
            "Chân Rex lún bùn sâu 40cm mất tốc độ xoay trở; Vasto linh hoạt lách sườn cào rách vai Rex (Reversal 1: 30/70)",
            "L1_heavy_mud_splattered_bleeding_shoulder",
            "Bridge 2->3: Rex khóa chặt hàm vào cổ Vasto, dùng hai chân sau đẩy lùi Vasto trượt băng qua rặng cây ngập mặn văng ra Bãi cát & Ghềnh đá sát mép biển",
        ),
        (
            "Act III — Rocky Shoreline Grapple & Hurl Into the Sea (Bờ biển & Quăng xuống Biển)",
            "ZONE_3_ROCKY_SHORELINE_EDGE",
            "Quần thảo trên bờ cát & đá tảng sát sóng; Rex quật ngã Vasto rồi quăng Vasto văng qua bờ đá rơi ầm xuống biển (Reversal 2: 75/25)",
            "L2_mud_and_wet_sand_bruised_hide",
            "Bridge 3->4 (3-Shot Physical Bridge): [1] Rex quăng Vasto rơi xuống vùng nước biển ngập ngực -> [2] Vasto đạp đáy biển đứng bật dậy giữa sóng vỗ -> [3] Rex từ bờ đất phóng nhảy thẳng xuống biển ngay chỗ Vasto đứng để đánh tiếp!",
        ),
        (
            "Act IV — Chest-Deep Breaking Sea Surf Battle (Thủy chiến giữa Sóng biển)",
            "ZONE_4_CHEST_DEEP_SEA_SURF",
            "Đánh nhau trong nước biển ngập ngực (lực cản nước lớn, sóng xô lệch trụ); Vasto đè đầu Rex xuống nước biển định dìm ngạt thở -> Rex đạp đáy biển húc ngược đỉnh sọ từ dưới nước lên (Reversal 3)",
            "L3_sea_soaked_foaming_blood_heavy_panting",
            "Bridge 4->5: Cả hai vừa cắn xé vừa vật nhau dạt lên Mỏm đá gành nhô ra vùng biển sâu ngay sát bên",
        ),
        (
            "Act V — Coastal Reef Spit Finisher & Apex Sovereignty (Mỏm đá Gành biển & Kết liễu)",
            "ZONE_5_COASTAL_REEF_SPIT",
            "Kiệt sức trên mỏm đá ướt; Rex khóa hàm vào gáy Vasto, mượn đà lao + độ dốc mỏm đá quật Vasto rơi xuống biển sâu buộc đối thủ tháo chạy, rồi đứng trên gành đá gầm vang chiến thắng",
            "L4_exhausted_sea_drenched_battle_scarred_victor",
            "Aftermath: Kẻ thua cuộc chìm xuống sóng biển sâu rút lui; kẻ thắng đứng sừng sững trên mỏm đá gành giữa sóng vỗ",
        ),
    ]
    acts_breakdown = []
    for idx in range(act_count):
        t0 = round(idx * act_sec)
        t1 = dur if idx == act_count - 1 else round((idx + 1) * act_sec)
        arch = act_archetypes_5[min(idx, len(act_archetypes_5) - 1)]
        acts_breakdown.append({
            "act_number": idx + 1,
            "time_window_sec": f"{t0}s-{t1}s",
            "title": arch[0],
            "arena_stage": arch[1],
            "dramatic_goal_and_reversal": arch[2],
            "progressive_damage_state": arch[3],
            "zone_transition_bridge": arch[4],
            "exchanges_in_act": max(1, round((t1 - t0) / 20.0)),
            "unique_shots_in_act": shots_per_act if idx < act_count - 1 else max(1, unique_shots - shots_per_act * (act_count - 1)),
        })

    return {
        "standard": "WORLD_CLASS_0_1_PERCENT_DIRECTOR_STANDARD",
        "zero_clip_reuse_policy": True,
        "contiguous_map_topology_policy": "5 vùng địa hình phải nằm liền kề nhau trên cùng 1 bản đồ sinh thái (Đất liền <-> Đầm lầy <-> Bờ biển <-> Dưới biển); chuyển vùng bắt buộc bằng lực đẩy/quăng/chạy truy kích vật lý.",
        "grounded_plausibility_laws": [
            "1. Bảo toàn Khối lượng & Đòn bẩy (Mass & Leverage): Muốn quăng đối thủ xuống biển phải khóa cổ + dùng đà lao + độ dốc bờ đất; cơ sinh học thay đổi theo địa hình (đất cứng -> bùn lún -> nước biển cản lực).",
            "2. Tâm lý Thực chiến (Combat Psychology): Thăm dò (Probe) -> Vật ngã (Takedown) -> Đánh lùi giữ khoảng cách (Push-back) -> Vừa chạy vừa đánh (Mobile Skirmish) -> Nhảy theo truy kích (Pursuit Leap).",
            "3. Hợp thức hóa Siêu nhiên/Sci-Fi (Rationalized Sci-Fi/Supernatural): Nếu có năng lượng/tia nhiệt/phép thuật, bắt buộc có (a) Dấu hiệu nạp sinh học, (b) Phản lực Newton lún chân + tương tác nhiệt thật với nước/đất, (c) Tiêu hao thể lực sau chiêu.",
        ],
        "fsm_state_continuity_equation": "Shot[k-1].exit_state == Shot[k].entry_state",
        "fixed_duration_blueprint": {
            "target_duration_sec": dur,
            "genre": genre_key,
            "avg_edited_shot_sec": asl,
            "unique_shots_required": unique_shots,
            "acts_count": act_count,
            "distinct_arenas_required": arenas_count,
            "tactical_exchanges_count": exchanges_count,
            "major_reversals_required": reversals_count,
            "action_reaction_cell_grammar": [
                "Shot 1 (Telegraph / Setup ~4.0s): Lấy đà, dồn trọng lượng, khóa ánh nhìn",
                "Shot 2 (Primary Collision ~4.0s): Va chạm toàn thân theo chiều sâu Z-axis",
                "Shot 3 (Visceral Macro Insert ~3.0s): 85mm-100mm cận cảnh răng/móng/vũ khí ép lún da thịt (>35% khung hình)",
                "Shot 4 (Asymmetric Consequence ~4.5s): Hất văng/quật ngã làm thay đổi tư thế (standing -> prone/pinned)",
                "Shot 5 (Tactical Recovery / Pivot ~4.5s): Dùng địa hình hoặc đòn hiểm thoát vây, khóa exit_state cho hiệp sau",
            ],
            "acts_breakdown": acts_breakdown,
        },
        "autonomous_runtime_tiers": {
            "tier_1_short_teaser": {"duration_sec": 90, "unique_shots": math.ceil(90 / asl), "arenas": 2, "scope": "1 Cao trào duy nhất (TikTok/Reels/Shorts)"},
            "tier_2_theatrical_setpiece": {"duration_sec": 300, "unique_shots": math.ceil(300 / asl), "arenas": 5, "scope": "Đại chiến 5 Hồi - 5 Đấu trường hoàn chỉnh (Chuẩn IMAX / YouTube 5 phút)"},
            "tier_3_extended_short_film": {"duration_sec": 900, "unique_shots": math.ceil(900 / asl), "arenas": 8, "scope": "Phim ngắn 15 phút (3 Chương: Rình mò -> Đụng độ & Rút lui đêm bão -> Quyết chiến vực thác)"},
            "tier_4_feature_anthology": {"duration_sec": 3600, "unique_shots": math.ceil(3600 / asl), "arenas": 24, "scope": "Phim Điện ảnh 60 phút (8 Sequences, A-Plot + B-Plot, 3 đại cảnh chiến đấu)"},
        },
    }
