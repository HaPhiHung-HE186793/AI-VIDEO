"""QA từng take và tự chọn take tốt nhất cho mỗi shot.

Luồng: take_sheet (8 frame có mốc giờ) → reviewer (agent / Gemini API / người) trả JSON theo TAKE_CHECKLIST
(điểm + danh sách lỗi có khoảng thời gian) → choose_take: loại take hỏng kỹ thuật, tìm cửa sổ sạch dài nhất
tránh lỗi "major", đủ dài cho lời dẫn, chấm điểm và chọn → đặt edit_in/edit_out. Không take nào đạt → needs_retake.
"""

import json
from pathlib import Path

from . import audio as au
from . import manifest as mf
from . import media

SEVERITIES = ("major", "minor")

DEFAULT_RUBRIC = [
    {"id": "identity", "check": "Chủ thể khớp ảnh tham chiếu (màu, hoa văn, tỷ lệ, chi tiết nhận dạng)."},
    {"id": "anatomy", "check": "Không thừa/thiếu chi, không biến dạng hình khối, không tan chảy/biến hình."},
    {"id": "objects", "check": "Không có vật thể tự mọc ra/biến mất giữa khung; không chữ, watermark, viền đen."},
    {"id": "prompt", "check": "Đúng cỡ cảnh, chuyển động máy và hành động mô tả trong prompt."},
]

TAKE_CHECKLIST = """Bạn là giám sát VFX/QC. Ảnh 1 là contact sheet {n} frame của MỘT take video AI, mỗi ô ghi mốc giờ t=…s.
Các ảnh sau (nếu có) là ẢNH THAM CHIẾU CHUẨN của nhân vật. Clip dài {dur:.1f}s.

Prompt đã dùng:
<<<{prompt}>>>

Tiêu chí bắt buộc (vi phạm = lỗi):
{rubric}

Ghi MỌI vi phạm thấy được kèm khoảng thời gian ước lượng từ mốc giờ trên ảnh (ô trước–ô sau quanh chỗ lỗi).
severity: "major" = không dùng được đoạn đó; "minor" = thấy được nhưng chấp nhận nếu không có take tốt hơn.
CHỈ trả JSON:
{{
  "identity_score_1_10": int,
  "prompt_adherence_1_10": int,
  "aesthetic_1_10": int,
  "defects": [{{"rule": "<id tiêu chí>", "severity": "major"|"minor", "t_from": float, "t_to": float, "note": "<...>"}}],
  "overall_score_1_10": int,
  "verdict": "pass" | "retake",
  "notes": "<nhận xét ngắn, gợi ý sửa prompt nếu retake>"
}}"""


def rubric_for(project: dict, cfg: dict) -> list:
    extra = project.get("qa_rubric") or []
    ids = {r["id"] for r in extra}
    return [r for r in DEFAULT_RUBRIC if r["id"] not in ids] + extra


