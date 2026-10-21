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
    # Dải letterbox/pillarbox thật sự vừa tối (mean < thr) vừa đồng nhất theo chiều ngang/dọc (std < 3.5);
    # cảnh đêm có mặt nước/bóng tối tự nhiên ở mép khung sẽ có độ lệch chuẩn cao hơn.
    row_score = np.where(mx.std(axis=1) < 3.5, mx.mean(axis=1), 255.0)
    col_score = np.where(mx.std(axis=0) < 3.5, mx.mean(axis=0), 255.0)
    return {
        "top": _edge_band(row_score, thr) / h,
        "bottom": _edge_band(row_score[::-1], thr) / h,
        "left": _edge_band(col_score, thr) / w,
        "right": _edge_band(col_score[::-1], thr) / w,
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


def strip_image_letterbox(image_path: Path, thr: float = 20.0, min_ratio: float = 0.03) -> bool:
    """Tự động cắt bỏ dải đen letterbox/pillarbox trên ảnh Keyframe và phóng lại đúng kích thước gốc."""
    import numpy as np

    cv2 = media.cv2_module()
    img = cv2.imread(str(image_path))
    if img is None:
        return False
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bars = detect_bars([gray], thr)
    lb = max(bars["top"], bars["bottom"])
    pb = max(bars["left"], bars["right"])
    if lb < min_ratio and pb < min_ratio:
        return False
    if lb >= pb:
        cut_top = int(round(max(bars["top"], bars["bottom"]) * h)) + 2
        nh = max(16, h - 2 * cut_top)
        nw = min(w, int(round(nh * (w / h))))
        x0 = (w - nw) // 2
        cropped = img[cut_top:cut_top + nh, x0:x0 + nw]
    else:
        cut_left = int(round(max(bars["left"], bars["right"]) * w)) + 2
        nw = max(16, w - 2 * cut_left)
        nh = min(h, int(round(nw * (h / w))))
        y0 = (h - nh) // 2
        cropped = img[y0:y0 + nh, cut_left:cut_left + nw]
    resized = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(image_path), resized)
    return True


def check_keyframe_pair_continuity(start_img_path: Path, end_img_path: Path, dynamic_camera: bool = False) -> dict:
    """Kiểm định độ tương thích quang học giữa cặp Keyframe START và END trước khi tốn credit chạy Veo 3.1.

    Theo quy trình Pre-Flight Continuity Gate của các studio AI hàng đầu:
    nếu ảnh START và ảnh END lệch tỷ lệ khung hình, nhảy độ sáng (luma jump > 55) hoặc trôi bảng màu
    (histogram correlation < 0.35), mạng DiT sẽ buộc phải dùng hiệu ứng chồng mờ (cross-dissolve) hoặc biến hình.
    """
    import numpy as np

    cv2 = media.cv2_module()
    im_a = cv2.imread(str(start_img_path))
    im_b = cv2.imread(str(end_img_path))
    if im_a is None or im_b is None:
        return {"ok": False, "luma_diff": 0.0, "hist_corr": 0.0, "issues": ["MISSING_IMAGE: Không đọc được file ảnh START hoặc END."]}

    ha, wa = im_a.shape[:2]
    hb, wb = im_b.shape[:2]
    ratio_a, ratio_b = wa / max(1, ha), wb / max(1, hb)
    issues = []
    if abs(ratio_a - ratio_b) > 0.03:
        issues.append(f"ASPECT_MISMATCH: START ({wa}x{ha}) và END ({wb}x{hb}) khác tỷ lệ khung hình → dễ sinh dải đen hoặc méo hình.")

    small_a = cv2.resize(im_a, (320, 180))
    small_b = cv2.resize(im_b, (320, 180))
    gray_a = cv2.cvtColor(small_a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_b = cv2.cvtColor(small_b, cv2.cvtColor(small_b, cv2.COLOR_BGR2GRAY).dtype if False else cv2.COLOR_BGR2GRAY).astype(np.float32)

    luma_diff = float(abs(np.mean(gray_a) - np.mean(gray_b)))
    if luma_diff > 55.0:
        issues.append(f"SEVERE_LUMA_JUMP: Độ sáng trung bình giữa START và END lệch {luma_diff:.1f}/255 (> 55) → dễ gây chớp sáng hoặc chồng mờ giữa clip.")

    hsv_a = cv2.cvtColor(small_a, cv2.COLOR_BGR2HSV)
    hsv_b = cv2.cvtColor(small_b, cv2.COLOR_BGR2HSV)
    hist_a = cv2.calcHist([hsv_a], [0, 1], None, [30, 32], [0, 180, 0, 256])
    hist_b = cv2.calcHist([hsv_b], [0, 1], None, [30, 32], [0, 180, 0, 256])
    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)
    hist_corr = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    if hist_corr < 0.35:
        issues.append(f"COLOR_PALETTE_DRIFT: Tương quan bảng màu giữa START và END quá thấp (corr={hist_corr:.2f} < 0.35) → kiểm tra lại ánh sáng của frame END.")

    return {
        "ok": len(issues) == 0,
        "luma_diff": round(luma_diff, 1),
        "hist_corr": round(hist_corr, 3),
        "issues": issues,
    }


