"""QA hai lớp.

Lớp 1 — kỹ thuật (đo được, đáng tin): độ phân giải, fps, thời lượng, letterbox/pillarbox,
đứng hình, frame đen, audio thiếu/câm/clipping.

Lớp 2 — thị giác (Gemini Vision): so contact sheet của clip với ảnh tham chiếu nhân vật và prompt
theo checklist (danh tính, bám prompt, lỗi giải phẫu, vật thể tự mọc, chữ/watermark...).
Không có API key thì xuất "gói QA" (ảnh + checklist) để Agent/người duyệt bằng mắt.

Lưu ý: không dùng heuristic pixel để "đoán" lỗi nội dung (pop-in, treadmill...) vì cho kết quả
PASS giả — đó là việc của lớp 2.
"""

import json
import time
import os
from pathlib import Path

from . import manifest as mf
from . import media

SAMPLE_RATIOS = (0.06, 0.35, 0.65, 0.94)


def _edge_band(rows_luma, thr) -> int:
    """Số hàng liên tiếp từ mép có độ sáng < thr."""
    n = 0
    for v in rows_luma:
        if v < thr:
            n += 1
        else:
            break
    return n


def detect_bars(frames, thr: float) -> dict:
    """Đo dải đen cố định ở 4 mép (letterbox / pillarbox) trên các frame mẫu."""
    import numpy as np

    if not frames:
        return {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}
    stack = np.stack(frames).astype(np.float32)
    # Lấy max theo thời gian: dải đen thật phải tối ở MỌI frame.
    mx = stack.max(axis=0)
    h, w = mx.shape
    rows, cols = mx.mean(axis=1), mx.mean(axis=0)
    return {
        "top": _edge_band(rows, thr) / h,
        "bottom": _edge_band(rows[::-1], thr) / h,
        "left": _edge_band(cols, thr) / w,
        "right": _edge_band(cols[::-1], thr) / w,
    }


def _runs(mask, fps, min_sec):
    """Các đoạn liên tục True dài ≥ min_sec → list (t_start, t_end)."""
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if (i - start) / fps >= min_sec:
                out.append((round(start / fps, 2), round(i / fps, 2)))
            start = None
    return out


def technical_qa(clip: Path, cfg: dict) -> dict:
    import numpy as np

    q = cfg["qa"]
    out_cfg = cfg["output"]
    findings = []

    def add(level, code, msg):
        findings.append({"level": level, "code": code, "msg": msg})

    info = media.probe(clip)
    if not info["has_video"]:
        add("reject", "NO_VIDEO", "File không có luồng video.")
        return {"info": info, "findings": findings, "verdict": "fail"}

    if info["height"] < out_cfg["height"] * 0.99 and info["width"] < out_cfg["width"] * 0.99:
        add("warn", "LOW_RESOLUTION", f"{info['width']}x{info['height']} < đầu ra {out_cfg['width']}x{out_cfg['height']}. Tải bản 1080p/upscale từ Flow thay vì để ffmpeg phóng to.")
    if info["fps"] and abs(info["fps"] - out_cfg["fps"]) > 0.05:
        add("info", "FPS_MISMATCH", f"{info['fps']} fps ≠ {out_cfg['fps']} fps đầu ra (sẽ chuyển đổi khi dựng).")
    if info["duration"] < q["min_duration_sec"]:
        add("warn", "SHORT_CLIP", f"Clip chỉ {info['duration']:.2f}s.")

    fps, frames = media.read_gray_frames(clip, size=(320, 180))
    if frames:
        sample_idx = np.linspace(0, len(frames) - 1, num=min(16, len(frames))).astype(int)
        bars = detect_bars([frames[i] for i in sample_idx], q["letterbox_luma"])
        lb = max(bars["top"], bars["bottom"])
        pb = max(bars["left"], bars["right"])
        if lb >= q["letterbox_min_ratio"]:
            add("reject", "LETTERBOX", f"Dải đen trên/dưới {bars['top']:.0%}/{bars['bottom']:.0%} chiều cao — sai tỷ lệ khung (kiểm tra aspect của start frame).")
        if pb >= q["letterbox_min_ratio"]:
            add("reject", "PILLARBOX", f"Dải đen trái/phải {bars['left']:.0%}/{bars['right']:.0%} chiều rộng — sai tỷ lệ khung.")

        # Đứng hình = gần như KHÔNG pixel nào đổi (camera trôi chậm vẫn đổi nhiều pixel nhỏ).
        changed = np.array([1.0] + [float(np.mean(np.abs(frames[i].astype(np.int16) - frames[i - 1].astype(np.int16))
                                                  > q["freeze_pixel_diff"]))
                                    for i in range(1, len(frames))])
        freezes = _runs(changed < q["freeze_changed_ratio"], fps, q["freeze_sec"])
        if freezes:
            add("warn", "FREEZE", f"Hình gần như đứng yên tại {freezes} (kiểm tra có phải chủ ý không).")
        means = np.array([float(f.mean()) for f in frames])
        blacks = _runs(means < q["black_luma"], fps, 0.4)
        if blacks:
            add("warn", "BLACK_FRAMES", f"Frame đen tại {blacks}.")

    if not info["has_audio"]:
        add("warn", "NO_AUDIO", "Clip không có audio.")
    else:
        pcm = media.read_pcm(clip, sr=16000)
        if pcm.size:
            peak = float(np.max(np.abs(pcm)))
            rms_db = 20 * np.log10(float(np.sqrt(np.mean(pcm ** 2))) + 1e-9)
            if rms_db < q["silence_dbfs"]:
                add("warn", "SILENT_AUDIO", f"Audio gần như câm ({rms_db:.1f} dBFS).")
            if peak >= 0.999:
                add("warn", "AUDIO_CLIPPING", "Audio chạm 0 dBFS (méo/clipping).")

    levels = {f["level"] for f in findings}
    verdict = "fail" if "reject" in levels else ("warn" if "warn" in levels else "pass")
    return {"info": info, "findings": findings, "verdict": verdict}