def take_sheet(clip: Path, out_img: Path, n: int = 8) -> dict:
    """Contact sheet n frame (2 hàng) có mốc giờ — đủ dày để khoanh vùng lỗi theo thời gian."""
    import numpy as np

    cv2 = media.cv2_module()
    dur = media.probe(clip)["duration"]
    times = [round(dur * (i + 0.5) / n, 2) for i in range(n)]
    cells = []
    for t in times:
        frame, real_t = media.read_frame_at(clip, t)
        frame = cv2.resize(frame, (480, int(480 * frame.shape[0] / frame.shape[1])))
        label = f"t={real_t:.1f}s"
        cv2.rectangle(frame, (6, 6), (14 + 13 * len(label), 36), (0, 0, 0), -1)
        cv2.putText(frame, label, (10, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cells.append(frame)
    h = max(c.shape[0] for c in cells)
    cells = [cv2.copyMakeBorder(c, 0, h - c.shape[0], 0, 0, cv2.BORDER_CONSTANT) for c in cells]
    half = (len(cells) + 1) // 2
    while len(cells) < 2 * half:
        cells.append(np.zeros_like(cells[0]))
    grid = np.vstack([np.hstack(cells[:half]), np.hstack(cells[half:])])
    out_img.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_img), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    return {"sheet": out_img, "duration": dur, "times": times}


def take_paths(proj: Path, shot_id: str, take_no: int) -> dict:
    base = Path(proj) / "assets" / "qa" / "takes" / f"{shot_id}_take{take_no:02d}"
    return {"sheet": base.with_suffix(".jpg"), "packet": base.with_suffix(".md"), "result": base.with_suffix(".json")}


def build_continuity_sheets(proj: Path, shots: list, batch_size: int = 4) -> list:
    """Ghép contact sheet của 4–5 shot liên tiếp thành 1 bảng tổng quan (`continuity_batch_XX.jpg`).

    Giúp Agent / Đạo diễn vừa giảm 75% lượt mở ảnh, vừa kiểm tra được tính liên tục ánh sáng, màu sắc,
    vị trí nhân vật (quy tắc 180°) và đạo cụ giữa các shot liền kề.
    """
    import numpy as np

    cv2 = media.cv2_module()
    proj = Path(proj)
    entries = []
    for s in shots:
        takes = s.get("takes") or []
        if not takes:
            continue
        sel = s.get("selected_take") or takes[-1]["take"]
        sp = take_paths(proj, s["shot_id"], sel)["sheet"]
        if sp.exists():
            entries.append((f"{s['shot_id']} (take {sel})", sp))
    if len(entries) < 2:
        return []
    out_paths = []
    out_dir = proj / "assets" / "qa" / "takes"
    out_dir.mkdir(parents=True, exist_ok=True)
    target_w = 1280
    for b_idx in range(0, len(entries), batch_size):
        chunk = entries[b_idx: b_idx + batch_size]
        strips = []
        for label, sp in chunk:
            im = cv2.imread(str(sp))
            if im is None:
                continue
            h_new = max(120, int(target_w * im.shape[0] / im.shape[1]))
            im = cv2.resize(im, (target_w, h_new))
            banner = np.zeros((32, target_w, 3), dtype=np.uint8)
            cv2.putText(banner, label, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            strips.append(np.vstack([banner, im]))
        if strips:
            out_file = out_dir / f"continuity_batch_{b_idx // batch_size + 1:02d}.jpg"
            cv2.imwrite(str(out_file), np.vstack(strips), [int(cv2.IMWRITE_JPEG_QUALITY), 86])
            out_paths.append(str(out_file.resolve()))
    return out_paths


def build_take_prompt(project: dict, shot: dict, cfg: dict, n: int, dur: float) -> str:
    rubric = "\n".join(f"- {r['id']}: {r['check']}" for r in rubric_for(project, cfg))
    return TAKE_CHECKLIST.format(n=n, dur=dur, prompt=shot.get("veo_prompt", ""), rubric=rubric)


def validate_take_result(data: dict, duration: float = None) -> list:
    errs = []
    for k in ("identity_score_1_10", "prompt_adherence_1_10", "overall_score_1_10"):
        v = data.get(k)
        if not isinstance(v, int) or not 1 <= v <= 10:
            errs.append(f"{k} phải là số nguyên 1–10")
    if data.get("verdict") not in ("pass", "retake"):
        errs.append("verdict phải là pass | retake")
    defects = data.get("defects", [])
    if not isinstance(defects, list):
        errs.append("defects phải là list")
        defects = []
    for i, d in enumerate(defects):
        if d.get("severity") not in SEVERITIES:
            errs.append(f"defects[{i}].severity phải là major | minor")
        try:
            a, b = float(d.get("t_from")), float(d.get("t_to"))
            if a > b or a < 0 or (duration and a > duration + 0.5):
                errs.append(f"defects[{i}] khoảng thời gian không hợp lệ")
        except (TypeError, ValueError):
            errs.append(f"defects[{i}] thiếu t_from/t_to")
    return errs


def detect_rubber_stamp(vision_results: list, min_batch: int = 5) -> list:
    """Phát hiện gian lận QA thị giác (rubber-stamping): chấm hàng loạt cùng bộ điểm, 0 lỗi và câu notes rập khuôn.

    vision_results: danh sách dict kết quả vision QA. Trả về danh sách cảnh báo/lỗi (rỗng nếu bình thường).
    """
    import difflib
    import re
    from collections import Counter

    if len(vision_results) < min_batch:
        return []
    issues = []
    n = len(vision_results)

    tuples = [
        (
            v.get("identity_score_1_10"),
            v.get("prompt_adherence_1_10"),
            v.get("aesthetic_1_10"),
            v.get("overall_score_1_10"),
            len(v.get("defects") or []),
        )
        for v in vision_results
    ]
    top_tuple, top_count = Counter(tuples).most_common(1)[0]
    if top_count / n >= 0.80 and top_tuple[4] == 0:
        issues.append(
            f"RUBBER_STAMP_SCORES: {top_count}/{n} take có cùng bộ điểm {top_tuple[:4]} và 0 lỗi (defects=[]) — "
            "dấu hiệu điền điểm tự động không qua kiểm tra từng contact sheet."
        )

    def _norm_note(s: str) -> str:
        s = re.sub(r"\b(shot[_\s]*\d+|take[_\s]*\d+|c\d+[_\s]*\d+)\b", "<ID>", (s or "").lower())
        return re.sub(r"\s+", " ", s).strip()

    notes = [_norm_note(v.get("notes", "")) for v in vision_results if v.get("notes")]
    if len(notes) >= min_batch:
        anchor = Counter(notes).most_common(1)[0][0]
        similar = sum(1 for x in notes if x == anchor or difflib.SequenceMatcher(None, anchor, x).ratio() >= 0.85)
        if similar / len(notes) >= 0.75:
            issues.append(
                f"RUBBER_STAMP_NOTES: {similar}/{len(notes)} take có nhận xét (notes) rập khuôn theo cùng 1 mẫu câu."
            )
    return issues


def clean_windows(duration: float, defects: list, severities=("major",), pad: float = 0.25) -> list:
    """Các khoảng [a, b] không giao với lỗi thuộc `severities` (nới mỗi lỗi thêm `pad` giây hai phía)."""
    bad = sorted((max(0.0, float(d["t_from"]) - pad), min(duration, float(d["t_to"]) + pad))
                 for d in defects if d.get("severity") in severities)
    windows, cur = [], 0.0
    for a, b in bad:
        if a > cur:
            windows.append((round(cur, 2), round(a, 2)))
        cur = max(cur, b)
    if cur < duration:
        windows.append((round(cur, 2), round(duration, 2)))
    return [w for w in windows if w[1] - w[0] > 0.05]


def needed_seconds(proj: Path, shot: dict, cfg: dict, project: dict = None) -> float:
    """Độ dài hình tối thiểu shot cần: phần chia của beat / đủ cho lời dẫn riêng / độ dài shot ưa thích."""
    from . import beats as bt

    ed = cfg["editorial"]
    vo = shot.get("voiceover_path")
    if vo and (Path(proj) / vo).exists():
        return round(float(shot.get("vo_offset", ed["vo_pre_roll_sec"])) + au.wav_duration(Path(proj) / vo)
                     + ed["vo_post_roll_sec"], 2)
    if project and shot.get("beat") in bt.beats_by_id(project):
        return bt.shot_need(proj, project, shot, cfg)
    return float(ed.get("preferred_shot_sec", 4.0))


def score_take(q: dict) -> float:
    minors = sum(1 for d in q.get("defects", []) if d.get("severity") == "minor")
    return (q["overall_score_1_10"] + 0.5 * q["identity_score_1_10"] + 0.3 * q["prompt_adherence_1_10"]
            + 0.2 * q.get("aesthetic_1_10", q["overall_score_1_10"]) - 0.7 * minors)


def choose_take(shot: dict, need_sec: float, cfg: dict, pref: float = None, chain_next: bool = False) -> dict:
    """Quyết định take + cửa sổ cắt. Trả về {take, edit_in, edit_out, score, reason} hoặc {retake: True, reasons}.

    pref: độ dài cắt mong muốn (mặc định preferred_shot_sec; shot trong beat dùng đúng phần chia của beat).
    chain_next: True nếu shot kế tiếp có `chain_from_prev=True` (nối từ frame cuối của shot này).
    """
    pref = float(pref if pref is not None else cfg["editorial"].get("preferred_shot_sec", 4.0))
    chain_prev = bool(shot.get("chain_from_prev"))
    candidates, reasons = [], []
    for t in shot.get("takes", []):
        q = t.get("qa") or {}
        tag = f"take{t['take']}"
        if t.get("rejected"):
            reasons.append(f"{tag}: bị loại thủ công")
            continue
        if not q.get("vision"):
            reasons.append(f"{tag}: chưa QA thị giác")
            continue
        if q.get("technical", {}).get("verdict") == "fail":
            reasons.append(f"{tag}: lỗi kỹ thuật")
            continue
        v, dur = q["vision"], q.get("duration") or 8.0
        wins = clean_windows(dur, v.get("defects", []))
        best = max(wins, key=lambda w: w[1] - w[0], default=None)
        if not best or best[1] - best[0] < need_sec:
            reasons.append(f"{tag}: đoạn sạch dài nhất {0 if not best else best[1] - best[0]:.1f}s < cần {need_sec:.1f}s")
            continue
        length = min(best[1] - best[0], max(need_sec, pref))
        if chain_prev and chain_next and best[0] <= 0.25 and best[1] >= dur - 0.25:
            a, b = round(best[0], 2), round(best[1], 2)
        elif chain_next and best[1] >= dur - 0.25:
            # Shot nối tiếp bắt đầu từ frame cuối của shot này -> neo cửa sổ sát cuối để khớp Daisy-Chain.
            b = round(best[1], 2)
            a = round(max(best[0], b - length), 2)
        elif chain_prev and best[0] <= 0.25:
            # Shot này bắt đầu từ frame cuối của shot trước -> neo cửa sổ sát đầu (0.0s) để nối không vết cắt.
            a = round(best[0], 2)
            b = round(min(best[1], a + length), 2)
        else:
            # Đặt cửa sổ ở giữa đoạn sạch: tránh khựng đầu clip và đoạn "đỗ" cuối clip của Veo.
            a = round(best[0] + (best[1] - best[0] - length) / 2, 2)
            b = round(a + length, 2)
        score = score_take(v) + (0.5 if v.get("verdict") == "pass" else -2.0)
        candidates.append({"take": t["take"], "edit_in": a, "edit_out": b, "score": round(score, 2),
                           "window": best})
    if not candidates:
        return {"retake": True, "reasons": reasons}
    best = max(candidates, key=lambda c: c["score"])
    best["reason"] = f"điểm {best['score']} (cao nhất / {len(candidates)} take đạt)"
    best["alternatives"] = [c["take"] for c in candidates if c is not best]
    best["rejected_reasons"] = reasons
    return best


def ensure_take_qa(take: dict) -> dict:
    return take.setdefault("qa", {})


def load_result(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def shots_with_takes(project: dict, only: str = "") -> list:
    return [s for s in mf.ordered_shots(project) if s.get("takes") and (not only or s["shot_id"] in only.split(","))]


def visual_signature(clip: Path, times=(2.5, 5.5)) -> list:
    """Chữ ký hình của clip tại vài mốc giờ (64x36 xám, chuẩn hóa): nhận ra cùng một clip ở độ phân giải khác."""
    import numpy as np

    cv2 = media.cv2_module()
    sig = []
    for t in times:
        frame, _ = media.read_frame_at(clip, t)
        g = cv2.cvtColor(cv2.resize(frame, (64, 36)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        sig.append(((g - g.mean()) / (g.std() + 1e-6)).ravel())
    return sig


def signature_similarity(a: list, b: list) -> float:
    return float(min(x @ y / len(x) for x, y in zip(a, b)))


def first_frame_match(clip: Path, image: Path) -> float:
    """Tương quan giữa frame đầu của clip và ảnh frame mở đầu của shot (clip tạo từ frame này: ~0.9–1.0)."""
    import numpy as np

    cv2 = media.cv2_module()
    frame, _ = media.read_frame_at(clip, 0.0)
    img = cv2.imread(str(image))
    if frame is None or img is None:
        return 0.0
    f = lambda x: (lambda g: ((g - g.mean()) / (g.std() + 1e-6)).ravel())(  # noqa: E731
        cv2.cvtColor(cv2.resize(x, (64, 36)), cv2.COLOR_BGR2GRAY).astype(np.float32))
    a, b = f(frame), f(img)
    return float(a @ b / len(a))