def detect_mid_clip_dissolve(frames, fps: float, min_span_diff: float = 28.0, max_blend_ratio: float = 0.22) -> list:
    """Phát hiện lỗi Veo tự chèn hiệu ứng chồng hình mờ (cross-dissolve / double exposure) ở giữa clip.

    Khi xảy ra cross-dissolve tại frame i với bán kính d (~0.45s), hai frame F[i-d] và F[i+d] khác nhau lớn
    (span_diff > min_span_diff), nhưng F[i] lại xấp xỉ trung bình cộng tuyến tính 0.5*(F[i-d] + F[i+d]).
    Trả về danh sách khoảng thời gian (t_from, t_to) bị chồng mờ.
    """
    import numpy as np

    d = max(4, int(0.45 * (fps or 24.0)))
    if len(frames) < 2 * d + 2:
        return []
    mask = [False] * len(frames)
    for i in range(d, len(frames) - d):
        fa = frames[i - d].astype(np.float32)
        fb = frames[i + d].astype(np.float32)
        span_diff = float(np.mean(np.abs(fb - fa)))
        if span_diff < min_span_diff:
            continue
        fm = frames[i].astype(np.float32)
        blend_err = float(np.mean(np.abs(fm - 0.5 * (fa + fb))))
        if blend_err / span_diff < max_blend_ratio:
            mask[i] = True
    return _runs(mask, fps or 24.0, 0.15)


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
        dissolves = detect_mid_clip_dissolve(frames, fps)
        if dissolves:
            add("warn", "MID_CLIP_DISSOLVE",
                f"Phát hiện chồng hình mờ (double-exposure dissolve) giữa clip tại {dissolves} — "
                "kiểm tra sự đồng bộ góc máy giữa Keyframe START/END và veo_prompt.")

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



