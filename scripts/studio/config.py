"""Cấu hình tập trung. Mọi giá trị phụ thuộc máy/tài khoản/model nằm ở `studio_config.json` (gốc repo)."""

import copy
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT_DIR / "projects"
CONFIG_PATH = ROOT_DIR / "studio_config.json"

DEFAULT_CONFIG = {
    "browser": {
        "chrome_exe": "",
        "profile_dir": "~/chrome_ai_bot",
        "debug_port": 9222,
        "flow_url": "https://labs.google/fx/tools/flow",
    },
    "models": {
        # Nhãn và đơn giá credit thay đổi theo thời gian — cập nhật trong studio_config.json.
        "video": {
            "quality": {"label": "Omni 1.1 Flash", "credits": 12},
            "fast": {"label": "Omni 1.1 Flash", "credits": 12},
        },
        "image": {"pro": "Nano Banana Pro", "standard": "Nano Banana 2"},
        # Model ID của Gemini API (khác tên gói/tên thương mại). Kiểm tra bằng `list-models`.
        "gemini_vision_qa": "gemini-4-argon",
        # Dự phòng khi model chính không có hạn mức (bậc miễn phí: argon/pro = 0) hoặc quá tải.
        "gemini_vision_qa_fallbacks": ["gemini-3.5-flash", "gemini-3.8-flash"],
        "gemini_tts": "gemini-3.8-flash-tts",
        "gemini_transcribe": "gemini-3.5-transcribe",
    },
    # Ai chấm QA thị giác: auto | agent | api | manual (ghi đè bằng biến STUDIO_REVIEWER hoặc --reviewer)
    "reviewer": {"mode": "auto"},
    "credits": {"budget": 25000, "takes_per_shot": 2, "quality_threshold": 4, "max_retakes_per_shot": 2},
    "tts": {"voice": "Charon", "sample_rate": 24000},
    "output": {
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "crf": 18,
        "audio_bitrate": "192k",
        "loudness_lufs": -14.0,
        "true_peak_db": -1.5,
    },
    "audio_mix": {
        "production_gain_db_with_vo": -8.0,
        "music_gain_db": -16.0,
        "duck_music_under_vo": True,
    },
    "editorial": {
        "default_transition": "cut",
        "dissolve_sec": 0.5,
        "vo_pre_roll_sec": 0.3,
        "vo_post_roll_sec": 0.6,
        "vo_max_sec": 7.0,           # lời dẫn tối đa cho 1 clip 8s (sau khi siết nhịp)
        "vo_max_beat_sec": 30.0,     # lời của beat (nhiều shot): chỉ rút khoảng lặng, không ép tốc độ
        "vo_max_pause_sec": 0.3,
        "vo_max_tempo": 1.25,
        "speech_pad_head_sec": 0.25,
        "speech_pad_tail_sec": 0.45,
        "min_shot_sec": 1.5,
        "preferred_shot_sec": 4.5,   # auto-select: độ dài cắt ưa thích khi shot không có lời dẫn
        "min_beat_shot_sec": 2.0,    # shot trong beat không ngắn hơn mức này
        "seam_max_l1": 9.5,
        "start_fade_sec": 0.8,       # mở chương từ đen (hình + tiếng)
        "end_fade_sec": 1.5,         # kết chương về đen
    },
    "qa": {
        "letterbox_luma": 20,
        "letterbox_min_ratio": 0.05,
        "freeze_sec": 1.5,
        "freeze_pixel_diff": 4,
        "freeze_changed_ratio": 0.001,
        "black_luma": 8,
        "silence_dbfs": -50.0,
        "min_duration_sec": 4.0,
        "first_frame_min_corr": 0.8,   # clip tạo từ frame mở đầu phải khớp frame đó (chống tải nhầm hàng)
    },
    "prompt": {"min_chars": 150, "warn_chars": 750, "max_chars": 1000, "max_timecoded_phases": 2},
    "subtitles": {
        "max_chars_per_line": 42,
        "max_chars_per_line_vertical": 22,
        "font": "Arial",
        "font_size": 20,
        "font_size_vertical": 11,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_dotenv(path: Path = ROOT_DIR / ".env") -> None:
    """Nạp biến từ file .env (vd. GEMINI_API_KEY) nếu chưa có trong môi trường. File .env đã bị gitignore."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: Path = CONFIG_PATH) -> dict:
    load_dotenv()
    if path.exists():
        user_cfg = json.loads(path.read_text(encoding="utf-8"))
        user_cfg.pop("_comment", None)
        return _deep_merge(DEFAULT_CONFIG, user_cfg)
    return copy.deepcopy(DEFAULT_CONFIG)
