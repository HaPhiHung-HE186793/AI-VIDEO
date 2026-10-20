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


def is_structured(shot: dict) -> bool:
    return bool(shot.get("action") and (shot.get("camera") or shot.get("camera_shot")))


def build_prompt(project: dict, shot: dict) -> str:
    """Ghép prompt Veo từ các trường có cấu trúc của shot."""
    chars = mf.characters_by_id(project)
    envs = mf.environments_by_id(project)
    lang = normalize_lang(project.get("language") or project.get("plan", {}).get("language_code", "vi"))

    parts = [_sentence(shot.get("camera") or shot.get("camera_shot"))]

    subject_lines = []
    for cid in shot.get("subjects", []):
        c = chars.get(cid, {})
        if c.get("identity_line"):
            subject_lines.append(_sentence(f"{display_name(c, cid)} is {c['identity_line'].rstrip('.')}"))
    parts += subject_lines

    parts.append(_sentence(shot.get("action")))

    setting = shot.get("setting")
    if not setting and shot.get("environment") in envs:
        setting = envs[shot["environment"]].get("identity_line") or envs[shot["environment"]].get("name")
    parts.append(_sentence(", ".join(x for x in [setting, shot.get("lighting")] if x)))
    parts.append(_sentence(project.get("style_line") or project.get("visual_style")))

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


def effective_negative_prompt(project: dict, shot: dict) -> str:
    items = [project.get("negative_prompt", ""), shot.get("negative_prompt", "")]
    return ", ".join(x.strip(" ,") for x in items if x and x.strip(" ,"))


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
    n = len(prompt)
    if n > pcfg["max_chars"]:
        add("warn", "PROMPT_TOO_LONG", f"{n} ký tự > {pcfg['max_chars']}. Prompt dài làm model bỏ qua chi tiết; giữ 1–2 hành động chính.")
    elif n > pcfg["warn_chars"]:
        add("info", "PROMPT_LONG", f"{n} ký tự — cân nhắc rút gọn (mục tiêu 400–{pcfg['warn_chars']}).")
    elif n < pcfg["min_chars"]:
        add("warn", "PROMPT_TOO_SHORT", f"{n} ký tự — thiếu máy quay/ánh sáng/âm thanh.")

    junk = sorted({m.group(0) for m in JUNK_TOKENS.finditer(prompt)})
    if junk:
        add("warn", "JUNK_TOKENS", f"Token vô nghĩa với Veo: {', '.join(junk)}.")
    negs = [m.group(0) for m in NEGATION.finditer(prompt)]
    if len(negs) >= 3:
        add("warn", "TOO_MANY_NEGATIONS", f"{len(negs)} cụm phủ định ({', '.join(negs[:5])}…). Chuyển sang negative_prompt và mô tả điều MUỐN thấy.")
    phases = TIMECODE.findall(prompt)
    if len(phases) > pcfg["max_timecoded_phases"]:
        add("warn", "TOO_MANY_PHASES", f"{len(phases)} pha có mốc giờ. Veo không bám mốc giờ chính xác; 1 clip nên có 1–2 hành động.")

    subjects = shot.get("subjects", [])
    for cid in subjects:
        c = chars.get(cid)
        if not c:
            add("error", "UNKNOWN_SUBJECT", f"Subject '{cid}' không có trong characters.")
            continue
        if not c.get("identity_line"):
            add("warn", "NO_IDENTITY_LINE", f"{cid} chưa có identity_line (mô tả chuẩn dán nguyên văn mọi shot).")
        elif c["identity_line"].strip().rstrip(".") not in prompt:
            add("warn", "IDENTITY_LINE_DRIFT", f"Prompt không chứa nguyên văn identity_line của {cid} → mô tả trôi giữa các shot.")
        if mode in ("text",) or (mode == "ingredients" and not (shot.get("reference_images") or c.get("reference_images"))):
            add("warn", "NO_IDENTITY_REFERENCE", f"{cid} xuất hiện nhưng shot không dùng ảnh tham chiếu (mode={mode}). Danh tính sẽ trôi giữa các clip.")

    if mode in ("first_frame", "first_last") and not shot.get("first_frame_path"):
        add("error", "MISSING_FIRST_FRAME", f"mode={mode} nhưng chưa có first_frame_path.")
    if mode == "first_last":
        if not shot.get("last_frame_path"):
            add("error", "MISSING_LAST_FRAME", "mode=first_last nhưng chưa có last_frame_path.")
        add("info", "FIRST_LAST_FRAMING", "First/Last frame phải cùng cỡ cảnh, góc máy, ánh sáng — khác nhau sẽ gây biến hình.")
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
    if len(subjects) >= 2 and mode == "ingredients":
        add("info", "MULTI_SUBJECT_COMPOSITION", f"Cảnh có {len(subjects)} nhân vật dùng mode=ingredients: nếu cần kiểm soát "
                                                 "chặt vị trí trái/phải (quy tắc 180°) và hướng nhìn, nên dựng first_frame trước.")
    return out


def lint_project(project: dict, cfg: dict) -> list:
    """Kiểm tra cấu trúc tổng thể của dự án (nhịp truyện beat, liên kết đạo cụ/bối cảnh)."""
    out = []

    def add(level, code, msg):
        out.append({"level": level, "code": code, "msg": msg})

    shots = [s for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    if len(shots) >= 6 and project.get("audio_strategy") == "voiceover_external" and not project.get("beats"):
        add("warn", "NO_BEATS_DEFINED",
            f"Dự án có {len(shots)} shot dùng voiceover_external nhưng chưa định nghĩa `beats` — lời dẫn sẽ bị "
            "đóng khung theo từng shot (không có L-cut/J-cut trải qua nhiều góc máy).")

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
    return out


def complexity_score(shot: dict, index: int, total: int) -> tuple:
    text = " ".join(str(shot.get(k) or "") for k in ("action", "camera", "camera_shot"))
    if not shot.get("action"):
        text += " " + re.split(r"saying[^:]*:|says[^:]*:", shot.get("veo_prompt") or "", flags=re.I)[0]
    score, reasons = 1, []
    if INTERACTION_WORDS.search(text):
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
    return min(10, score), reasons or ["cảnh đơn giản"]


def route_model(score: int, cfg: dict) -> dict:
    tier = "quality" if score >= cfg["credits"]["quality_threshold"] else "fast"
    m = cfg["models"]["video"][tier]
    return {"tier": tier, "label": m["label"], "credits": m["credits"]}