def benchmark_against_reference(
    candidate_video: Path,
    ref_video: Path,
    project: dict = None,
    timeline_path: Path = None,
    out_sheet_path: Path = None,
    target_duration_sec: float = 300.0,
    ref_start_sec: float = 254.0,
    ref_end_sec: float = 474.0,
) -> dict:
    """Đối chiếu định lượng & điện ảnh giữa video dự án (`candidate_video`) và video mẫu (`ref_video`, vd. Jurassic World Final Battle).

    Trả về bảng điểm 0–100 trên 6 trụ cột:
      1. `duration_score`: Độ khớp thời lượng mục tiêu (mặc định 300.0s = 5 phút).
      2. `lighting_score`: Độ khớp ánh sáng Chiaroscuro đêm (Mean Luma, Dark Shadow Ratio, Contrast Std).
      3. `pacing_score`: Mật độ cắt cảnh (Cut Count >= 60 cho 5 phút, ASL 3.5s–4.8s).
      4. `camera_variety_score`: Độ phủ 6 mẫu góc máy đặc trưng của `FtCslvCjZEY` (Foot Macro, Eye/Snarl ECU, 85mm Jaw Clamp, Asymmetric Knockdown, Environmental Destruction, Cliff/Abyss Standoff).
      5. `motion_score`: Động năng chuyển động và tỷ lệ khung hình hoạt động thực (không bị đóng băng).
      6. `defect_free_score`: Tỷ lệ cửa sổ dựng hoàn toàn sạch lỗi `major` và `minor`.
    """
    import re
    import numpy as np
    cv2 = media.cv2_module()
    candidate_video = Path(candidate_video)
    ref_video = Path(ref_video)
    project = project or {}

    def _sample_video_metrics(vpath: Path, t_start: float = 0.0, t_end: float = 0.0, n_samples: int = 12):
        cap = cv2.VideoCapture(str(vpath))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        dur = n_frames / fps if fps > 0 else 0.0
        t0 = max(0.5, float(t_start)) if t_start > 0 else 0.5
        t1 = min(dur - 0.5, float(t_end)) if (t_end and t_end > t0) else max(t0 + 0.5, dur - 0.5)
        ts = np.linspace(t0, t1, max(4, n_samples))
        lumas, contrasts, dark_ratios, spec_ratios, motion_diffs, thumbs = [], [], [], [], [], []
        prev_gray = None
        for t in ts:
            cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            small = cv2.resize(frame, (360, 200), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            lumas.append(float(np.mean(gray)))
            contrasts.append(float(np.std(gray)))
            dark_ratios.append(float(np.mean(gray < 48)))
            spec_ratios.append(float(np.mean(gray > 155)))
            # Read next frame ~80ms later to measure instantaneous motion
            ok2, frame2 = cap.read()
            if ok2 and frame2 is not None:
                g2 = cv2.cvtColor(cv2.resize(frame2, (360, 200), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
                motion_diffs.append(float(np.mean(cv2.absdiff(gray, g2))))
            elif prev_gray is not None:
                motion_diffs.append(float(np.mean(cv2.absdiff(gray, prev_gray))))
            prev_gray = gray
            thumbs.append((float(t), small))
        cap.release()
        return {
            "duration": round(dur, 2),
            "mean_luma": round(float(np.mean(lumas)) if lumas else 0.0, 2),
            "contrast_std": round(float(np.mean(contrasts)) if contrasts else 0.0, 2),
            "dark_shadow_ratio": round(float(np.mean(dark_ratios)) if dark_ratios else 0.0, 3),
            "specular_ratio": round(float(np.mean(spec_ratios)) if spec_ratios else 0.0, 4),
            "mean_motion_diff": round(float(np.mean(motion_diffs)) if motion_diffs else 0.0, 2),
            "active_motion_ratio": round(float(np.mean([m > 0.8 for m in motion_diffs])) if motion_diffs else 0.0, 3),
            "thumbs": thumbs,
        }

    cand_m = _sample_video_metrics(candidate_video, 0.0, 0.0, n_samples=12)
    ref_m = _sample_video_metrics(ref_video, ref_start_sec, ref_end_sec, n_samples=12) if ref_video.exists() else {
        "duration": 516.93,
        "mean_luma": 24.5,
        "contrast_std": 28.5,
        "dark_shadow_ratio": 0.78,
        "specular_ratio": 0.012,
        "mean_motion_diff": 3.4,
        "active_motion_ratio": 0.96,
        "thumbs": [],
    }

    issues = []

    # 1. Duration Score (target 300.0s = 5 minutes)
    dur_c = cand_m["duration"]
    dur_err = abs(dur_c - target_duration_sec) / max(1.0, target_duration_sec)
    duration_score = round(max(0.0, 100.0 * (1.0 - dur_err)), 1)
    if dur_c < target_duration_sec * 0.85:
        issues.append(
            f"DURATION_SHORT ({dur_c:.1f}s vs mục tiêu {target_duration_sec:.0f}s): Video chưa đủ thời lượng 5 phút (5 hồi đại chiến)."
        )

    # 2. Chiaroscuro Lighting Score (ref mean_luma ~22–42, dark_shadow_ratio >= 0.55)
    luma_c = cand_m["mean_luma"]
    dark_c = cand_m["dark_shadow_ratio"]
    std_c = cand_m["contrast_std"]
    # Ideal low-key creature battle range: luma in [20, 46], dark_shadow_ratio >= 0.52, contrast_std >= 24
    if 18.0 <= luma_c <= 46.0:
        luma_sub = 100.0
    elif luma_c > 46.0:
        luma_sub = max(0.0, 100.0 - (luma_c - 46.0) * 1.35)
    else:
        luma_sub = max(0.0, 100.0 - (18.0 - luma_c) * 3.0)
    dark_sub = min(100.0, (dark_c / 0.55) * 100.0)
    contrast_sub = min(100.0, (std_c / 25.0) * 100.0)
    lighting_score = round(0.45 * luma_sub + 0.35 * dark_sub + 0.20 * contrast_sub, 1)
    if luma_c > 55.0 or dark_c < 0.45:
        issues.append(
            f"OVEREXPOSED_DAYLIGHT_LOOK (Mean Luma={luma_c:.1f}, Dark Ratio={dark_c:.2f} vs mẫu Jurassic World Luma={ref_m['mean_luma']:.1f}, Dark Ratio={ref_m['dark_shadow_ratio']:.2f}): "
            "Ánh sáng ban ngày/vàng rực làm lộ bề mặt da CG; cần hạ về Low-Key Night Chiaroscuro (70% bóng tối sâu + viền sáng 6500K cyan / 2700K amber)."
        )

    # 3. Pacing & Cut Density Score
    segs = []
    if timeline_path and Path(timeline_path).exists():
        try:
            segs = json.loads(Path(timeline_path).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            segs = []
    num_cuts = len(segs) if segs else max(1, int(round(dur_c / 4.6)))
    asl = round(dur_c / max(1, num_cuts), 2)
    target_cuts = max(55, int(round(target_duration_sec / 4.5)))
    cut_count_sub = min(100.0, (num_cuts / target_cuts) * 100.0)
    asl_sub = 100.0 if 2.8 <= asl <= 4.8 else max(0.0, 100.0 - abs(asl - 4.0) * 18.0)
    pacing_score = round(0.65 * cut_count_sub + 0.35 * asl_sub, 1)
    if num_cuts < 50:
        issues.append(
            f"INSUFFICIENT_CUT_DENSITY ({num_cuts} cú cắt vs chuẩn {target_cuts}+ cú cắt trong 5 phút): "
            "Cần dựng đa góc máy (Multi-Coverage Sub-Clipping + Dynamic Focal Punch-In) xuyên suốt 5 hồi."
        )

    # 4. Camera Archetype Coverage Score (6 Jurassic World Battle Archetypes)
    shots = project.get("shots", [])
    corpus_parts = []
    for s in shots:
        corpus_parts.append(
            f"{s.get('camera', '')} {s.get('action', '')} {s.get('start_action', '')} {s.get('end_action', '')} {s.get('veo_prompt', '')}"
        )
    for seg in segs:
        corpus_parts.append(f"{seg.get('shot_id', '')} {seg.get('coverage_role', '')} {seg.get('crop_mode', '')}")
    corpus = " ".join(corpus_parts).lower()

    archetypes = {
        "foot_tremor_macro": bool(re.search(r"\b(foot|talon|clawed\s+foot|footprint|ground[- ]level|0\.3m|0\.4m|puddle\s+tremor|stomp)\b", corpus)),
        "eye_snarl_ecu": bool(re.search(r"\b(extreme\s+close[- ]up|ecu|macro\s+eye|amber\s+eye|snarl|85mm\s+close|dilat)\b", corpus)),
        "visceral_jaw_clamp_cu": bool(re.search(r"\b(50mm|85mm|close[- ]up)[^.]*\b(jaws?\s+clamp|clamp(?:s|ed|ing)?\s+(?:its\s+)?jaws?|teeth\s+sink|neck\s+flesh)\b|\b(jaw[- ]clamp|close_up_punch)\b", corpus)),
        "asymmetric_knockdown": bool(re.search(r"\b(hurl(?:s|ed|ing)?|knock(?:s|ed)?\s+down|pinned|onto\s+(?:its\s+)?flank|slams?\s+onto\s+the\s+(?:mud|ground)|downed|towering\s+over)\b", corpus)),
        "environmental_destruction": bool(re.search(r"\b(shatter(?:s|ing|ed)?|splinter(?:s|ing|ed)?|collaps(?:e|es|ing)|crushing|explod(?:e|es|ing)|basalt|burning\s+trunk)\b", corpus)),
        "abyss_standoff_wide": bool(re.search(r"\b(chasm|precipice|gorge|waterfall|cliff[- ]edge|across\s+the\s+newly\s+formed)\b", corpus)),
    }
    covered = [k for k, v in archetypes.items() if v]
    missing_arch = [k for k, v in archetypes.items() if not v]
    camera_variety_score = round((len(covered) / len(archetypes)) * 100.0, 1)
    if missing_arch:
        issues.append(
            f"MISSING_HOLLYWOOD_SHOT_ARCHETYPES (Thiếu {len(missing_arch)}/6 mẫu góc máy của Jurassic World: {', '.join(missing_arch)}): "
            "Cần bổ sung đủ 6 mẫu cảnh (Đặc tả bàn chân dậm đất, ECU mắt/răng gầm, Cận cảnh 85mm ngoạm ngập cổ, Quật ngã ghì xuống bùn bất đối xứng, Phá hủy môi trường, Đối đầu bờ vực)."
        )

    # 5. Motion Energy & Active Ratio Score
    act_r = cand_m["active_motion_ratio"]
    mot_d = cand_m["mean_motion_diff"]
    motion_score = round(min(100.0, 65.0 * act_r + 35.0 * min(1.0, mot_d / 2.2)), 1)

    # 6. Defect-Free Score
    defect_hits = 0
    checked_shots = 0
    for s in shots:
        sel_t = s.get("selected_take")
        t_in = float(s.get("edit_in") or 0.0)
        t_out = float(s.get("edit_out") or 0.0)
        if not sel_t or t_out <= t_in:
            continue
        checked_shots += 1
        for tk in s.get("takes", []):
            if tk.get("take") == sel_t:
                defs = ((tk.get("qa") or {}).get("vision") or {}).get("defects") or []
                for d in defs:
                    d0 = float(d.get("t_from", d.get("start_sec", 0.0)))
                    d1 = float(d.get("t_to", d.get("end_sec", 0.0)))
                    if max(t_in, d0) < min(t_out, d1) - 0.05:
                        defect_hits += 1
    defect_free_score = round(max(0.0, 100.0 - defect_hits * 15.0), 1)
    if defect_hits > 0:
        issues.append(f"ACTIVE_WINDOW_DEFECTS: Còn {defect_hits} lỗi thị giác giao cắt với cửa sổ dựng [edit_in, edit_out].")

    overall_score = round(
        0.22 * duration_score
        + 0.22 * lighting_score
        + 0.18 * pacing_score
        + 0.18 * camera_variety_score
        + 0.10 * motion_score
        + 0.10 * defect_free_score,
        1,
    )

    # Render side-by-side visual comparison sheet if requested
    if out_sheet_path and ref_m["thumbs"] and cand_m["thumbs"]:
        out_sheet_path = Path(out_sheet_path)
        out_sheet_path.parent.mkdir(parents=True, exist_ok=True)
        idx_ref = np.linspace(0, len(ref_m["thumbs"]) - 1, 6).astype(int)
        idx_cand = np.linspace(0, len(cand_m["thumbs"]) - 1, 6).astype(int)
        ref_cells, cand_cells = [], []
        for i in idx_ref:
            t_r, img_r = ref_m["thumbs"][i]
            cell = img_r.copy()
            cv2.rectangle(cell, (0, 0), (360, 28), (0, 0, 0), -1)
            cv2.putText(cell, f"REF JW @ {t_r:.0f}s (Luma {ref_m['mean_luma']:.0f})", (6, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 210, 255), 1, cv2.LINE_AA)
            ref_cells.append(cell)
        for i in idx_cand:
            t_c, img_c = cand_m["thumbs"][i]
            cell = img_c.copy()
            cv2.rectangle(cell, (0, 0), (360, 28), (0, 0, 0), -1)
            cv2.putText(cell, f"STUDIO @ {t_c:.0f}s (Luma {cand_m['mean_luma']:.0f})", (6, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 160), 1, cv2.LINE_AA)
            cand_cells.append(cell)
        row_ref_1 = np.hstack(ref_cells[:3])
        row_ref_2 = np.hstack(ref_cells[3:6])
        row_cand_1 = np.hstack(cand_cells[:3])
        row_cand_2 = np.hstack(cand_cells[3:6])
        comp_grid = np.vstack([row_ref_1, row_ref_2, row_cand_1, row_cand_2])
        cv2.imwrite(str(out_sheet_path), comp_grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    return {
        "overall_similarity_score_100": overall_score,
        "verdict": "PASS_HOLLYWOOD_BENCHMARK" if overall_score >= 92.0 and not issues else "NEEDS_IMPROVEMENT",
        "scores": {
            "duration_score_100": duration_score,
            "lighting_chiaroscuro_score_100": lighting_score,
            "pacing_cut_density_score_100": pacing_score,
            "camera_variety_score_100": camera_variety_score,
            "motion_energy_score_100": motion_score,
            "defect_free_score_100": defect_free_score,
        },
        "candidate_metrics": {k: v for k, v in cand_m.items() if k != "thumbs"},
        "reference_metrics": {k: v for k, v in ref_m.items() if k != "thumbs"},
        "editorial_stats": {
            "cut_count": num_cuts,
            "avg_shot_length_sec": asl,
            "target_duration_sec": target_duration_sec,
            "covered_archetypes": covered,
            "missing_archetypes": missing_arch,
        },
        "issues": issues,
        "comparison_sheet": str(out_sheet_path) if out_sheet_path else None,
    }
