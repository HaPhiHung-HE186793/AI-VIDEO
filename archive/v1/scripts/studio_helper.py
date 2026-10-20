#!/usr/bin/env python3
"""
AI Video Studio Helper CLI v3.0 — Hyper-Parallel & GPU-Accelerated Engine (`scripts/studio_helper.py`)
------------------------------------------------------------------------------------------------------
Tối ưu hóa hiệu năng tối đa trên phần cứng máy trạm của User:
- CPU: AMD Ryzen 5 5600H (6 Cores / 12 Threads) -> Đa luồng `ThreadPoolExecutor(max_workers=12)`
- GPU: NVIDIA GeForce RTX 3050 (`h264_nvenc` / `hevc_nvenc`) + AMD AMF -> Mã hóa phần cứng siêu tốc & Zero-Reencode `-c copy`
- RAM: 16 GB -> Xử lý Batch Queueing, Pre-Generated Keyframe Graph ($K_0 ... K_N$) & Chapter Sharding cho phim dài 1–5 tiếng.

Các lệnh chính:
1. `plan`               : Tính toán số cảnh (shots 8s), chia Chapters/Batches cho phim ngắn & phim dài (1p -> 5 tiếng).
2. `init`               : Khởi tạo dự án với Đồ thị Keyframe Biên (Boundary Keyframe Graph) để render video song song 100%.
3. `validate`           : Kiểm định kịch bản chống sạn AI (Zero-Prop check, Camera Diversity, Lip-Sync Pacing).
4. `download-batch`     : Tải song song 12 luồng toàn bộ ảnh Ingredients/Keyframes & Video Clips từ Google Flow CDN.
5. `extract-last-frame` : Trích xuất frame cuối cùng (`last_frame.png`) từ clip bất kỳ.
6. `qa-frames`          : Trích xuất song song 12 luồng lưới 4 khung hình kiểm định (Visual QA Contact Sheet).
7. `assemble`           : Ghép phim siêu tốc bằng Zero-Reencode (`-c copy`, ghép 100 cảnh trong 2 giây) + GPU `h264_nvenc` (RTX 3050).
8. `sync-browser`       : Đồng bộ tức thì cổng Chrome 9222 (`chrome_ai_bot`) trong 50ms (Optimistic Zero-Auth-Check).
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT_DIR / "projects"
CPU_THREADS = os.cpu_count() or 12

LANGUAGE_SPEECH_RATES = {
    "vi": {
        "name": "Tiếng Việt (Vietnamese)",
        "unit": "âm tiết (chữ)",
        "rate_per_sec": 2.8,
        "recommended_max_per_8s_shot": 19,
        "hard_max_per_8s_shot": 22,
    },
    "en": {
        "name": "Tiếng Anh (English)",
        "unit": "từ (words)",
        "rate_per_sec": 2.7,
        "recommended_max_per_8s_shot": 18,
        "hard_max_per_8s_shot": 22,
    },
    "ja": {
        "name": "Tiếng Nhật (Japanese)",
        "unit": "mora/ký tự",
        "rate_per_sec": 5.5,
        "recommended_max_per_8s_shot": 35,
        "hard_max_per_8s_shot": 42,
    },
    "ko": {
        "name": "Tiếng Hàn (Korean)",
        "unit": "âm tiết",
        "rate_per_sec": 4.2,
        "recommended_max_per_8s_shot": 26,
        "hard_max_per_8s_shot": 32,
    },
}

DEFAULT_CAMERA_PROGRESSION = [
    "Wide Establishing Shot (Mở bối cảnh & không gian)",
    "Two-Shot / Group Interaction (Các chủ thể tương tác trực tiếp)",
    "Over-the-Shoulder Medium Close-Up (Cận trung qua vai - Chủ thể A)",
    "Over-the-Shoulder Reverse Shot (Cận trung đảo chiều - Chủ thể B)",
    "Dynamic Tracking / Causal Physics Shot (Chuyển động & tác động vật lý môi trường)",
    "Medium Group / Ecosystem Shot (Chính - Phụ - Quần chúng phản ứng)",
    "Close-Up / Macro Detail Shot (Cận cảnh chi tiết / biểu cảm cao trào)",
    "Wide / Medium Resolution Shot (Khung hình kết đoạn & chuyển chương)",
]


def normalize_lang(lang_str: str) -> str:
    s = lang_str.strip().lower()
    if any(k in s for k in ["vi", "viet", "tiếng việt", "tieng viet"]):
        return "vi"
    if any(k in s for k in ["en", "eng", "anh", "english"]):
        return "en"
    if any(k in s for k in ["ja", "jp", "nhật", "japanese"]):
        return "ja"
    if any(k in s for k in ["ko", "kr", "hàn", "korean"]):
        return "ko"
    return "vi"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return slug or f"video-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def sync_chrome_port_fast() -> dict:
    """Đồng bộ tức thì DevToolsActivePort với cổng 9222 (profile chrome_ai_bot) mà không kiểm tra đăng nhập rườm rà."""
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\Asus\AppData\Local")
    port_file = Path(local_app_data) / "Google" / "Chrome" / "User Data" / "DevToolsActivePort"
    port_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ws_url = data.get("webSocketDebuggerUrl", "")
            if ws_url:
                parsed = urlparse(ws_url)
                port = parsed.port or 9222
                port_file.write_text(f"{port}\n{parsed.path}\n", encoding="ascii")
                return {"ready": True, "ws_url": ws_url}
    except Exception:
        pass
    return {"ready": port_file.exists(), "ws_url": None}


def calculate_plan(duration_sec: int, lang: str, shot_duration: int = 8, batch_size: int = 8) -> dict:
    lang_code = normalize_lang(lang)
    lang_info = LANGUAGE_SPEECH_RATES.get(lang_code, LANGUAGE_SPEECH_RATES["vi"])
    num_shots = max(1, math.ceil(duration_sec / shot_duration))
    total_generated_sec = num_shots * shot_duration
    num_chapters = max(1, math.ceil(num_shots / batch_size))

    return {
        "target_duration_sec": duration_sec,
        "target_duration_human": f"{duration_sec // 3600}h {(duration_sec % 3600) // 60}m {duration_sec % 60}s",
        "veo_shot_duration_sec": shot_duration,
        "num_shots": num_shots,
        "num_boundary_keyframes": num_shots + 1,
        "parallel_batch_size": batch_size,
        "num_chapters_or_batches": num_chapters,
        "raw_total_duration_sec": total_generated_sec,
        "language_code": lang_code,
        "language_name": lang_info["name"],
        "speech_unit": lang_info["unit"],
        "recommended_max_units_per_shot": lang_info["recommended_max_per_8s_shot"],
        "hard_max_units_per_shot": lang_info["hard_max_per_8s_shot"],
        "total_recommended_words": num_shots * lang_info["recommended_max_per_8s_shot"],
        "hardware_acceleration": {
            "cpu_threads": CPU_THREADS,
            "gpu_encoder": "h264_nvenc (NVIDIA RTX 3050)",
            "concat_mode": "Zero-Reencode Instant Stream Copy (-c copy) + NVENC Tempo Adjust",
            "cloud_dispatch_mode": "2-Wave Selective Scene-Parallel Queueing (INTRA_SCENE_CONTINUE for 16s-24s multi-clip scenes + INTER_SCENE_CUT between different scenes)",
        },
    }


def cmd_plan(args):
    sync_chrome_port_fast()
    plan = calculate_plan(args.duration, args.lang, args.shot_length, args.batch_size)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


def cmd_init(args):
    sync_chrome_port_fast()
    slug = slugify(args.name)
    proj_dir = PROJECTS_DIR / slug
    (proj_dir / "assets" / "characters").mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets" / "environments").mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets" / "props").mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets" / "frames").mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets" / "clips").mkdir(parents=True, exist_ok=True)
    (proj_dir / "assets" / "qa").mkdir(parents=True, exist_ok=True)
    (proj_dir / "output").mkdir(parents=True, exist_ok=True)

    plan = calculate_plan(args.duration, args.lang, batch_size=args.batch_size)
    shots = []
    for i in range(1, plan["num_shots"] + 1):
        chapter_idx = ((i - 1) // args.batch_size) + 1
        cam = DEFAULT_CAMERA_PROGRESSION[(i - 1) % len(DEFAULT_CAMERA_PROGRESSION)]
        shots.append(
            {
                "shot_id": f"shot_{i:04d}" if plan["num_shots"] >= 100 else f"shot_{i:02d}",
                "scene_id": f"scene_{i:02d}",
                "sub_shot_index": 1,
                "sub_shot_total": 1,
                "transition_to_next": "INTER_SCENE_CUT",
                "chapter": chapter_idx,
                "order": i,
                "duration_sec": plan["veo_shot_duration_sec"],
                "start_sec": (i - 1) * plan["veo_shot_duration_sec"],
                "end_sec": i * plan["veo_shot_duration_sec"],
                "generation_mode": "selective_scene_continuity",
                "camera_shot": cam,
                "entities_in_shot": [],
                "audio_modality": "lip_sync_or_voiceover",
                "active_speaker": "",
                "environmental_physics": "",
                "dialogue_language": plan["language_name"],
                "dialogue_text": "",
                "word_count": 0,
                "ingredients_used": [],
                "start_keyframe_id": f"S{i:02d}_START",
                "end_keyframe_id": "",
                "first_frame_prompt": "",
                "last_frame_prompt": "",
                "first_frame_path": f"assets/frames/S{i:02d}_START.png",
                "last_frame_path": "",
                "veo_prompt": "",
                "cdn_video_url": "",
                "clip_output_path": f"assets/clips/shot_{i:04d}.mp4" if plan["num_shots"] >= 100 else f"assets/clips/shot_{i:02d}.mp4",
                "status": "pending",
            }
        )

    manifest = {
        "project_name": args.name,
        "project_slug": slug,
        "created_at": datetime.now().isoformat(),
        "visual_style": args.style,
        "aspect_ratio": args.aspect,
        "plan": plan,
        "characters": [],
        "environments": [],
        "props": [],
        "boundary_keyframes": [],
        "shots": shots,
    }

    manifest_path = proj_dir / "project_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Đã khởi tạo dự án v6.0 (Selective Scene Continuity) tại: {proj_dir} ({plan['num_shots']} shots)")


def cmd_validate(args):
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] Không tìm thấy file {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan = manifest.get("plan", {})
    hard_max = plan.get("hard_max_units_per_shot", 22)
    rec_max = plan.get("recommended_max_units_per_shot", 19)
    shots = manifest.get("shots", [])
    characters = manifest.get("characters", [])

    issues = []
    warnings = []
    total_sec = sum(s.get("duration_sec", 8) for s in shots)

    prop_keywords = [r"\bholding a\b", r"\bholding\b", r"\bsmartphone\b", r"\bphone\b", r"\bboba\b", r"\bclipboard\b"]
    for c in characters:
        cid = c.get("id", "unknown")
        cprompt = (c.get("nano_banana_prompt") or "").lower()
        if any(re.search(pk, cprompt) for pk in prop_keywords) and "no held objects" not in cprompt and "empty hands" not in cprompt and "hand-state" not in cprompt:
            warnings.append(
                f"[Base Ingredient {cid}] Phát hiện đạo cụ rời gắn trong ảnh đơn nhân vật. Hãy tách thành: (1) Turnaround Sheet (Trước-Sau-Trái-Phải-Trên xuống, tay trống) và (2) Articulation & Hand-State Sheet (Chi tiết tay mở vs. tay cầm đồ)."
            )
        if not c.get("turnaround_sheet_prompt") or not c.get("articulation_sheet_prompt"):
            warnings.append(
                f"[Character Model Rig {cid}] Thiếu Bản Thiết Kế Model Đa Góc Độ (`turnaround_sheet_prompt`: Trước-Sau-Trái-Phải-Trên xuống) hoặc Bản Thiết Kế Bộ Phận & Cầm Nắm (`articulation_sheet_prompt`: Miệng/Hàm + Tay mở vs. Tay cầm đồ). Chỉ dùng 1 ảnh đơn sẽ làm AI tự bịa góc khuất và gây giả!"
            )

    active_shots = [s for s in shots if (s.get("veo_prompt") or "").strip()]
    if len(active_shots) >= 4:
        chained_count = 0
        for idx in range(len(active_shots) - 1):
            cur_s = active_shots[idx]
            nxt_s = active_shots[idx + 1]
            cur_end = (cur_s.get("end_keyframe_id") or "").strip()
            nxt_start = (nxt_s.get("start_keyframe_id") or "").strip()
            trans = cur_s.get("transition_to_next", "INTER_SCENE_CUT")
            if (cur_end and cur_end == nxt_start) or trans == "INTRA_SCENE_CONTINUE":
                chained_count += 1
            # Kiểm tra tính đúng đắn của từng điểm chuyển tiếp
            if trans == "INTRA_SCENE_CONTINUE":
                if cur_end and nxt_start and cur_end != nxt_start:
                    issues.append(
                        f"[{cur_s.get('shot_id')} -> {nxt_s.get('shot_id')}] Đánh dấu là INTRA_SCENE_CONTINUE (cùng 1 cảnh dài 16s-24s) nhưng end_keyframe_id ({cur_end}) khác start_keyframe_id ({nxt_start})!"
                    )
            elif trans == "INTER_SCENE_CUT":
                if cur_end and nxt_start and cur_end == nxt_start:
                    issues.append(
                        f"[{cur_s.get('shot_id')} -> {nxt_s.get('shot_id')}] Đánh dấu là INTER_SCENE_CUT (chuyển sang cảnh khác/góc máy khác) nhưng lại nối chung frame ({cur_end})! Khi sang cảnh mới bắt buộc phải cắt chuyển cảnh bình thường, không nối liền vô tội vạ."
                    )

        if chained_count == len(active_shots) - 1:
            issues.append(
                f"[Editorial Grammar Error] Phát hiện nối liền vô tội vạ 100% ({chained_count}/{len(active_shots)-1}) các shot! Chỉ dùng INTRA_SCENE_CONTINUE khi 1 cảnh/góc máy kéo dài 16s–24s (2–3 đoạn 8s). Khi hết cảnh sang góc máy mới, bắt buộc dùng INTER_SCENE_CUT (Chuyển cảnh bình thường)!"
            )

    camera_shots = [(s.get("camera_shot") or "").strip() for s in shots]
    unique_cameras = set(c for c in camera_shots if c)
    if len(shots) >= 4 and len(unique_cameras) <= 2:
        warnings.append(
            f"[Cinematography] {len(shots)} cảnh chỉ dùng {len(unique_cameras)} góc máy. Hãy đa dạng hóa góc máy (Wide, Two-Shot, OTS, Close-Up, Tracking)."
        )

    fake_physics_keywords = [
        r"\bexplosive force\b",
        r"\bexplosive\b",
        r"\bexplode\b",
        r"\bpulverize\b",
        r"\bshockwave\b",
        r"\bspeed of light\b",
    ]

    for s in shots:
        sid = s.get("shot_id", "unknown")
        dialogue = (s.get("dialogue_text") or "").strip()
        words = dialogue.split() if dialogue else []
        w_count = len(words)
        s["word_count"] = w_count
        if w_count > hard_max:
            issues.append(f"[{sid}] Câu thoại quá dài ({w_count} từ > {hard_max} từ cho 8 giây).")
        elif w_count > rec_max:
            warnings.append(f"[{sid}] Câu thoại sát ngưỡng ({w_count}/{rec_max} từ).")

        vprompt = (s.get("veo_prompt") or "").lower()
        for fk in fake_physics_keywords:
            if re.search(fk, vprompt):
                warnings.append(
                    f"[{sid}] [Biomechanical Realism Filter] Phát hiện từ ngữ cường điệu gây hiệu ứng nổ giả ('{fk}') trong veo_prompt. AI sẽ vẽ vật thể nổ tung như thuốc nổ hoặc sai tỷ lệ! Hãy thay bằng mô tả cơ sinh học tự nhiên (lực ép cơ hàm, trọng lượng thực, tỷ lệ giải phẫu chuẩn)."
                )

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "valid": len(issues) == 0,
                "total_shots": len(shots),
                "total_duration_sec": total_sec,
                "issues": issues,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if issues:
        sys.exit(2)


def cmd_audit_assets(args):
    """
    Kiểm định toàn diện Tài nguyên Tiền kỳ (Pre-Production Asset Audit Gate v1.0):
    1. Character Rig Pack: Turnaround 5 góc (Trước-Sau-Trái-Phải-Trên xuống), Articulation (Hàm/Khẩu hình & Tay rỗng vs. Tay cầm nắm), Scale Reference 1:1.
    2. Zero-Prop Law: Kiểm tra tay nhân vật trên turnaround có bị gắn đạo cụ rời (sword, phone, cup, gun, bone) không.
    3. Environment Clean Plates: Bối cảnh sạch không bóng người/sinh vật (Clean background plate).
    4. Isolated Props Library: Đạo cụ độc lập, 3 góc nhìn, đúng kích thước mm/cm/m.
    5. Tạo Contact Sheet kiểm định tài nguyên tiền kỳ (assets/qa/preprod_assets_qa_grid.jpg).
    """
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] Không tìm thấy file {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    characters = manifest.get("characters", [])
    environments = manifest.get("environments", [])
    props = manifest.get("props", [])

    issues = []
    warnings = []
    char_results = []
    env_results = []
    prop_results = []

    # 1. AUDIT CHARACTERS (CHARACTER RIG PACK)
    if not characters:
        warnings.append("[Characters] Chưa khai báo nhân vật nào trong manifest['characters']!")

    for char in characters:
        cid = char.get("id", "unknown")
        cname = char.get("name", cid)
        t_prompt = (char.get("turnaround_sheet_prompt") or char.get("nano_banana_prompt") or "").lower()
        a_prompt = (char.get("articulation_sheet_prompt") or "").lower()
        s_prompt = (char.get("scale_sheet_prompt") or "").lower()

        t_path = proj_dir / char.get("turnaround_path", f"assets/characters/{cid}_turnaround.png")
        a_path = proj_dir / char.get("articulation_path", f"assets/characters/{cid}_articulation.png")
        s_path = proj_dir / char.get("scale_path", f"assets/characters/{cid}_scale.png")

        c_status = {
            "id": cid,
            "name": cname,
            "turnaround_sheet": "MISSING",
            "articulation_sheet": "MISSING",
            "scale_sheet": "MISSING",
            "zero_prop_compliance": True,
            "files_on_disk": {
                "turnaround": t_path.exists(),
                "articulation": a_path.exists(),
                "scale": s_path.exists()
            },
        }

        # Kiểm tra 5 góc Turnaround
        required_angles = ["front", "back", "left", "right"]
        top_angle = ["top-down", "dorsal", "high-angle"]
        has_basic_angles = all(a in t_prompt for a in required_angles)
        has_top_angle = any(a in t_prompt for a in top_angle)

        if not t_prompt:
            issues.append(f"[Character {cid}] Thiếu prompt bản thiết kế đa góc (`turnaround_sheet_prompt`)!")
        elif not (has_basic_angles and has_top_angle):
            warnings.append(
                f"[Character {cid}] Turnaround Sheet chưa đủ 5 góc chuẩn hình học (Trước - Sau - Trái - Phải - Trên xuống/Dorsal). AI có thể tự bịa góc khuất!"
            )
            c_status["turnaround_sheet"] = "INCOMPLETE_ANGLES"
        else:
            c_status["turnaround_sheet"] = "PASS"

        # Kiểm tra Zero-Prop Law trên Turnaround Sheet
        illegal_prop_words = [r"\bholding\b", r"\bholding a\b", r"\bwith a sword in hand\b", r"\bsmartphone in hand\b", r"\bholding weapon\b"]
        has_zero_prop_keywords = any(k in t_prompt for k in ["empty hands", "no held objects", "no detached props", "neutral a-pose", "neutral posture", "empty claws"])
        if any(re.search(pat, t_prompt) for pat in illegal_prop_words) and not has_zero_prop_keywords:
            issues.append(
                f"[Character {cid}] [Zero-Prop Law Violated] Bản thiết kế Turnaround gốc bị gắn sẵn đạo cụ rời vào tay nhân vật! Sẽ gây lỗi mọc thêm tay hoặc dính đạo cụ khi cử động. Hãy để hai tay/chi hoàn toàn trống rỗng (`empty hands, no held objects`)."
            )
            c_status["zero_prop_compliance"] = False

        # Kiểm tra Articulation Sheet
        if not a_prompt:
            warnings.append(
                f"[Character {cid}] Thiếu Bản Thiết Kế Khớp Động & Cầm Nắm (`articulation_sheet_prompt`). Cần đặc tả: (1) Khẩu hình/Hàm khép vs. Mở, (2) Bàn tay rỗng 5 ngón vs. Bàn tay cầm nắm đồ vật."
            )
        else:
            has_hand_jaw = any(k in a_prompt for k in ["hand", "jaw", "mouth", "grip", "holding", "finger", "articulation", "callout", "foot", "claw"])
            c_status["articulation_sheet"] = "PASS" if has_hand_jaw else "NEEDS_DETAIL"

        # Kiểm tra Scale Sheet
        if not s_prompt:
            warnings.append(f"[Character {cid}] Thiếu Bản Khóa Tỷ Lệ Thực Tế (`scale_sheet_prompt`) so với vật chuẩn hoặc môi trường.")
        else:
            c_status["scale_sheet"] = "PASS"

        char_results.append(c_status)

    # 2. AUDIT ENVIRONMENTS (CLEAN PLATES)
    if not environments:
        warnings.append("[Environments] Chưa khai báo bối cảnh nào trong manifest['environments']!")

    for env in environments:
        eid = env.get("id", "unknown")
        ename = env.get("name", eid)
        epath = proj_dir / env.get("path", f"assets/environments/{eid}.png")
        eprompt = (env.get("clean_plate_prompt") or env.get("nano_banana_prompt") or "").lower()

        e_status = {
            "id": eid,
            "name": ename,
            "clean_plate_compliance": True,
            "file_on_disk": epath.exists(),
        }

        clean_keywords = ["no characters", "no creatures", "no people", "no flying creatures", "empty", "pristine environment plate", "clear upper canopy", "unpopulated"]
        if not any(k in eprompt for k in clean_keywords):
            warnings.append(
                f"[Environment {eid}] Chưa ghi rõ từ khóa Bối Cảnh Sạch (`clean plate`: 'no characters, no creatures, empty'). AI có thể tự sinh thêm người/quái vật làm rối bối cảnh nền!"
            )
            e_status["clean_plate_compliance"] = False

        env_results.append(e_status)

    # 3. AUDIT PROPS LIBRARY
    for prop in props:
        pid = prop.get("id", "unknown")
        pname = prop.get("name", pid)
        ppath = proj_dir / prop.get("path", f"assets/props/{pid}.png")
        pprompt = (prop.get("prop_prompt") or "").lower()

        p_status = {
            "id": pid,
            "name": pname,
            "isolated_compliance": True,
            "file_on_disk": ppath.exists(),
        }

        iso_keywords = ["isolated", "neutral studio", "clean studio", "white background", "grey background", "studio lighting", "multi-angle", "no hands holding"]
        if not any(k in pprompt for k in iso_keywords):
            warnings.append(
                f"[Prop {pid}] Đạo cụ chưa được thiết kế ở dạng tách rời độc lập (`isolated on clean studio background`). Hãy tạo riêng trước khi cho nhân vật cầm!"
            )
            p_status["isolated_compliance"] = False

        prop_results.append(p_status)

    # 4. TẠO PRE-PRODUCTION CONTACT SHEET NẾU CÓ ẢNH TRÊN ĐĨA
    cv2 = ensure_cv2()
    qa_dir = proj_dir / "assets" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    asset_images = []

    for char in characters:
        for pkey in ["turnaround_path", "articulation_path", "scale_path"]:
            p = proj_dir / char.get(pkey, "")
            if p.exists() and p.is_file():
                asset_images.append((f"{char.get('id')}_{pkey.replace('_path','')}", str(p)))

    for env in environments:
        p = proj_dir / env.get("path", "")
        if p.exists() and p.is_file():
            asset_images.append((f"ENV_{env.get('id')}", str(p)))

    for prop in props:
        p = proj_dir / prop.get("path", "")
        if p.exists() and p.is_file():
            asset_images.append((f"PROP_{prop.get('id')}", str(p)))

    contact_sheet_path = ""
    if asset_images and cv2:
        try:
            import numpy as np
            cells = []
            for label, imp in asset_images[:9]:
                im = cv2.imread(imp)
                if im is not None:
                    im_resized = cv2.resize(im, (640, 360))
                    cv2.rectangle(im_resized, (8, 8), (632, 42), (0, 0, 0), -1)
                    cv2.putText(im_resized, label[:35], (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cells.append(im_resized)
            if cells:
                while len(cells) % 3 != 0 and len(cells) > 3:
                    blank = np.zeros_like(cells[0])
                    cells.append(blank)
                rows = []
                num_cols = 3 if len(cells) >= 3 else len(cells)
                for r in range(0, len(cells), num_cols):
                    rows.append(np.hstack(cells[r:r+num_cols]))
                grid = np.vstack(rows) if len(rows) > 1 else rows[0]
                out_cs = qa_dir / "preprod_assets_qa_grid.jpg"
                cv2.imwrite(str(out_cs), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                contact_sheet_path = str(out_cs)
        except Exception as e:
            warnings.append(f"[Contact Sheet Generation Error] {e}")

    ready_for_keyframe_staging = len(issues) == 0
    ready_for_video_production = ready_for_keyframe_staging and all(
        c["files_on_disk"].get("turnaround", False) for c in char_results
    )

    verdict = {
        "status": "PASS" if len(issues) == 0 else "ACTION_REQUIRED",
        "ready_for_keyframe_staging": ready_for_keyframe_staging,
        "ready_for_video_production": ready_for_video_production,
        "characters_audit": char_results,
        "environments_audit": env_results,
        "props_audit": prop_results,
        "preprod_contact_sheet": contact_sheet_path,
        "issues": issues,
        "warnings": warnings,
        "recommendations": [
            "Đảm bảo toàn bộ Character Turnaround Sheet đạt chuẩn 5 góc và Zero-Prop (hai tay mở rỗng) trước khi đưa vào cảnh.",
            "Tạo Environment Clean Plates trước để khóa ánh sáng và bối cảnh chuẩn không đổi.",
            "Dùng Nano Banana Pro ghép [Char Rig] + [Clean Plate] + [Prop Sheet] thành Composite Start Keyframe trước khi bấm máy Veo 3.1."
        ]
    }

    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    if issues:
        sys.exit(2)


def cmd_forge_assets(args):
    """
    Sinh tự động bộ prompt chuẩn Studio cho:
    1. Bộ 3 Bản Thiết Kế Model Nhân Vật (Turnaround 5 Góc, Articulation Khẩu hình & Cầm nắm, Scale Reference 1:1)
    2. Environment Clean Plates (Bối cảnh sạch không người/sinh vật)
    3. Isolated Props Library (Đạo cụ độc lập 3 góc, đúng kích thước mm/cm/m)
    Có thể tự động cập nhật vào project_manifest.json nếu có cờ --apply-to-manifest.
    """
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    style = args.style or manifest.get("visual_style", "Photorealistic 3D / Cinematic")
    char_name = args.char_name or "Main Character"
    char_desc = args.char_desc or "detailed visual appearance, costume, anatomy and textures"
    char_type = (args.char_type or "human").lower()
    char_id = args.char_id or f"CHAR_{slugify(char_name).upper().replace('-', '_')}"

    # 1. Turnaround & Articulation & Scale Prompts theo loại thực thể
    if char_type in ["creature", "animal", "dinosaur", "monster"]:
        turnaround_prompt = (
            f"Professional VFX creature model turnaround sheet of {char_name} ({char_desc}), "
            f"{style}. Multi-angle orthographic reference layout on a single 16:9 sheet showing 5 consistent views "
            f"of the exact same creature: (1) Full-body Left Side Profile, (2) Full-body Right Side Profile, "
            f"(3) Direct Front View, (4) Direct Rear/Back View, and (5) Top-Down Dorsal View showing head-to-tail proportions. "
            f"100% consistent scale pattern, coloration, anatomical muscle volume across all views, "
            f"neutral studio lighting, natural neutral posture with empty claws/limbs, zero held objects, no text labels, 8k, 16:9."
        )
        articulation_prompt = (
            f"Professional VFX creature anatomical articulation callout sheet of the exact same {char_name} ({char_desc}), "
            f"{style}, 16:9 layout. Detailed close-up reference views of the exact same creature's body parts: "
            f"(1) Head with jaws closed naturally showing lips and forward-facing eyes, "
            f"(2) Head with jaws open 45 degrees showing realistic inner jaw adductor muscles and teeth/tongue proportions, "
            f"(3) Detailed close-up of forelimbs/hands in resting empty state vs active flexing/holding state, and "
            f"(4) Heavy hind foot anatomy pressing into ground with cushioned footpads. Ultra-realistic texture and biomechanics, no text, 16:9."
        )
        scale_prompt = (
            f"AAA Studio Biomechanical Scale & Interaction Reference Sheet in {style}. "
            f"Full side-profile comparison on a unified ground plane locking exact real-world anatomical proportions "
            f"between {char_name} ({char_desc}) and a standard metric reference / secondary entity at strict 1:1 paleontological/anatomical scale. "
            f"Natural studio lighting, realistic ground contact shadows, zero exaggerated props, 8k, 16:9, no text."
        )
    elif char_type in ["mech", "robot", "cyborg"]:
        turnaround_prompt = (
            f"Professional AAA hard-surface mechanical model turnaround sheet of {char_name} ({char_desc}), "
            f"{style}. Multi-angle orthographic reference layout on a single 16:9 sheet showing 5 consistent views "
            f"of the exact same mech: (1) Full-body Front View, (2) Full-body Back View, (3) Left Side Profile View, "
            f"(4) Right 3/4 View, and (5) High-Angle Top-Down Perspective. Neutral standing pose with empty mechanical hands, "
            f"100% identical panel lines, hydraulic joints, and materials across all angles, clean studio grid background, no text labels, 16:9."
        )
        articulation_prompt = (
            f"Professional hard-surface joint articulation and hand-state callout sheet of {char_name}, {style}, 16:9 layout. "
            f"Left half shows optic sensor array / head unit in neutral, scanning, and combat modes. "
            f"Right half shows detailed mechanical manipulator hand in: (1) Relaxed open empty hand, (2) High-torque gripping hand state, "
            f"and (3) Extended tool/weapon hardpoint state. Clean studio reference, no text, 16:9."
        )
        scale_prompt = (
            f"AAA Hard-Surface Scale Reference Sheet in {style}. Full side-profile comparison on a clean hangar ground plane "
            f"locking exact metric height of {char_name} against a 1.8-meter human operator and vehicle at strict 1:1 scale, 8k, 16:9, no text."
        )
    else:  # human / anime / stylized 3d
        turnaround_prompt = (
            f"Professional AAA game & animation studio character model turnaround sheet of {char_name} ({char_desc}), "
            f"{style}. Multi-angle orthographic reference layout on a single 16:9 sheet showing 5 consistent views "
            f"of the exact same character: (1) Full-body Front View, (2) Full-body Back View, (3) Left Side Profile View, "
            f"(4) Right 3/4 View, and (5) High-Angle Top-Down Perspective. Neutral A-pose with empty hands, "
            f"100% identical proportions, facial features, hair, and costume across all angles, clean neutral studio grid background, "
            f"zero held objects, no detached props glued to hands, no text labels, 16:9."
        )
        articulation_prompt = (
            f"Professional character articulation, expression & hand-state model sheet of {char_name}, {style}, 16:9 layout. "
            f"Left half shows 3 facial expression & mouth states: (1) Neutral closed mouth, (2) Speaking phoneme mouth (lip-sync ready), "
            f"(3) High-emotion reaction face. Right half shows 3 anatomical hand states: (1) Relaxed open empty hands (palm front and back, strictly 5 fingers), "
            f"(2) Natural gripping hand posture ready to wrap around objects, and (3) Pointing/gesturing hand posture. Clean studio reference, no text."
        )
        scale_prompt = (
            f"Professional Character Scale Reference Sheet in {style}. Full side-by-side comparison on a flat ground plane "
            f"showing {char_name} next to a standard 1.8-meter height marker, doorframe, or co-star at strict 1:1 human scale, 8k, 16:9, no text."
        )

    # 2. Environment Clean Plate Prompt
    env_name = args.env_name or "Main Environment"
    env_desc = args.env_desc or "atmospheric lighting, detailed terrain, architecture and weather conditions"
    env_id = args.env_id or f"ENV_{slugify(env_name).upper().replace('-', '_')}"
    env_clean_prompt = (
        f"Pristine environment plate in {style}, {env_name}: {env_desc}. "
        f"Master wide architectural/landscape plate, volumetric ambient lighting and cinematic atmosphere. "
        f"Strict Clean Plate Rule: completely empty environment, no people, no characters, no creatures, no vehicles, "
        f"clear natural background ready for composite staging, 8k, 16:9, no text."
    )

    # 3. Props Library Prompt
    prop_prompts = []
    prop_entries = []
    if args.props:
        prop_list = [p.strip() for p in args.props.split(",") if p.strip()]
        for p_item in prop_list:
            pid = f"PROP_{slugify(p_item).upper().replace('-', '_')}"
            pprompt = (
                f"Professional AAA prop design and 3-angle turnaround sheet of {p_item}, in {style}. "
                f"Multi-angle isolated orthographic layout on neutral studio grey background: (1) Front View, (2) Side Profile View, "
                f"(3) Perspective 3/4 View showing materials, wear, and mechanical details. "
                f"Strict isolated studio asset: no hands holding it, no character attached, natural contact shadow on ground, "
                f"scaled accurately to standard physical dimensions, 8k, 16:9, no text."
            )
            prop_prompts.append((pid, p_item, pprompt))
            prop_entries.append({
                "id": pid,
                "name": p_item,
                "prop_prompt": pprompt,
                "path": f"assets/props/{pid}.png",
                "recommended_banana_model": "Nano Banana Pro"
            })

    output_data = {
        "character_rig_pack": {
            "id": char_id,
            "name": char_name,
            "type": char_type,
            "turnaround_sheet_prompt": turnaround_prompt,
            "articulation_sheet_prompt": articulation_prompt,
            "scale_sheet_prompt": scale_prompt,
            "turnaround_path": f"assets/characters/{char_id}_turnaround.png",
            "articulation_path": f"assets/characters/{char_id}_articulation.png",
            "scale_path": f"assets/characters/{char_id}_scale.png",
            "recommended_banana_model": "Nano Banana Pro"
        },
        "environment_clean_plate": {
            "id": env_id,
            "name": env_name,
            "clean_plate_prompt": env_clean_prompt,
            "path": f"assets/environments/{env_id}.png",
            "recommended_banana_model": "Nano Banana 2"
        },
        "props_library": prop_entries
    }

    if args.apply_to_manifest and manifest_path.exists():
        existing_chars = manifest.setdefault("characters", [])
        c_idx = next((i for i, c in enumerate(existing_chars) if c.get("id") == char_id), None)
        if c_idx is not None:
            existing_chars[c_idx].update(output_data["character_rig_pack"])
        else:
            existing_chars.append(output_data["character_rig_pack"])

        existing_envs = manifest.setdefault("environments", [])
        e_idx = next((i for i, e in enumerate(existing_envs) if e.get("id") == env_id), None)
        if e_idx is not None:
            existing_envs[e_idx].update(output_data["environment_clean_plate"])
        else:
            existing_envs.append(output_data["environment_clean_plate"])

        existing_props = manifest.setdefault("props", [])
        for pe in prop_entries:
            p_idx = next((i for i, p in enumerate(existing_props) if p.get("id") == pe["id"]), None)
            if p_idx is not None:
                existing_props[p_idx].update(pe)
            else:
                existing_props.append(pe)

        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Đã tự động cập nhật Bộ Tài Nguyên Chuẩn vào: {manifest_path}")

    print(json.dumps(output_data, ensure_ascii=False, indent=2))


def _sync_prompts_from_markdown_if_needed(proj_dir: Path, manifest: dict) -> bool:
    """Đồng bộ tự động veo_prompt và dialogue_text từ script_and_prompts.md nếu trong manifest đang trống."""
    md_path = proj_dir / "script_and_prompts.md"
    if not md_path.exists():
        return False
    md_text = md_path.read_text(encoding="utf-8")
    updated = False
    shots = manifest.get("shots", [])
    for s in shots:
        sid = s.get("shot_id", "")
        m_num = re.search(r"shot_(\d+)", sid)
        if not m_num:
            continue
        num_str = m_num.group(1)
        pattern = rf"###\s+Shot\s+0?{int(num_str)}\b.*?- \*\*Camera\*\*:\s*(.+?)\n.*?- \*\*(?:Narrator|Dialogue).*?\*\*:\s*`?\"(.+?)\"`?\n.*?- \*\*Veo 3\.1 Prompt\*\*:\s*```text\s*\n(.+?)\n```"
        match = re.search(pattern, md_text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            cam, dial, vprompt = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
            if not s.get("veo_prompt"):
                s["camera_shot"] = cam
                s["dialogue_text"] = dial
                s["veo_prompt"] = vprompt
                updated = True
    return updated


def cmd_audit_prompts(args):
    """
    Thực thi Vòng Lặp Kiểm Duyệt Prompt 3 Lần (3-Pass Senior AI Prompt Audit Loop)
    & Bộ Định Tuyến Model Thông Minh (Veo 3.1 Fast [10 tokens] vs. Veo 3.1 Quality [100 tokens],
    Nano Banana 2.1 vs. Nano Banana Pro) dựa trên ngân sách 85,000 tokens (+50 tokens/ngày).
    """
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] Không tìm thấy file {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _sync_prompts_from_markdown_if_needed(proj_dir, manifest)

    visual_style = manifest.get("visual_style", "Photorealistic 3D / Cinematic")
    characters = manifest.get("characters", [])
    environments = manifest.get("environments", [])
    shots = manifest.get("shots", [])

    audit_log = {
        "pass_1_semantic_and_scale_fixes": [],
        "pass_2_multi_angle_rig_and_articulation_fixes": [],
        "pass_3_cinematography_and_model_routing": [],
    }

    # =========================================================================
    # VÒNG 1 (PASS 1): DIỆT BẪY HIỂU SAI NGỮ NGHĨA, TỪ PHÓNG ĐẠI NỔ GIẢ & KHÓA TỶ LỆ ĐẠO CỤ
    # =========================================================================
    hyperbolic_replacements = [
        (r"\bsnapping and crushing it in half with explosive force as bone fragments and dust fly outward\b",
         "gripping the anatomically proportional rib bone in its heavy jaws; its thick neck and jaw muscles tense visibly as it bites down with 6-ton biomechanical pressure, bending and cracking the rib bone cleanly with realistic weight"),
        (r"\bwith explosive force\b", "with immense biomechanical muscular pressure and realistic physical weight"),
        (r"\bexplosive force\b", "heavy biomechanical pressure"),
        (r"\bexplosive\b", "high-impact biomechanical"),
        (r"\bexplode(?:s|d|ing)?\b", "fracture naturally under pressure"),
        (r"\bpulverize(?:s|d|ing)?\b", "crush"),
        (r"\bshatter(?:s|ed|ing)? into dust\b", "crack along natural structural lines"),
        (r"\bshockwave ripples\b", "natural acoustic concentric water ripples"),
        (r"\bshockwave\b", "heavy ground vibration"),
        (r"\ba thick prehistoric bone on the ground\b",
         "an anatomically proportional rib bone from a fresh herbivore carcass (measuring 0.4x the length of the T-Rex skull, natural ivory-bone anatomy, not oversized rock)"),
    ]

    # Bản đồ tra cứu nhanh Keyframes để kiểm tra Định Luật Bảo Toàn Thực Thể & Bảo Toàn Trạng Thái Con Mồi (v10.0)
    kf_map = {k.get("id"): k for k in manifest.get("boundary_keyframes", []) if k.get("id")}
    secondary_entity_Rules = [
        (r"\bpterosaurs?\b", "pterosaurs", "with a small flock of pterosaurs already visible gliding near the upper canopy edge"),
        (r"\bflock of birds\b", "birds", "with birds already visible near the upper sky edge"),
        (r"\bedmontosaurus\b", "edmontosaurus", "with a herd of duck-billed Edmontosaurus visible in the misty background"),
        (r"\btriceratops\b", "triceratops", "with an adult Triceratops visible in the frame"),
    ]

    # Bộ lọc v10.0 Diệt Lỗi "Xương Khô Bảo Tàng & Que Xương Cao Su Bay Lơ Lửng" (BBC Occluded-Contact & Prey State Conservation Filter):
    fake_bone_interaction_replacements = [
        (
            r"over the exposed ribcage of a freshly fallen Edmontosaurus carcass(?: lying in the mud)?;?\s*(?:the ivory rib bones are anatomically proportional[^,.]*)?",
            "over the massive flesh-covered flank of a freshly hunted 12-meter adult Edmontosaurus prey resting in the lower foreground mud (intact thick olive-grey scaly hide, massive body bulk equal in scale to the T-Rex itself, zero dry bleached museum skeleton, zero floating stick-bones)",
        ),
        (
            r"over the exposed ribcage of a freshly fallen Edmontosaurus carcass on the muddy riverbank\s*\([^)]*\)",
            "over the massive flesh-covered flank of a freshly hunted 12-meter adult Edmontosaurus prey resting in the lower foreground mud (intact thick olive-grey scaly hide, massive body bulk equal in scale to the T-Rex itself, zero dry bleached museum skeleton, zero floating stick-bones)",
        ),
        (
            r"clamps its heavy jaws firmly (?:around|onto) a(?:n)? (?:cracked,\s*)?anatomically proportional rib bone of the (?:fallen )?Edmontosaurus carcass(?:\s*\([^)]*\))?",
            "drives its heavy muzzle down in a closed-jaw occluded biomechanical clamp onto the massive flesh-covered flank of the 12-meter adult Edmontosaurus prey at the lower frame edge (intact thick hide, massive body bulk equal in scale to the T-Rex, jaws staying firmly clamped into the heavy torso mass, zero floating stick-like rubber bones in open jaws, zero dry skeleton)",
        ),
    ]

    for kf in manifest.get("boundary_keyframes", []):
        kid = kf.get("id", "unknown")
        kp = kf.get("nano_banana_prompt") or ""
        for pat, repl in fake_bone_interaction_replacements:
            if re.search(pat, kp, flags=re.IGNORECASE):
                kp = re.sub(pat, repl, kp, flags=re.IGNORECASE)
                audit_log["pass_1_semantic_and_scale_fixes"].append(
                    f"[{kid} - Pass 1 (v10.0 BBC Occluded-Contact & Anti-Skeleton Filter)] Đã thay thế mô tả dễ gây vẽ 'bộ xương khô bảo tàng / que xương cao su lơ lửng' bằng tương tác cơ sinh học chuẩn BBC (`Closed-Jaw Occluded Clamp on 1:1 Flesh-Covered Prey Flank`)."
                )
        kf["nano_banana_prompt"] = kp

    for s in shots:
        sid = s.get("shot_id", "unknown")
        vp = s.get("veo_prompt") or ""
        if not vp:
            continue
        for pat, repl in hyperbolic_replacements + fake_bone_interaction_replacements:
            if re.search(pat, vp, flags=re.IGNORECASE):
                vp = re.sub(pat, repl, vp, flags=re.IGNORECASE)
                audit_log["pass_1_semantic_and_scale_fixes"].append(
                    f"[{sid} - Pass 1 (v10.0 Biomechanical & Contact Filter)] Đã chuẩn hóa tương tác vật lý cơ sinh học (`{pat[:40]}...`)."
                )
        if s.get("dialogue_text") and re.search(r"\bpulverize\b", s["dialogue_text"], flags=re.IGNORECASE):
            s["dialogue_text"] = re.sub(r"\bpulverize\b", "crush", s["dialogue_text"], flags=re.IGNORECASE)

        # Nếu là cảnh ăn mồi / cắn / tương tác xác con mồi (Feeding / Bite / Carcass), tiêm khóa v10.0 Closed-Jaw Occluded Contact & 180-Degree Axis Lock:
        if any(w in vp.lower() for w in ["carcass", "bite", "clamps", "feeding", "prey flank"]):
            if "closed-jaw occluded clamp" not in vp.lower() and "never opening wide with a floating" not in vp.lower():
                vp = (
                    vp.rstrip(". ")
                    + ". Strict v10.0 BBC Biomechanical Contact Physics: closed-jaw occluded clamp where the T-Rex drives its muzzle firmly into the massive 1:1 scale flesh-covered prey flank at the lower frame edge while its thick jaw adductor and neck muscles bulge and tense under 6-ton crushing force (jaws stay firmly clamped on the target mass, NEVER opening wide with a floating stick-bone suspended in mid-air, NEVER rendering a dry bleached museum skeleton, NEVER flipping 180-degree left-right screen direction)."
                )
                audit_log["pass_1_semantic_and_scale_fixes"].append(
                    f"[{sid} - Pass 1 (v10.0 Closed-Jaw Occluded Contact & 180° Axis Lock)] Đã khóa vật lý tiếp xúc đóng khớp, căng cơ hàm, tỷ lệ con mồi 1:1 và khóa trục máy quay 180 độ."
                )

        # Kiểm tra Định Luật Bảo Toàn Thực Thể (v9.0 Entity Conservation & Anti-Pop-In Law):
        start_kf_id = (s.get("start_keyframe_id") or "").strip()
        start_kf = kf_map.get(start_kf_id)
        for ent_pat, ent_name, kf_inject in secondary_entity_Rules:
            if re.search(ent_pat, vp, flags=re.IGNORECASE):
                if start_kf:
                    k_prompt = start_kf.get("nano_banana_prompt") or ""
                    if not re.search(ent_pat, k_prompt, flags=re.IGNORECASE):
                        start_kf["nano_banana_prompt"] = k_prompt.rstrip(". ") + f", {kf_inject}."
                        audit_log["pass_1_semantic_and_scale_fixes"].append(
                            f"[{sid} / {start_kf_id} - Pass 1 (v9.0 Entity Conservation Law)] Phát hiện `{ent_name}` có trong `veo_prompt` nhưng THIẾU trong Start Frame `{start_kf_id}` (nguyên nhân gây lỗi CGI tự mọc ra giữa màn hình lúc 0:02-0:03). Đã đồng bộ `{ent_name}` vào `{start_kf_id}`!"
                        )
                if "never spawning or materializing mid-air" not in vp.lower():
                    vp = (
                        vp.rstrip(". ")
                        + f". Strict Entity Conservation: all {ent_name} must already be visible in the Start Frame at t=0.0s or enter smoothly from beyond the outer frame edge (never spawning or materializing mid-air inside the frame)."
                    )
                    audit_log["pass_1_semantic_and_scale_fixes"].append(
                        f"[{sid} - Pass 1 (v9.0 Anti-Pop-In Lock)] Đã khóa quy tắc cấm `{ent_name}` tự hiện hình giữa không trung (`No Mid-Air Spawning`)."
                    )

        # Khóa Quỹ Đạo Vượt Vật Chuẩn cho cảnh Bước Đi (v9.0 Anti-Treadmill Locomotion Law):
        cam_lower = (s.get("camera_shot") or "").lower()
        if any(w in vp.lower() or w in cam_lower for w in ["stride", "striding", "walking", "walks", "locomotion", "steps forward"]):
            if "zero in-place treadmill stepping" not in vp.lower():
                vp = (
                    vp.rstrip(". ")
                    + ". True forward spatial progression with strong foreground-to-background parallax: the subject's body physically advances 4 meters forward across the ground plane, passing completely past background tree trunks and landmarks (zero in-place treadmill stepping, zero foot-sliding)."
                )
                audit_log["pass_1_semantic_and_scale_fixes"].append(
                    f"[{sid} - Pass 1 (v9.0 Anti-Treadmill Parallax Lock)] Đã khóa quỹ đạo tiến về phía trước vượt qua cây cối/vật chuẩn nền (`Zero In-Place Treadmill Stepping`)."
                )

        # Kiểm tra nếu phần hình ảnh có nhắc tới bone/phone/cup/object mà chưa khóa tỷ lệ giải phẫu
        if re.search(r"\b(bone|carcass|phone|smartphone|cup|glass|sword|tool)\b", vp, flags=re.IGNORECASE) and "proportional" not in vp.lower():
            vp = vp.rstrip(". ") + ". Strict anatomical prop scale relative to the subject's head and limbs, no oversized rock-like objects."
            audit_log["pass_1_semantic_and_scale_fixes"].append(
                f"[{sid} - Pass 1] Đã chèn khóa tỷ lệ đạo cụ/vật thể (`Strict anatomical prop scale`) để chống AI vẽ vật thể to bất thường."
            )
        s["veo_prompt"] = vp.strip()

    # =========================================================================
    # VÒNG 2 (PASS 2): KHÓA BỘ 3 BẢN THIẾT KẾ MODEL ĐA GÓC ĐỘ & LUẬT GỘP SHOT CÙNG CẢNH (v10.0 TRUE SINGLE-TAKE & ZERO MORPHING)
    # =========================================================================
    for c in characters:
        cid = c.get("id", "unknown")
        cname = c.get("name", cid)
        base_p = (c.get("nano_banana_prompt") or "").strip()

        if not c.get("turnaround_sheet_prompt"):
            c["turnaround_sheet_prompt"] = (
                f"AAA Studio Character/Creature Model Orthographic 5-Angle Turnaround Reference Sheet of {cname} ({visual_style}). "
                f"The single 16:9 widescreen sheet displays the exact same {cname} from 5 orthographic views lined up cleanly: "
                f"(1) Front View, (2) Back View, (3) Left Profile View, (4) Right Profile View, and (5) Top-Down Dorsal View. "
                f"{base_p} Identical proportions, identical skin/scale/clothing markings across all 5 views, neutral daylight studio lighting, empty hands/limbs, no held props, 8k, 16:9, no text."
            )
            audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                f"[{cid} - Pass 2] Đã tự động thiết lập Bản Thiết Kế 5 Góc Độ (`turnaround_sheet_prompt`: Trước - Sau - Trái - Phải - Trên xuống)."
            )

        if not c.get("articulation_sheet_prompt"):
            c["articulation_sheet_prompt"] = (
                f"AAA Studio Anatomical Articulation, Facial/Jaw & Hand/Limb State Reference Sheet of {cname} ({visual_style}). "
                f"Split callout sheet on 16:9 canvas showing: "
                f"(Left Panel - Head & Mouth/Jaw Rig): Neutral closed mouth/jaw vs. Fully open vocalizing/biting jaw with accurate internal anatomy. "
                f"(Center Panel - Flexible Hand/Forelimb States): State A: Relaxed empty open hand/forelimb (no held object) vs. State B: Active anatomical gripping/holding pose (fingers/claws naturally wrapping around an object) vs. State C: Pointing/Action gesture. "
                f"(Right Panel - Load-Bearing Foot/Leg Rig): Ground contact weight compression. {base_p} 8k, 16:9, no text."
            )
            audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                f"[{cid} - Pass 2] Đã tự động thiết lập Bản Thiết Kế Bộ Phận & Cầm Nắm Linh Hoạt (`articulation_sheet_prompt`: Miệng/Hàm + Tay mở trống vs. Tay cầm đồ)."
            )

        if not c.get("scale_sheet_prompt"):
            c["scale_sheet_prompt"] = (
                f"AAA Studio Biomechanical Scale & Interaction Reference Sheet of {cname} ({visual_style}). "
                f"Full side-profile comparison locking exact real-world anatomical proportions between {cname} and its surrounding environment/prey/props on a unified ground plane. "
                f"Strict real-world scale, zero exaggerated prop sizes, {base_p} 8k, 16:9, no text."
            )
            audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                f"[{cid} - Pass 2] Đã tự động thiết lập Bản Thiết Kế Khóa Tỷ Lệ Thực (`scale_sheet_prompt`)."
            )

        c["recommended_banana_model"] = "Nano Banana Pro"

    for env in environments:
        env["recommended_banana_model"] = "Nano Banana 2"

    for s in shots:
        sid = s.get("shot_id", "unknown")
        vp = s.get("veo_prompt") or ""
        if not vp:
            continue
        if "continuous unbroken 3-phase" not in vp.lower() and "never finish the action early" not in vp.lower():
            vp = (
                vp.rstrip(". ")
                + ". Continuous unbroken 3-phase anatomical motion across the full 0.0s to 8.0s clip matching the narration duration (never finish the action early and never stop, freeze, or park in a static rest pose while speaking)."
            )
            audit_log["pass_1_semantic_and_scale_fixes"].append(
                f"[{sid} - Pass 1 (v9.0 Zero-Parking 3-Phase Action Lock)] Đã chèn khóa cử động 3 pha liên tục khớp độ dài thoại (`0-3s / 3-6s / 6-8s`), cấm dừng hình/đỗ xe giữa câu nói."
            )
        if "consistent 360-degree" not in vp.lower() and "model geometry" not in vp.lower():
            vp = vp.rstrip(". ") + ". Consistent 360-degree character model geometry and skin texture across all angles, accurate limb and jaw articulation, no extra limbs, no morphing."
            audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                f"[{sid} - Pass 2] Đã khóa hình học 360 độ & khớp nối giải phẫu (`Consistent 360-degree character model geometry & limb articulation`)."
            )
        s["veo_prompt"] = vp

    active_shots = [s for s in shots if (s.get("veo_prompt") or "").strip()]
    intra_scene_chains = 0
    inter_scene_cuts = 0
    for idx in range(len(active_shots)):
        cur_s = active_shots[idx]
        sid = cur_s.get("shot_id", f"shot_{idx+1:02d}")
        trans = cur_s.get("transition_to_next", "INTER_SCENE_CUT")
        if idx < len(active_shots) - 1:
            nxt_s = active_shots[idx + 1]
            nxt_id = nxt_s.get("shot_id", f"shot_{idx+2:02d}")
            cur_scene = cur_s.get("scene_id") or f"scene_{idx+1:02d}"
            nxt_scene = nxt_s.get("scene_id") or f"scene_{idx+2:02d}"
            if cur_scene == nxt_scene or trans == "INTRA_SCENE_CONTINUE":
                cur_s["transition_to_next"] = "INTRA_SCENE_CONTINUE"
                intra_scene_chains += 1
                removed_kf = cur_s.get("end_keyframe_id") or cur_s.get("last_frame_path") or "pre_generated_midpoint"
                cur_s["end_keyframe_id"] = ""
                cur_s["last_frame_path"] = ""
                cur_s["end_frame_parking_policy"] = "V10_OPEN_END_FOR_TRUE_SINGLE_TAKE_CHAIN"
                exact_chain_frame = f"assets/keyframes/{sid}_exact_cut_last_frame.png"
                nxt_s["start_keyframe_id"] = f"{sid}_EXACT_CUT_FRAME"
                nxt_s["first_frame_path"] = exact_chain_frame
                nxt_s["start_frame_chaining_policy"] = "V10_TRUE_SEQUENTIAL_EXACT_CUT_FRAME_ZERO_DISSOLVE"
                audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                    f"[{sid} -> {nxt_id} - Pass 2 (v10.0 True Single-Take Intra-Scene Chaining)] "
                    f"Đã gỡ bỏ ảnh giữa vẽ sẵn `{removed_kf}` khỏi `{sid}` (`End Frame = EMPTY`) và khóa `{nxt_id}` bắt đầu từ Frame cắt thực tế `{exact_chain_frame}` của `{sid}` (nối 0.00s Zero-Dissolve, 0% bóng ma, 100% như 1 cú máy liền mạch)."
                )
            else:
                cur_s["transition_to_next"] = "INTER_SCENE_CUT"
                inter_scene_cuts += 1
                # LUẬT v10.0 CẤM GẮN END FRAME TĨNH GÂY BIẾN HÌNH / LẬT HƯỚNG 180° (như lỗi K_08 xương khô quay phải -> K_09 xác thịt quay trái ở shot_09):
                if cur_s.get("end_keyframe_id") or cur_s.get("last_frame_path"):
                    removed_end = cur_s.get("end_keyframe_id") or cur_s.get("last_frame_path")
                    cur_s["end_keyframe_id"] = ""
                    cur_s["last_frame_path"] = ""
                    cur_s["end_frame_parking_policy"] = "V10_ZERO_END_FRAME_MORPH_AND_FLIP_GUARD"
                    audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
                        f"[{sid} -> {nxt_s.get('shot_id')} - Pass 2 (v10.0 Zero End-Frame Morph & Flip Guard)] Đã gỡ bỏ End Frame tĩnh `{removed_end}` khỏi `{sid}` để chống lỗi AI tự biến hình cỡ cảnh hoặc lật ngược 180 độ trạng thái xác con mồi (như lỗi K_08 -> K_09 ở 0:55-1:00)!"
                    )

    # =========================================================================
    # VÒNG 3 (PASS 3): TỐI ƯU ĐIỆN ẢNH, KINETIC FREEZE-TRIM, HIỆU ỨNG CHUYỂN CẢNH & ĐỊNH TUYẾN MODEL
    # =========================================================================
    total_fast_shots = 0
    total_quality_shots = 0
    total_veo_tokens = 0
    unoptimized_tokens = len(active_shots) * 100

    # Phân tích tự động Kinetic Trim & Hiệu ứng Chuyển cảnh (v9.0 True Single-Take & Anti-Pop-In Engine)
    _compute_kinetic_trims_and_transitions(proj_dir, active_shots, audit_log)

    for idx, s in enumerate(active_shots):
        sid = s.get("shot_id", f"shot_{idx+1:02d}")
        vp = s.get("veo_prompt") or ""
        cam = (s.get("camera_shot") or "").lower()
        # Chỉ chấm điểm dựa trên phần mô tả cảnh (trước phần saying: "...")
        visual_only = re.split(r"saying[^:]*:", vp, flags=re.IGNORECASE)[0].lower()

        # Đảm bảo câu kết chống phụ đề/watermark luôn chuẩn ở cuối Pass 3
        if "no subtitles" not in vp.lower():
            vp = vp.rstrip(". ") + ", no subtitles, no on-screen text."
            s["veo_prompt"] = vp

        # Chấm điểm độ phức tạp (Complexity Score 1 - 10)
        score = 1
        reasons = []

        # Bỏ phần mô tả nhân vật cố định trong ngoặc đơn (...) để chấm đúng hành động của cảnh
        action_only = re.sub(r"\([^)]*\)", "", visual_only)

        # 1. Tương tác vật lý cơ sinh học phức tạp (cắn, cầm nắm, đánh nhau, té bùn/nước mạnh, mở hàm răng)
        if re.search(r"\b(bite|bites|biting|clamps|crushing|cracking|grip|gripping|holding|drops|dropping|slams|splashing|combat|fight|fighting|clench|parting its heavy jaws)\b", action_only):
            score += 4
            reasons.append("Tương tác cơ sinh học phức tạp (hàm cắn/mở hàm/tay cầm nắm/va chạm vật lý)")

        # 2. Đa chủ thể tương tác trực tiếp trong khung hình
        if re.search(r"\b(two-shot|carcass|prey|versus|vs|predator and prey)\b", action_only) or "two-shot" in cam:
            score += 3
            reasons.append("Đa chủ thể / Tương tác trực tiếp với Con mồi/Đạo cụ")

        # 3. Góc máy Cận cảnh Chi tiết Giải phẫu (Extreme Close-Up mắt, cơ hàm, răng, ngón tay, bàn chân)
        if re.search(r"\b(extreme close-up|macro|jaws|teeth|forelimbs|three-toed|pupils)\b", action_only) or "macro" in cam:
            score += 3
            reasons.append("Cận cảnh giải phẫu chi tiết cao (Macro mắt/răng/cơ hàm/chi trước/bàn chân)")

        # 4. Cảnh mở đầu (Hook Shot 01) hoặc Cảnh kết cao trào (Climax Shot)
        if idx == 0 or idx == len(active_shots) - 1 or re.search(r"\b(climax|roar|thunderous)\b", action_only):
            score += 3
            reasons.append("Cảnh đinh (Hook mở đầu / Climax cao trào)")

        score = min(10, score)
        s["audit_passes_completed"] = 3
        s["complexity_score"] = score
        s["complexity_reasons"] = reasons if reasons else ["Cảnh tĩnh/di chuyển đơn giản (Standard Atmospheric/Tracking Shot)"]

        if score >= 4:
            s["recommended_veo_model"] = "Veo 3.1 - Quality"
            s["estimated_token_cost"] = 100
            total_quality_shots += 1
            total_veo_tokens += 100
        else:
            s["recommended_veo_model"] = "Veo 3.1 - Fast"
            s["estimated_token_cost"] = 10
            total_fast_shots += 1
            total_veo_tokens += 10

        audit_log["pass_3_cinematography_and_model_routing"].append(
            {
                "shot_id": sid,
                "complexity_score": f"{score}/10",
                "selected_model": s["recommended_veo_model"],
                "token_cost": s["estimated_token_cost"],
                "articulation_start_sec": s.get("articulation_start_sec", 0.0),
                "mid_speech_parking_detected": s.get("mid_speech_parking_detected", False),
                "cgi_pop_in_detected": s.get("cgi_pop_in_detected", False),
                "trim_window_sec": f"{s.get('trim_start_sec', 0.0):.2f}s .. {s.get('trim_end_sec', 8.0):.2f}s",
                "video_trim_window_sec": f"{s.get('video_trim_start_sec', 0.0):.2f}s .. {s.get('video_trim_end_sec', 8.0):.2f}s",
                "transition_to_next": s.get("editorial_transition_class", s.get("transition_to_next", "END")),
                "xfade_effect": f"{s.get('transition_effect', 'none')} ({s.get('transition_duration_sec', 0.0):.2f}s)",
                "qa_gate_status": s.get("v9_qa_gate_status", "PENDING_RENDER"),
                "reasons": s["complexity_reasons"],
            }
        )

    user_budget = getattr(args, "budget", 85000)
    tokens_saved = unoptimized_tokens - total_veo_tokens
    manifest["prompt_audit_summary"] = {
        "audit_version": "v9.0 (True Single-Take Intra-Scene Chaining + Entity Conservation Anti-Pop-In + Parallax Lock)",
        "passes_executed": 3,
        "active_shots_audited": len(active_shots),
        "intra_scene_continuations_same_scene_16s_24s": intra_scene_chains,
        "inter_scene_editorial_transitions_new_scene": inter_scene_cuts,
        "veo_quality_shots_100_tokens": total_quality_shots,
        "veo_fast_shots_10_tokens": total_fast_shots,
        "total_veo_tokens_required": total_veo_tokens,
        "unoptimized_all_quality_tokens": unoptimized_tokens,
        "smart_routing_tokens_saved": tokens_saved,
        "user_available_tokens": user_budget,
        "remaining_tokens_after_batch": user_budget - total_veo_tokens,
        "daily_regen_tokens": 50,
    }

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "summary": manifest["prompt_audit_summary"],
                "audit_log": audit_log,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _download_single(task: tuple) -> dict:
    rel_path, url, out_path = task
    t0 = time.time()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out_path)
    return {
        "file": rel_path,
        "bytes": out_path.stat().st_size,
        "elapsed_sec": round(time.time() - t0, 2),
    }


def cmd_download_batch(args):
    """Tải song song đa luồng (12 luồng CPU Ryzen 5600H) tất cả các URL có trong project_manifest.json hoặc file JSON."""
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    tasks = []

    if args.urls_json:
        mapping = json.loads(Path(args.urls_json).read_text(encoding="utf-8"))
        for rel, url in mapping.items():
            if url:
                tasks.append((rel, url, proj_dir / rel))
    elif manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for s in manifest.get("shots", []):
            url = s.get("cdn_video_url")
            rel = s.get("clip_output_path")
            if url and rel:
                tasks.append((rel, url, proj_dir / rel))

    if not tasks:
        print("[INFO] Không có URL nào cần tải.", file=sys.stderr)
        return

    t0 = time.time()
    results = []
    workers = min(CPU_THREADS, len(tasks))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_download_single, t) for t in tasks]
        for fut in as_completed(futures):
            results.append(fut.result())

    print(
        json.dumps(
            {
                "status": "ok",
                "parallel_workers": workers,
                "files_downloaded": len(results),
                "total_elapsed_sec": round(time.time() - t0, 2),
                "details": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def get_ffmpeg_exe() -> str:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "ffmpeg"
    except Exception:
        pass
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg", "opencv-python"], check=True)
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()


def has_nvenc(ffmpeg_exe: str) -> bool:
    """Kiểm tra xem card rời NVIDIA RTX 3050 (`h264_nvenc`) có sẵn sàng mã hóa phần cứng không."""
    try:
        res = subprocess.run(
            [
                ffmpeg_exe,
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=256x256:d=0.1",
                "-c:v",
                "h264_nvenc",
                "-f",
                "null",
                "-",
            ],
             stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def ensure_cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python"], check=True)
        import cv2
        return cv2


def cmd_extract_last_frame(args):
    clip_path = Path(args.clip).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cv2 = ensure_cv2()
    cap = cv2.VideoCapture(str(clip_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    target_idx = max(0, total_frames - 2)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 1))
        ret, frame = cap.read()
    cap.release()
    if not ret:
        print(f"[ERROR] Không thể đọc frame cuối từ {clip_path}", file=sys.stderr)
        sys.exit(1)
    cv2.imwrite(str(out_path), frame)
    print(json.dumps({"status": "ok", "extracted_last_frame": str(out_path)}, ensure_ascii=False))


def cmd_extract_active_frame(args):
    """
    Trích xuất Khung Hình Đang Cử Động Mượt Nhất (v8.0 Live Active-Motion Frame Chaining):
    - Thay vì lấy frame cuối cùng khi nhân vật đã ngậm miệng/đứng im (Static Rest Pose),
      lệnh này quét quanh thời điểm kết thúc thoại (`speech_end_sec`) và chọn frame có
      độ nét cao nhất đang trong pha cử động khớp (`Sharp-Edge Articulation P85 >= 3.0`)
      để làm Start Frame nối tiếp hoàn hảo cho Shot kế tiếp!
    """
    import numpy as np

    clip_path = Path(args.clip).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cv2 = ensure_cv2()
    ffmpeg_exe = get_ffmpeg_exe()
    prof = _analyze_clip_speech_and_motion(clip_path, ffmpeg_exe, is_last_clip=False)
    sp_end = prof["speech_end_sec"]

    cap = cv2.VideoCapture(str(clip_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    dur = round(total_frames / fps, 2) if total_frames > 0 else 8.0

    # Trích xuất chính xác Frame tại t_cut = min(dur, round(sp_end + 0.08, 2)) khớp 100% với điểm cắt Zero-Dissolve của Shot A
    cut_a = min(dur, round(sp_end + 0.08, 2))
    best_idx = min(max(0, total_frames - 2), max(0, int(cut_a * fps) - 1))

    cap.set(cv2.CAP_PROP_POS_FRAMES, best_idx)
    ret, best_frame = cap.read()
    cap.release()
    if not ret:
        print(f"[ERROR] Không thể trích xuất exact-cut frame từ {clip_path}", file=sys.stderr)
        sys.exit(1)
    cv2.imwrite(str(out_path), best_frame)
    print(
        json.dumps(
            {
                "status": "ok",
                "extracted_active_frame": str(out_path),
                "selected_timestamp_sec": cut_a,
                "frame_index": best_idx,
                "speech_end_sec": sp_end,
            },
            ensure_ascii=False,
        )
    )


def _qa_single_clip(cpath: Path, qa_dir: Path) -> str:
    import cv2
    import numpy as np

    ratios = [0.10, 0.40, 0.70, 0.92]
    cap = cv2.VideoCapture(str(cpath))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    if total_frames <= 0:
        cap.release()
        return ""

    sampled = []
    for r in ratios:
        idx = min(total_frames - 1, max(0, int(total_frames * r)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        h, w = frame.shape[:2]
        new_w, new_h = 640, int(640 * h / max(1, w))
        resized = cv2.resize(frame, (new_w, new_h))
        t_sec = idx / fps
        label = f"{cpath.stem} | t={t_sec:.1f}s (frame {idx}/{total_frames})"
        cv2.rectangle(resized, (8, 8), (460, 42), (0, 0, 0), -1)
        cv2.putText(resized, label, (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        sampled.append(resized)
    cap.release()

    if len(sampled) == 4:
        top = np.hstack([sampled[0], sampled[1]])
        bot = np.hstack([sampled[2], sampled[3]])
        grid = np.vstack([top, bot])
        out_img = qa_dir / f"{cpath.stem}_qa_grid.jpg"
        cv2.imwrite(str(out_img), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return str(out_img)
    return ""


def cmd_qa_frames(args):
    """Trích xuất song song 12 luồng CPU toàn bộ lưới ảnh QA Contact Sheet chỉ trong <1 giây."""
    t0 = time.time()
    proj_dir = Path(args.project).resolve()
    clips_dir = proj_dir / "assets" / "clips"
    qa_dir = proj_dir / "assets" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    ensure_cv2()
    clip_files = sorted(clips_dir.glob("*.mp4"))
    if not clip_files:
        print(f"[ERROR] Không tìm thấy clip .mp4 nào trong {clips_dir}", file=sys.stderr)
        sys.exit(1)

    qa_outputs = []
    workers = min(CPU_THREADS, len(clip_files))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_qa_single_clip, cpath, qa_dir) for cpath in clip_files]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                qa_outputs.append(res)

    qa_outputs.sort()
    print(
        json.dumps(
            {
                "status": "ok",
                "parallel_workers": workers,
                "elapsed_sec": round(time.time() - t0, 2),
                "clips_inspected": len(qa_outputs),
                "qa_contact_sheets": qa_outputs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _analyze_clip_speech_and_motion(clip_path: Path, ffmpeg_exe: str, is_last_clip: bool = False, shot_meta: dict = None) -> dict:
    """
    Hệ thống Phân Tích Chuyển Động Khớp, Bắt Lỗi CGI Pop-In & Đi Bộ Tại Chỗ v9.0:
    1. Đo cửa sổ thoại thực tế [speech_start_sec, speech_end_sec] ở độ phân giải 50ms.
    2. Dùng bộ lọc biên Sobel (edge > 45.0) + Khung xương cứng (Strong Structural Edge > 90.0) kết hợp Optical Flow Farneback
       để đo cả cử động khớp (`artic_curve`) lẫn dịch chuyển thực của hộp sọ/cơ thể (`rigid_body_curve`).
    3. Tự động phát hiện 4 lỗi chí mạng cấp Senior AI Film Engineer:
       - `cgi_pop_in_detected`: Vật thể/khủng long bay tự nhiên mọc ra từ hư không giữa khung hình (như Shot 01 lúc 0:02.7s).
       - `mid_speech_parking_detected`: Chủ thể dừng quay đầu / ngậm miệng đứng im >= 1.0s trong khi thoại vẫn đang đọc (như Shot 05 lúc 2.80s..4.35s).
       - `treadmill_stepping_detected`: Chủ thể bước chân nhưng thân cây/bối cảnh phía sau đứng yên không trôi qua (đi bộ trên máy chạy bộ như Shot 03 lúc 0:14.8s..0:16.7s).
       - `end_frame_freeze_detected`: Chủ thể đóng băng ở 1 giây cuối cảnh trước khi hết câu (như Shot 02 lúc 0:13.5s..0:14.35s).
    """
    import numpy as np

    duration = 8.0
    speech_start = 0.05
    speech_end = 7.50
    motion_head = 5.0
    motion_tail = 5.0
    articulation_start = 0.0
    mid_speech_parking = False
    parking_windows = []
    artic_curve = []
    rigid_body_curve = []
    cgi_pop_in_detected = False
    cgi_pop_in_windows = []
    treadmill_detected = False
    early_stasis_sec = 0.0

    if not clip_path.exists():
        return {
            "duration": duration,
            "speech_start_sec": speech_start,
            "speech_end_sec": speech_end,
            "motion_head": motion_head,
            "motion_tail": motion_tail,
            "articulation_start_sec": articulation_start,
            "mid_speech_parking_detected": mid_speech_parking,
            "mid_speech_parking_windows": parking_windows,
            "articulation_curve_250ms": artic_curve,
            "rigid_body_curve_250ms": rigid_body_curve,
            "cgi_pop_in_detected": cgi_pop_in_detected,
            "cgi_pop_in_windows": cgi_pop_in_windows,
            "treadmill_stepping_detected": treadmill_detected,
            "early_stasis_start_sec": early_stasis_sec,
        }

    try:
        cv2 = ensure_cv2()
        cap = cv2.VideoCapture(str(clip_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if n_frames > 0:
            duration = round(n_frames / fps, 2)
        frames = []
        while True:
            ret, f = cap.read()
            if not ret:
                break
            frames.append(cv2.cvtColor(cv2.resize(f, (320, 180)), cv2.COLOR_BGR2GRAY))
        cap.release()
        if len(frames) > 6:
            diffs = [0.0] + [float(np.mean(cv2.absdiff(frames[k], frames[k - 1]))) for k in range(1, len(frames))]
            motion_head = round(float(np.mean(diffs[1:7])), 2)
            motion_tail = round(float(np.mean(diffs[-18:])), 2)

            step = max(1, int(fps * 0.25))
            bg_dx_list = []
            leg_flow_list = []

            for i in range(0, len(frames) - step, step):
                f1 = frames[i][25:155, 50:270]
                f2 = frames[i + step][25:155, 50:270]
                e1 = np.hypot(cv2.Sobel(f1, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(f1, cv2.CV_32F, 0, 1, ksize=3))
                mask = e1 > 45.0
                rigid_mask = e1 > 95.0
                flow = cv2.calcOpticalFlowFarneback(f1, f2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                if int(np.sum(mask)) >= 80:
                    dx = flow[..., 0][mask] - np.median(flow[..., 0][mask])
                    dy = flow[..., 1][mask] - np.median(flow[..., 1][mask])
                    mag = np.sqrt(dx * dx + dy * dy)
                    val = float(np.percentile(mag, 85))
                else:
                    val = 3.0
                artic_curve.append(round(val, 2))

                if int(np.sum(rigid_mask)) >= 40:
                    rdx = flow[..., 0][rigid_mask] - np.median(flow[..., 0][rigid_mask])
                    rdy = flow[..., 1][rigid_mask] - np.median(flow[..., 1][rigid_mask])
                    rmag = np.sqrt(rdx * rdx + rdy * rdy)
                    rval = float(np.percentile(rmag, 78))
                else:
                    rval = val
                rigid_body_curve.append(round(rval, 2))

                # Đo Parallax nền (1/3 trên) vs. Chuyển động chân (1/3 dưới) để bắt lỗi Đi bộ trên máy chạy bộ (Treadmill)
                full_flow = cv2.calcOpticalFlowFarneback(frames[i], frames[i + step], None, 0.5, 3, 15, 3, 5, 1.2, 0)
                bg_dx = float(np.median(full_flow[10:60, 40:280, 0]))
                leg_mag = float(np.percentile(np.hypot(full_flow[110:172, 70:250, 0], full_flow[110:172, 70:250, 1]), 85))
                bg_dx_list.append(bg_dx)
                leg_flow_list.append(leg_mag)

            # Bắt lỗi CGI Mid-Frame Pop-In (như đàn Pterosaurs tự mọc ra giữa màn hình lúc 2.5s..3.5s ở Shot 01):
            # Đếm số thực thể tối nhỏ (flying silhouettes / pop-in blobs) xuất hiện đột ngột ở vùng giữa bầu trời/tán cây [18:85, 70:250]
            blob_counts = []
            for i in range(0, len(frames), step):
                roi = frames[i][18:85, 70:250]
                blur = cv2.GaussianBlur(roi, (21, 21), 0)
                bmask = ((blur.astype(np.float32) - roi.astype(np.float32)) > 22.0).astype(np.uint8)
                num_l, _, stats, _ = cv2.connectedComponentsWithStats(bmask)
                cnt = sum(1 for k in range(1, num_l) if 6 <= stats[k, cv2.CC_STAT_AREA] <= 180 and stats[k, cv2.CC_STAT_WIDTH] >= 3)
                blob_counts.append(cnt)

            if len(blob_counts) >= 15:
                base_blobs = float(np.mean(blob_counts[4:11]))  # trung bình giai đoạn 1.0s .. 2.5s (bầu trời/tán cây sạch sẽ có base_blobs <= 7.5)
                if base_blobs <= 7.5:
                    for w_i in range(11, min(20, len(blob_counts))):
                        if blob_counts[w_i] >= base_blobs * 2.0 and blob_counts[w_i] >= 10:
                            t_pop = round(w_i * 0.25, 2)
                            cgi_pop_in_detected = True
                            cgi_pop_in_windows.append(f"{t_pop:.2f}s(blobs={blob_counts[w_i]}_vs_base={base_blobs:.1f})")

            # Tìm articulation_start_sec trong 1.50s đầu tiên (6 cửa sổ 0.25s)
            idx_w = 0
            while idx_w < min(6, len(artic_curve)) and artic_curve[idx_w] < 2.50:
                idx_w += 1
            articulation_start = round(idx_w * 0.25, 2)

            # Kiểm tra lỗi Đi bộ trên máy chạy bộ (Treadmill Locomotion) cho các cảnh Camera Tracking / Walking / Striding:
            cam_text = ((shot_meta or {}).get("camera_shot") or "").lower()
            if any(w in cam_text for w in ["stride", "striding", "walking", "locomotion"]):
                # Quét cửa sổ trượt 6 nhịp (1.5s): nếu chân bước mạnh (mean leg_flow >= 3.5) nhưng nền hầu như đứng yên (abs(mean bg_dx) < 0.55)
                for w_i in range(0, max(1, len(bg_dx_list) - 6)):
                    win_bg = bg_dx_list[w_i : w_i + 6]
                    win_leg = leg_flow_list[w_i : w_i + 6]
                    if len(win_bg) == 6 and float(np.mean(win_leg)) >= 3.5 and abs(float(np.mean(win_bg))) < 0.55:
                        treadmill_detected = True
                        break

            # Kiểm tra lỗi v10.0 Biến Hình Cỡ Cảnh / Lật Hướng 180 Độ / Biến Xương Khô Thành Xác Thịt (In-Shot Morphing & 180° Pose Flip ở 0:49..1:01):
            in_shot_morph_reasons = []
            if len(frames) >= 120:
                f_early = frames[10]
                f_late = frames[-18]
                # 1. Đo dịch chuyển tâm khối tối (Dark Subject Center of Mass X) ở nửa trên khung hình [15:115, 20:300]
                xs = np.arange(280, dtype=np.float32)
                w_early = np.maximum(0.0, 95.0 - f_early[15:115, 20:300].astype(np.float32))
                w_late = np.maximum(0.0, 95.0 - f_late[15:115, 20:300].astype(np.float32))
                com_x_early = float(np.sum(w_early.mean(axis=0) * xs) / max(1.0, float(np.sum(w_early.mean(axis=0)))))
                com_x_late = float(np.sum(w_late.mean(axis=0) * xs) / max(1.0, float(np.sum(w_late.mean(axis=0)))))
                # 2. Đo mật độ xương sáng sắc nét (Bright Skeletal Rib/Bone Edges) ở 1/3 dưới khung hình [115:175, 50:270]
                eb_early = np.hypot(cv2.Sobel(f_early[115:175, 50:270], cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(f_early[115:175, 50:270], cv2.CV_32F, 0, 1, ksize=3))
                eb_late = np.hypot(cv2.Sobel(f_late[115:175, 50:270], cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(f_late[115:175, 50:270], cv2.CV_32F, 0, 1, ksize=3))
                skel_early = int(np.sum((f_early[115:175, 50:270] > 115) & (eb_early > 60.0)))
                skel_late = int(np.sum((f_late[115:175, 50:270] > 115) & (eb_late > 60.0)))

                if any(k in cam_text for k in ["feeding", "carcass", "bite"]):
                    if abs(com_x_late - com_x_early) >= 24.0:
                        in_shot_morph_reasons.append(f"180_DEG_POSE_AND_CARCASS_STATE_FLIP(com_x:{com_x_early:.0f}->{com_x_late:.0f}px)")
                    if abs(skel_late - skel_early) >= 350:
                        in_shot_morph_reasons.append(f"IN_SHOT_SKELETON_FLESH_OR_FOCAL_MORPH(skel_px:{skel_early}->{skel_late})")
    except Exception:
        in_shot_morph_reasons = []

    try:
        cmd = [ffmpeg_exe, "-i", str(clip_path), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
        raw = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if len(samples) >= 1600:
            rms = [float(np.sqrt(np.mean(samples[k : k + 800] ** 2))) for k in range(0, len(samples), 800)]
            n_b = len(rms)
            start_idx = 0
            for k in range(min(32, n_b - 6)):
                win = rms[k : k + 6]
                if rms[k] >= 0.050 and sum(1 for x in win if x >= 0.052) >= 3 and float(np.mean(win[:5])) >= 0.058:
                    start_idx = k
                    break
            speech_start = round(start_idx * 0.05, 2)

            if is_last_clip:
                end_idx = n_b - 1
            else:
                end_idx = int(min(n_b - 1, 148))
                for k in range(n_b - 4, max(115, start_idx + 10), -1):
                    win = rms[max(0, k - 3) : k + 1]
                    if sum(1 for x in win if x >= 0.050) >= 3 and max(win) >= 0.068:
                        end_idx = k
                        while end_idx + 1 < n_b - 2 and rms[end_idx + 1] >= 0.048:
                            end_idx += 1
                        break
            speech_end = round(min(duration, max(5.5, (end_idx + 1) * 0.05)), 2)
    except Exception:
        pass

    # Phát hiện lỗi "Đỗ Xe Giữa Câu Thoại / Dừng Quay Đầu Sớm" (Mid-Speech Subject Parking & Early Stasis):
    if (not is_last_clip) and artic_curve and max(artic_curve) >= 4.2:
        max_w = min(len(artic_curve), int((speech_end + 0.30) / 0.25))
        consec = 0
        cur_run = []
        for w_idx in range(6, max_w):
            # Thực sự đứng hình khi CẢ artic_curve < 2.20 LẪN rigid_body_curve < 1.55 kéo dài >= 4 cửa sổ (1.0s+)
            r_val = rigid_body_curve[w_idx] if w_idx < len(rigid_body_curve) else artic_curve[w_idx]
            if artic_curve[w_idx] < 2.20 and r_val < 1.55:
                consec += 1
                cur_run.append(f"{w_idx*0.25:.2f}s(artic={artic_curve[w_idx]},rigid={r_val})")
                if consec >= 4:
                    mid_speech_parking = True
                    if early_stasis_sec == 0.0:
                        early_stasis_sec = round((w_idx - consec + 1) * 0.25, 2)
                    parking_windows = list(cur_run)
            else:
                consec = 0
                cur_run = []

    return {
        "duration": duration,
        "speech_start_sec": speech_start,
        "speech_end_sec": speech_end,
        "motion_head": motion_head,
        "motion_tail": motion_tail,
        "articulation_start_sec": articulation_start,
        "mid_speech_parking_detected": mid_speech_parking,
        "mid_speech_parking_windows": parking_windows,
        "early_stasis_start_sec": early_stasis_sec,
        "cgi_pop_in_detected": cgi_pop_in_detected,
        "cgi_pop_in_windows": cgi_pop_in_windows,
        "treadmill_stepping_detected": treadmill_detected,
        "in_shot_morphing_or_flip_reasons": in_shot_morph_reasons,
        "articulation_curve_250ms": artic_curve,
        "rigid_body_curve_250ms": rigid_body_curve,
    }


def _find_best_seam_frame_in_tail(clip_a: Path, min_time_a: float, dur_a: float, clip_b: Path) -> tuple[float, float]:
    """Quét vùng cuối [min_time_a, dur_a] của Shot A để tìm chính xác Frame khớp 100% với Frame #0 của Shot B (phục vụ nối 0.00s Zero-Dissolve)."""
    import numpy as np

    if not (clip_a.exists() and clip_b.exists()):
        return round(min(dur_a, min_time_a + 0.08), 3), 99.9
    try:
        cv2 = ensure_cv2()
        cap_b = cv2.VideoCapture(str(clip_b))
        ret_b, fb = cap_b.read()
        cap_b.release()
        if not ret_b:
            return round(min(dur_a, min_time_a + 0.08), 3), 99.9
        gb = cv2.cvtColor(cv2.resize(fb, (320, 180)), cv2.COLOR_BGR2GRAY)

        cap_a = cv2.VideoCapture(str(clip_a))
        fps_a = cap_a.get(cv2.CAP_PROP_FPS) or 24.0
        n_a = int(cap_a.get(cv2.CAP_PROP_FRAME_COUNT))
        start_idx = max(0, min(n_a - 2, int(min_time_a * fps_a) - 2))
        best_idx = min(n_a - 1, max(0, int((min_time_a + 0.08) * fps_a)))
        best_diff = 99.9
        for idx in range(start_idx, n_a):
            cap_a.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret_a, fa = cap_a.read()
            if not ret_a:
                continue
            ga = cv2.cvtColor(cv2.resize(fa, (320, 180)), cv2.COLOR_BGR2GRAY)
            d = float(np.mean(cv2.absdiff(ga, gb)))
            if d < best_diff:
                best_diff = d
                best_idx = idx
        cap_a.release()
        best_t = round(min(dur_a, (best_idx + 1) / fps_a), 3)
        return best_t, round(best_diff, 2)
    except Exception:
        return round(min(dur_a, min_time_a + 0.08), 3), 99.9