def contact_sheet(clip: Path, out_img: Path, label: str = "") -> Path:
    """Lưới 2x2 frame mẫu kèm nhãn thời gian."""
    import numpy as np

    cv2 = media.cv2_module()
    info = media.probe(clip)
    cells = []
    for r in SAMPLE_RATIOS:
        frame, t = media.read_frame_at(clip, info["duration"] * r)
        h, w = frame.shape[:2]
        frame = cv2.resize(frame, (640, int(640 * h / max(1, w))))
        text = f"{label or clip.stem} | t={t:.1f}s"
        cv2.rectangle(frame, (8, 8), (16 + 11 * len(text), 40), (0, 0, 0), -1)
        cv2.putText(frame, text, (14, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cells.append(frame)
    hmax = max(c.shape[0] for c in cells)
    cells = [cv2.copyMakeBorder(c, 0, hmax - c.shape[0], 0, 0, cv2.BORDER_CONSTANT) for c in cells]
    grid = np.vstack([np.hstack(cells[:2]), np.hstack(cells[2:])])
    out_img.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_img), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    return out_img


VISION_CHECKLIST = """Bạn là giám sát VFX/QC cho phim. Ảnh 1 là contact sheet 4 frame của một clip AI (Veo 3.1).
Các ảnh tiếp theo (nếu có) là ẢNH THAM CHIẾU CHUẨN của nhân vật/bối cảnh.

Prompt đã dùng:
<<<{prompt}>>>

Chấm khắt khe theo checklist và CHỈ trả về JSON đúng schema:
{{
  "identity_match": [{{"subject": "<id>", "score_1_10": int, "issues": "<khác biệt màu, hình khối, chi tiết nhận dạng>"}}],
  "prompt_adherence": {{"camera_ok": bool, "action_ok": bool, "setting_ok": bool, "notes": "<...>"}},
  "artifacts": {{"extra_or_missing_limbs": bool, "morphing": bool, "objects_popping_in": bool,
                 "text_or_watermark": bool, "letterbox": bool, "physics_errors": bool, "notes": "<...>"}},
  "continuity_with_previous": "<nhận xét nếu có ảnh shot trước, ngược lại 'n/a'>",
  "overall_score_1_10": int,
  "verdict": "pass" | "retake",
  "retake_advice": "<sửa prompt / đổi chế độ / đổi ảnh tham chiếu cụ thể thế nào>"
}}
Subjects cần kiểm tra danh tính: {subjects}."""


def _reference_images(proj_dir: Path, project: dict, shot: dict) -> list:
    rels = mf.shot_reference_paths(project, shot, proj_dir=proj_dir, limit=4, include_env=True)
    return [proj_dir / p for p in rels]


# Biến môi trường do các AI agent đặt khi chạy lệnh (Claude Code: CLAUDECODE / AI_AGENT).
# Agent khác (vd. Antigravity) chưa xác minh được biến nào → dùng --reviewer agent hoặc STUDIO_REVIEWER=agent.
AGENT_ENV_HINTS = ("CLAUDECODE", "AI_AGENT")
REVIEWER_MODES = ("auto", "agent", "api", "manual")


def detect_reviewer(cfg: dict, override: str = None) -> dict:
    """Ai chấm QA thị giác: agent đang chat (không tốn API) > Gemini API (khi chạy độc lập) > người duyệt."""
    mode = (override or os.environ.get("STUDIO_REVIEWER") or cfg.get("reviewer", {}).get("mode") or "auto").lower()
    if mode not in REVIEWER_MODES:
        raise ValueError(f"reviewer '{mode}' không hợp lệ ({', '.join(REVIEWER_MODES)})")
    agent = os.environ.get("AI_AGENT") or ("claude-code" if os.environ.get("CLAUDECODE") else "")
    if mode == "auto":
        if any(os.environ.get(k) for k in AGENT_ENV_HINTS):
            return {"mode": "agent", "agent": agent, "reason": "đang chạy trong AI agent"}
        ok, why = vision_available()
        if ok:
            return {"mode": "api", "agent": "", "reason": "chạy độc lập, có API key"}
        return {"mode": "manual", "agent": "", "reason": f"chạy độc lập, không có API ({why})"}
    return {"mode": mode, "agent": agent if mode == "agent" else "", "reason": "chỉ định thủ công"}


def validate_vision_result(data: dict) -> list:
    """Kiểm tra kết quả QA thị giác (từ API hoặc agent) theo schema VISION_CHECKLIST."""
    errors = []
    if data.get("verdict") not in ("pass", "retake"):
        errors.append("verdict phải là 'pass' hoặc 'retake'")
    score = data.get("overall_score_1_10")
    if not isinstance(score, int) or not 1 <= score <= 10:
        errors.append("overall_score_1_10 phải là số nguyên 1–10")
    if not isinstance(data.get("identity_match", []), list):
        errors.append("identity_match phải là list")
    if data.get("verdict") == "retake" and not data.get("retake_advice"):
        errors.append("verdict=retake cần retake_advice")
    return errors


def vision_available() -> tuple:
    try:
        from google import genai  # noqa: F401
    except ImportError:
        return False, "chưa cài google-genai"
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        return False, "chưa đặt GEMINI_API_KEY"
    return True, ""


def build_vision_packet(proj_dir: Path, project: dict, shot: dict, sheet: Path) -> dict:
    refs = _reference_images(proj_dir, project, shot)
    prompt = VISION_CHECKLIST.format(prompt=shot.get("veo_prompt", ""), subjects=", ".join(shot.get("subjects", [])) or "không có")
    return {"contact_sheet": sheet, "references": refs, "prompt": prompt}


def run_vision_qa(packet: dict, cfg: dict) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client()
    parts = [types.Part.from_bytes(data=Path(packet["contact_sheet"]).read_bytes(), mime_type="image/jpeg")]
    for ref in packet["references"]:
        mime = "image/png" if ref.suffix.lower() == ".png" else "image/jpeg"
        parts.append(types.Part.from_bytes(data=ref.read_bytes(), mime_type=mime))
    parts.append(packet["prompt"])
    gen_cfg = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
    models = [cfg["models"]["gemini_vision_qa"], *cfg["models"].get("gemini_vision_qa_fallbacks", [])]
    last_err = None
    for model in dict.fromkeys(models):
        for attempt in range(4):
            try:
                resp = client.models.generate_content(model=model, contents=parts, config=gen_cfg)
                result = json.loads(resp.text)
                result["_model"] = model
                return result
            except Exception as e:  # noqa: BLE001
                last_err, msg = e, str(e)
                if "limit: 0" in msg:  # model không có trong hạn mức (vd. bậc miễn phí) → sang model dự phòng
                    break
                if " 503 " in f" {msg[:4]} " or "UNAVAILABLE" in msg or "429" in msg[:4]:
                    time.sleep(10 * (attempt + 1))  # quá tải / giới hạn theo phút → chờ rồi thử lại
                    continue
                raise
    raise last_err


def write_packet(packet: dict, out_md: Path, result_path: Path) -> Path:
    """Gói QA để agent/người duyệt: ảnh cần xem (đường dẫn tuyệt đối), checklist, nơi ghi kết quả."""
    rel = lambda p: os.path.relpath(p, out_md.parent).replace("\\", "/")  # noqa: E731
    lines = [f"# Gói QA thị giác — {out_md.stem}", "",
             "Ảnh cần xem (ảnh 1 = contact sheet của clip, các ảnh sau = tham chiếu chuẩn):", "",
             f"1. `{Path(packet['contact_sheet']).resolve()}`"]
    lines += [f"{i}. `{Path(r).resolve()}`" for i, r in enumerate(packet["references"], start=2)]
    lines += ["", f"![contact sheet]({rel(packet['contact_sheet'])})", ""]
    lines += [f"![ref]({rel(r)})" for r in packet["references"]]
    lines += ["", "## Checklist", "", "```text", packet["prompt"], "```", "",
              f"Ghi JSON kết quả vào: `{result_path.resolve()}` rồi chạy `qa-vision-submit`.", ""]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md