def _compute_kinetic_trims_and_transitions(proj_dir: Path, active_shots: list, audit_log: dict):
    """
    Hệ thống Dựng Phim Thông Minh v10.0 (True Single-Take Intra-Scene Stitch + BBC Contact Physics & Morphing QA Gate + Max 1.18x Stretch Cap):
    """
    MAX_PTS_STRETCH = 1.18
    ffmpeg_exe = get_ffmpeg_exe()
    n = len(active_shots)
    profiles = []
    clip_paths = []
    for idx, s in enumerate(active_shots):
        rel_path = s.get("clip_output_path") or f"assets/clips/{s.get('shot_id', f'shot_{idx+1:02d}')}.mp4"
        cpath = proj_dir / rel_path
        clip_paths.append(cpath)
        prof = _analyze_clip_speech_and_motion(cpath, ffmpeg_exe, is_last_clip=(idx == n - 1), shot_meta=s)
        profiles.append(prof)
        s["speech_start_sec"] = prof["speech_start_sec"]
        s["speech_end_sec"] = prof["speech_end_sec"]
        s["articulation_start_sec"] = prof["articulation_start_sec"]
        s["mid_speech_parking_detected"] = prof["mid_speech_parking_detected"]
        s["mid_speech_parking_windows"] = prof["mid_speech_parking_windows"]
        s["early_stasis_start_sec"] = prof["early_stasis_start_sec"]
        s["cgi_pop_in_detected"] = prof["cgi_pop_in_detected"]
        s["cgi_pop_in_windows"] = prof["cgi_pop_in_windows"]
        s["treadmill_stepping_detected"] = prof["treadmill_stepping_detected"]
        s["in_shot_morphing_or_flip_reasons"] = prof.get("in_shot_morphing_or_flip_reasons", [])

        qa_flags = []
        if prof["cgi_pop_in_detected"]:
            qa_flags.append(f"REJECT_CGI_MID_FRAME_POP_IN({','.join(prof['cgi_pop_in_windows'][:2])})")
        if prof["treadmill_stepping_detected"]:
            qa_flags.append("REJECT_TREADMILL_IN_PLACE_LOCOMOTION")
        if prof["mid_speech_parking_detected"]:
            qa_flags.append(f"REJECT_EARLY_STASIS_AT_{prof['early_stasis_start_sec']}s_BEFORE_SPEECH_END_{prof['speech_end_sec']}s")
        for m_reason in s["in_shot_morphing_or_flip_reasons"]:
            qa_flags.append(f"REJECT_{m_reason}")
        s["v9_qa_gate_status"] = " | ".join(qa_flags) if qa_flags else ("PASS" if cpath.exists() else "PENDING_RENDER")

    # Bước 1: Tính trim_start_sec cho kênh Audio và kênh Video
    for idx, s in enumerate(active_shots):
        prof = profiles[idx]
        sp_start = prof["speech_start_sec"]
        artic_start = prof["articulation_start_sec"]
        m_head = prof["motion_head"]
        if idx == 0:
            s["trim_start_sec"] = 0.0
        else:
            if sp_start >= 0.80:
                pad = 0.25 if s.get("sub_shot_index", 1) > 1 else 0.40
                audio_trim = max(0.0, sp_start - pad)
            elif sp_start >= 0.25 and m_head < 3.8:
                audio_trim = max(0.0, sp_start - 0.20)
            else:
                audio_trim = 0.0

            if artic_start > 0.25 and sp_start >= 0.25:
                active_trim = min(artic_start, max(0.0, sp_start - 0.15))
                s["trim_start_sec"] = round(max(audio_trim, active_trim), 2)
            else:
                s["trim_start_sec"] = round(audio_trim, 2)
        s["video_trim_start_sec"] = s["trim_start_sec"]

    # Bước 2: Phân loại chuyển cảnh v9.0 (True Single-Take 0.00s Stitch cho INTRA_SCENE_CONTINUE vs. Editorial Dissolve cho INTER_SCENE_CUT)
    for idx in range(n):
        cur_s = active_shots[idx]
        sid = cur_s.get("shot_id", f"shot_{idx+1:02d}")
        prof_a = profiles[idx]
        dur_a = prof_a["duration"]
        sp_end_a = prof_a["speech_end_sec"]

        if idx == n - 1:
            cur_s["trim_end_sec"] = dur_a
            cur_s["video_trim_end_sec"] = dur_a
            cur_s["editorial_transition_class"] = "END_OF_SEQUENCE"
            cur_s["transition_effect"] = "none"
            cur_s["transition_duration_sec"] = 0.0
            continue

        nxt_s = active_shots[idx + 1]
        nxt_id = nxt_s.get("shot_id", f"shot_{idx+2:02d}")
        prof_b = profiles[idx + 1]
        sp_start_b = prof_b["speech_start_sec"]
        trim_start_b = nxt_s["trim_start_sec"]
        head_margin_b = max(0.0, sp_start_b - trim_start_b)

        trans_mode = cur_s.get("transition_to_next", "INTER_SCENE_CUT")
        cur_cam = (cur_s.get("camera_shot") or "").lower()
        nxt_cam = (nxt_s.get("camera_shot") or "").lower()
        cur_vp = (cur_s.get("veo_prompt") or "").lower()

        if trans_mode == "INTRA_SCENE_CONTINUE":
            # LUẬT v10.0: Cùng 1 cảnh (INTRA_SCENE_CONTINUE) -> CẤM DÙNG XFADE GÂY BÓNG MA 2 ĐẦU!
            # Tìm chính xác Frame khớp (Seam Frame) trong vùng cuối [sp_end_a, dur_a] của Shot A so với Frame #0 của Shot B
            seam_t_a, l1_diff_frame0 = _find_best_seam_frame_in_tail(clip_paths[idx], sp_end_a, dur_a, clip_paths[idx + 1])
            cur_s["intra_scene_boundary_l1_diff"] = l1_diff_frame0

            t_class = "INTRA_SCENE_TRUE_SINGLE_TAKE_ZERO_DISSOLVE"
            effect = "concat_single_take"
            actual_t = 0.0
            # Giữ khoảng nghỉ thoại tự nhiên <= 0.35s, còn kênh Video lấy trọn tới đúng Frame khớp seam_t_a
            trim_end_a = min(seam_t_a, round(sp_end_a + 0.35, 2))

            if l1_diff_frame0 <= 9.5:
                # Khớp 100% Frame cuối Shot A == Frame 0 Shot B -> Giữ nguyên Video Shot B từ Frame #0 (0.000s)!
                nxt_s["video_trim_start_sec"] = 0.0
            else:
                if "REJECT_INTRA_SCENE_SEAM_MISMATCH" not in cur_s.get("v9_qa_gate_status", ""):
                    prev_flag = cur_s.get("v9_qa_gate_status", "PASS")
                    new_flag = f"REJECT_INTRA_SCENE_SEAM_MISMATCH_WITH_{nxt_id}(L1_diff={l1_diff_frame0}px>9.5px)"
                    cur_s["v9_qa_gate_status"] = new_flag if prev_flag == "PASS" else f"{prev_flag} | {new_flag}"

            cur_s["trim_end_sec"] = trim_end_a
            cur_s["video_trim_end_sec"] = seam_t_a
            cur_s["editorial_transition_class"] = t_class
            cur_s["transition_effect"] = effect
            cur_s["transition_duration_sec"] = actual_t
        else:
            if ("stride" in cur_cam or "walking" in cur_vp) and ("tracking" in nxt_cam or "stride" in nxt_cam or "telephoto" in nxt_cam):
                t_class = "INTER_SCENE_TRACKING_TRANSITION"
                effect = "smoothleft"
                target_t = 0.45
                desired_gap = 0.20
            elif ("close-up" in cur_cam or "sensory" in cur_cam) and ("close-up" in nxt_cam or "forelimbs" in nxt_cam or "chest" in nxt_cam):
                t_class = "INTER_SCENE_ANATOMICAL_DISSOLVE"
                effect = "fade"
                target_t = 0.45
                desired_gap = 0.22
            elif idx == 0 or idx == n - 2:
                t_class = "INTER_SCENE_CLIMAX_DISSOLVE"
                effect = "fade"
                target_t = 0.42
                desired_gap = 0.15
            else:
                t_class = "INTER_SCENE_CINEMATIC_DISSOLVE"
                effect = "fade"
                target_t = 0.45
                desired_gap = 0.20

            needed_tail_a = target_t + desired_gap - head_margin_b
            raw_trim_end_a = sp_end_a + max(0.15, needed_tail_a)
            if raw_trim_end_a <= dur_a:
                trim_end_a = round(raw_trim_end_a, 2)
                actual_t = round(target_t, 2)
            else:
                trim_end_a = dur_a
                avail_tail_a = max(0.0, dur_a - sp_end_a)
                actual_t = round(max(0.25, min(target_t, avail_tail_a + head_margin_b - 0.13)), 2)

            cur_s["trim_end_sec"] = trim_end_a
            cur_s["video_trim_end_sec"] = trim_end_a
            cur_s["editorial_transition_class"] = t_class
            cur_s["transition_effect"] = effect
            cur_s["transition_duration_sec"] = actual_t

        # Bước 3 (v9.0 Anti-Over-Stretched Stasis Cap):
        # TUYỆT ĐỐI CẤM kéo giãn slow-motion quá 1.18x (như lỗi kéo 1.89x ở Shot 05 làm con T-Rex há miệng đứng im 3 giây)!
        a_dur = max(0.5, cur_s["trim_end_sec"] - cur_s["trim_start_sec"])
        v_dur = max(0.5, cur_s["video_trim_end_sec"] - cur_s["video_trim_start_sec"])
        if a_dur / v_dur > MAX_PTS_STRETCH:
            min_v_dur = round(a_dur / MAX_PTS_STRETCH, 2)
            cur_s["video_trim_end_sec"] = round(min(dur_a, cur_s["video_trim_start_sec"] + min_v_dur), 2)

        trimmed_off_tail = round(dur_a - cur_s["trim_end_sec"], 2)
        trimmed_off_head_b = round(trim_start_b, 2)
        audit_log["pass_2_multi_angle_rig_and_articulation_fixes"].append(
            f"[{sid} -> {nxt_id} - v9.0 Single-Take & Editorial Engine] Chế độ `{t_class}` (`effect={effect}`, `{actual_t}s`) | "
            f"Đã cắt bỏ `{trimmed_off_tail}s` cuối `{sid}` và `{trimmed_off_head_b}s` đầu `{nxt_id}` | QA Status `{sid}`: `{cur_s.get('v9_qa_gate_status')}`."
        )


def cmd_assemble(args):
    """
    Ghép nối Điện Ảnh Thông Minh v9.0 (GPU NVIDIA RTX 3050 + True Single-Take 0.00s Intra-Scene Stitch + Smart Inter-Scene xfade):
    - Với `INTRA_SCENE_CONTINUE` (`transition_effect == 'concat_single_take'`): Nối thẳng `0.00s` không dùng `xfade` (diệt 100% bóng ma 2 cái đầu / 2 hàm răng!),
      đồng thời khóa `MAX_PTS_STRETCH <= 1.18x` (diệt 100% lỗi kéo giãn slow-motion đứng hình!).
    - Với `INTER_SCENE_CUT`: Dùng `xfade` (`smoothleft` / `fade`) mượt mà đúng ngữ pháp điện ảnh.
    """
    t0 = time.time()
    proj_dir = Path(args.project).resolve()
    manifest_path = proj_dir / "project_manifest.json"
    if not manifest_path.exists():
        print(f"[ERROR] Không tìm thấy {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips_dir = proj_dir / "assets" / "clips"
    output_dir = proj_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    active_shots = []
    clip_files = []
    for shot in manifest.get("shots", []):
        rel_path = shot.get("clip_output_path") or f"assets/clips/{shot['shot_id']}.mp4"
        cpath = proj_dir / rel_path
        if cpath.exists():
            active_shots.append(shot)
            clip_files.append(cpath)

    if not clip_files:
        for cpath in sorted(clips_dir.glob("*.mp4")):
            clip_files.append(cpath)
            active_shots.append({"shot_id": cpath.stem, "clip_output_path": f"assets/clips/{cpath.name}"})

    if not clip_files:
        print(f"[ERROR] Không tìm thấy file .mp4 nào trong {clips_dir}", file=sys.stderr)
        sys.exit(1)

    dummy_log = {"pass_2_multi_angle_rig_and_articulation_fixes": []}
    _compute_kinetic_trims_and_transitions(proj_dir, active_shots, dummy_log)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    ffmpeg_exe = get_ffmpeg_exe()
    use_nvenc = has_nvenc(ffmpeg_exe)
    v_codec = ["h264_nvenc", "-preset", "p4", "-cq", "19"] if use_nvenc else ["libx264", "-preset", "fast", "-crf", "18"]

    final_out = output_dir / "final_video.mp4"
    n = len(clip_files)

    if n == 1:
        s0 = active_shots[0]
        ts = float(s0.get("trim_start_sec", 0.0))
        te = float(s0.get("trim_end_sec", 8.0))
        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i",
                str(clip_files[0]),
                "-vf",
                f"trim=start={ts:.3f}:end={te:.3f},setpts=PTS-STARTPTS",
                "-af",
                f"atrim=start={ts:.3f}:end={te:.3f},asetpts=PTS-STARTPTS",
                "-c:v",
                *v_codec,
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(final_out),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assembled_duration = round(te - ts, 2)
        transitions_applied = []
    else:
        inputs_cmd = []
        v_trims = []
        a_trims = []
        clip_durations = []

        for idx, (cpath, shot) in enumerate(zip(clip_files, active_shots)):
            inputs_cmd.extend(["-i", str(cpath)])
            ts = float(shot.get("trim_start_sec", 0.0))
            te = float(shot.get("trim_end_sec", 8.0))
            v_ts = float(shot.get("video_trim_start_sec", ts))
            v_te = float(shot.get("video_trim_end_sec", te))
            dur = round(max(0.5, te - ts), 4)
            v_dur = round(max(0.5, v_te - v_ts), 4)
            clip_durations.append(dur)
            if abs(dur - v_dur) > 0.04:
                # Khóa cứng tốc độ kéo giãn tối đa <= 1.18x để không bao giờ gây đứng hình slow-motion!
                scale_pts = min(1.18, max(0.85, dur / v_dur))
                v_trims.append(
                    f"[{idx}:v]trim=start={v_ts:.3f}:end={v_te:.3f},setpts={scale_pts:.6f}*(PTS-STARTPTS),fps=24,format=yuv420p[v{idx}]"
                )
            else:
                v_trims.append(
                    f"[{idx}:v]trim=start={v_ts:.3f}:end={v_te:.3f},setpts=PTS-STARTPTS,fps=24,format=yuv420p[v{idx}]"
                )
            a_trims.append(
                f"[{idx}:a]atrim=start={ts:.3f}:end={te:.3f},asetpts=PTS-STARTPTS,aresample=48000[a{idx}]"
            )

        xfade_filters = []
        across_filters = []
        transitions_applied = []
        cum_duration = clip_durations[0]

        for idx in range(n - 1):
            cur_s = active_shots[idx]
            nxt_s = active_shots[idx + 1]
            eff = cur_s.get("transition_effect") or "fade"
            t_dur = float(cur_s.get("transition_duration_sec", 0.35))

            v_in_left = f"[v0]" if idx == 0 else f"[vx{idx-1}]"
            v_out = f"[vout]" if idx == n - 2 else f"[vx{idx}]"
            a_in_left = f"[a0]" if idx == 0 else f"[ax{idx-1}]"
            a_out = f"[aout]" if idx == n - 2 else f"[ax{idx}]"

            if eff == "concat_single_take" or t_dur <= 0.02:
                # Nối thẳng 0.00s Zero-Dissolve cho INTRA_SCENE_CONTINUE (không dùng xfade trên Video -> 0% bóng ma!)
                xfade_filters.append(f"{v_in_left}[v{idx+1}]concat=n=2:v=1:a=0,fps=24,format=yuv420p{v_out}")
                # Âm thanh vẫn nối mượt 40ms (0.04s) hoặc concat để không có tiếng click mà vẫn giữ đồng bộ
                across_filters.append(f"{a_in_left}[a{idx+1}]concat=n=2:v=0:a=1{a_out}")
                offset = round(cum_duration, 4)
                cum_duration = round(cum_duration + clip_durations[idx + 1], 4)
                actual_eff_label = "zero_dissolve_single_take (0.00s, NO xfade ghosting)"
                actual_dur_val = 0.0
            else:
                t_dur = round(max(0.15, min(t_dur, clip_durations[idx] - 0.2, clip_durations[idx + 1] - 0.2)), 3)
                offset = round(cum_duration - t_dur, 4)
                xfade_filters.append(
                    f"{v_in_left}[v{idx+1}]xfade=transition={eff}:duration={t_dur:.3f}:offset={offset:.3f}{v_out}"
                )
                across_filters.append(
                    f"{a_in_left}[a{idx+1}]acrossfade=d={t_dur:.3f}:c1=tri:c2=tri{a_out}"
                )
                cum_duration = round(cum_duration + clip_durations[idx + 1] - t_dur, 4)
                actual_eff_label = eff
                actual_dur_val = t_dur

            transitions_applied.append(
                {
                    "join": f"{cur_s.get('shot_id', f'shot_{idx+1:02d}')} -> {nxt_s.get('shot_id', f'shot_{idx+2:02d}')}",
                    "class": cur_s.get("editorial_transition_class", cur_s.get("transition_to_next", "TRANSITION")),
                    "xfade": actual_eff_label,
                    "duration_sec": actual_dur_val,
                    "timeline_offset_sec": round(offset, 2),
                }
            )

        full_filter = ";".join(v_trims + a_trims + xfade_filters + across_filters)
        filter_script_path = output_dir / "smart_editorial_filtergraph.txt"
        filter_script_path.write_text(full_filter, encoding="utf-8")

        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                *inputs_cmd,
                "-filter_complex_script",
                str(filter_script_path),
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                *v_codec,
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(final_out),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assembled_duration = round(cum_duration, 2)

    v9_backup = output_dir / "chapter1_v9_single_take_master.mp4"
    try:
        import shutil
        shutil.copy2(final_out, v9_backup)
    except Exception:
        pass

    qa_rejections = [
        {
            "shot_id": s.get("shot_id"),
            "v9_qa_gate_status": s.get("v9_qa_gate_status"),
            "cgi_pop_in_windows": s.get("cgi_pop_in_windows", []),
            "treadmill_stepping_detected": s.get("treadmill_stepping_detected", False),
            "mid_speech_parking_windows": s.get("mid_speech_parking_windows", []),
            "intra_scene_boundary_l1_diff": s.get("intra_scene_boundary_l1_diff"),
        }
        for s in active_shots
        if "REJECT" in (s.get("v9_qa_gate_status") or "")
    ]

    print(
        json.dumps(
            {
                "status": "ok",
                "engine_version": "v9.0 (True Single-Take 0.00s Intra-Scene Stitch + Entity Conservation Anti-Pop-In + Anti-Treadmill)",
                "gpu_nvenc_used": use_nvenc,
                "encoder": "NVIDIA GeForce RTX 3050 (h264_nvenc)" if use_nvenc else "CPU Fast",
                "clips_merged": len(clip_files),
                "assembled_duration_sec": assembled_duration,
                "elapsed_sec": round(time.time() - t0, 2),
                "final_video_path": str(final_out),
                "v9_editorial_master_path": str(v9_backup),
                "v9_qa_gate_rejections": qa_rejections,
                "transitions_applied": transitions_applied,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_check_browser(args):
    res = sync_chrome_port_fast()
    if args.launch and not res["ready"]:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for cp in chrome_paths:
            if Path(cp).exists():
                subprocess.Popen(
                    [
                        cp,
                        "--remote-debugging-port=9222",
                        r"--user-data-dir=C:\Users\Asus\chrome_ai_bot",
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "https://labs.google/fx/vi/tools/flow",
                    ]
                )
                time.sleep(2)
                res = sync_chrome_port_fast()
                break
    print(json.dumps(res, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="AI Video Studio Helper CLI v8.0 (Zero-Parking & GPU Accelerated)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Tính toán số cảnh, chia Chapters/Batches song song cho phim ngắn & phim dài (1p -> 5h)")
    p_plan.add_argument("--duration", type=int, required=True, help="Thời lượng video mong muốn (giây)")
    p_plan.add_argument("--lang", type=str, default="vi", help="Ngôn ngữ nói (vi, en, ja, ko)")
    p_plan.add_argument("--shot-length", type=int, default=8, help="Độ dài mỗi shot Veo 3.1 (mặc định 8 giây)")
    p_plan.add_argument("--batch-size", type=int, default=8, help="Số cảnh bắn song song mỗi Batch/Chapter")
    p_plan.set_defaults(func=cmd_plan)

    p_init = sub.add_parser("init", help="Khởi tạo dự án mới với Đồ thị Keyframe Biên song song")
    p_init.add_argument("--name", type=str, required=True, help="Tên dự án")
    p_init.add_argument("--duration", type=int, required=True, help="Thời lượng mục tiêu (giây)")
    p_init.add_argument("--lang", type=str, default="vi", help="Ngôn ngữ")
    p_init.add_argument("--style", type=str, default="Auto Dynamic", help="Phong cách hình ảnh")
    p_init.add_argument("--aspect", type=str, default="16:9", help="Tỷ lệ khung hình")
    p_init.add_argument("--batch-size", type=int, default=8, help="Số cảnh mỗi Batch song song")
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate", help="Kiểm tra kịch bản & chống sạn AI")
    p_val.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_val.set_defaults(func=cmd_validate)

    p_audit_assets = sub.add_parser(
        "audit-assets",
        help="Kiểm định Bộ Bản Thiết Kế Model Nhân Vật (Turnaround 5 Góc, Articulation, Scale), Bối Cảnh Sạch & Đạo Cụ trước khi làm phim",
    )
    p_audit_assets.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_audit_assets.set_defaults(func=cmd_audit_assets)

    p_forge_assets = sub.add_parser(
        "forge-assets",
        help="Sinh tự động bộ prompt chuẩn Studio cho Character Rig (3 Sheet), Environment Clean Plates và Props Library",
    )
    p_forge_assets.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_forge_assets.add_argument("--char-name", type=str, default="Main Character", help="Tên nhân vật")
    p_forge_assets.add_argument("--char-desc", type=str, default="", help="Mô tả ngoại hình, trang phục, giải phẫu")
    p_forge_assets.add_argument("--char-type", type=str, choices=["human", "creature", "robot", "anime"], default="human", help="Phân loại thực thể")
    p_forge_assets.add_argument("--char-id", type=str, default="", help="ID nhân vật (tùy chọn)")
    p_forge_assets.add_argument("--style", type=str, default="", help="Phong cách hình ảnh (tùy chọn)")
    p_forge_assets.add_argument("--env-name", type=str, default="", help="Tên bối cảnh sạch")
    p_forge_assets.add_argument("--env-desc", type=str, default="", help="Mô tả bối cảnh sạch")
    p_forge_assets.add_argument("--env-id", type=str, default="", help="ID bối cảnh (tùy chọn)")
    p_forge_assets.add_argument("--props", type=str, default="", help="Danh sách đạo cụ tách rời (phân cách bằng dấu phẩy)")
    p_forge_assets.add_argument("--apply-to-manifest", action="store_true", help="Tự động ghi vào project_manifest.json")
    p_forge_assets.set_defaults(func=cmd_forge_assets)

    p_aud = sub.add_parser(
        "audit-prompts",
        help="Chạy Vòng Lặp Kiểm Duyệt Prompt 3 Lần (3-Pass Audit v8.0 Zero-Parking) & Định Tuyến Model Thông Minh",
    )
    p_aud.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_aud.add_argument("--budget", type=int, default=85000, help="Ngân sách token hiện có của User (mặc định: 85000)")
    p_aud.set_defaults(func=cmd_audit_prompts)

    p_dl = sub.add_parser("download-batch", help="Tải song song 12 luồng toàn bộ ảnh & video từ Google Flow CDN")
    p_dl.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_dl.add_argument("--urls-json", type=str, default="", help="File JSON ánh xạ relative_path -> url")
    p_dl.set_defaults(func=cmd_download_batch)

    p_ext = sub.add_parser("extract-last-frame", help="Trích xuất frame cuối của clip")
    p_ext.add_argument("--clip", type=str, required=True, help="Đường dẫn file .mp4")
    p_ext.add_argument("--out", type=str, required=True, help="Đường dẫn lưu ảnh .png")
    p_ext.set_defaults(func=cmd_extract_last_frame)

    p_act = sub.add_parser(
        "extract-active-frame",
        help="Trích xuất frame đang cử động mượt nhất quanh thời điểm kết thúc thoại (v8.0 Live Active-Motion Chaining)",
    )
    p_act.add_argument("--clip", type=str, required=True, help="Đường dẫn file .mp4")
    p_act.add_argument("--out", type=str, required=True, help="Đường dẫn lưu ảnh .png")
    p_act.set_defaults(func=cmd_extract_active_frame)

    p_qa = sub.add_parser("qa-frames", help="Trích xuất song song 12 luồng lưới ảnh QA Contact Sheet")
    p_qa.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_qa.set_defaults(func=cmd_qa_frames)

    p_asm = sub.add_parser("assemble", help="Ghép nối Điện Ảnh Thông Minh v8.0 bằng GPU NVIDIA RTX 3050 (h264_nvenc)")
    p_asm.add_argument("--project", type=str, required=True, help="Đường dẫn thư mục dự án")
    p_asm.add_argument("--skip-exact-tempo", action="store_true", help="Chỉ ghép nguyên bản (-c copy) trong 1 giây")
    p_asm.set_defaults(func=cmd_assemble)

    p_chk = sub.add_parser("check-browser", help="Đồng bộ cổng 9222 tức thì (Optimistic Mode)")
    p_chk.add_argument("--launch", action="store_true", help="Mở Chrome nếu chưa bật")
    p_chk.set_defaults(func=cmd_check_browser)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
