"""Cổng duyệt storyboard (0 credit): người dùng duyệt ảnh mở đầu + lời dẫn theo beat TRƯỚC khi tạo video.

`storyboard` xuất output/storyboard.html (+ ảnh tổng hợp .jpg) và ghi manifest["storyboard"] = {status, hash}.
`storyboard-approve` đặt status=approved với hash nội dung hiện tại. Sửa beat/shot sau khi duyệt → hash đổi →
flow-generate --kind video bị chặn tới khi duyệt lại.
"""

import hashlib
import html
import json
import os
from datetime import datetime
from pathlib import Path

from . import beats as bt
from . import manifest as mf
from . import media

HASH_FIELDS = ("beat", "order", "camera", "action", "subjects", "first_frame_path", "last_frame_path", "generation_mode", "veo_prompt")


def content_hash(project: dict) -> str:
    beats = [{k: b.get(k) for k in ("beat_id", "order", "narration", "j_cut_sec")} for b in bt.ordered_beats(project)]
    shots = [{k: s.get(k) for k in HASH_FIELDS} for s in mf.ordered_shots(project) if not s.get("exclude_from_edit")]
    return hashlib.sha256(json.dumps([beats, shots], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def approval_state(project: dict) -> dict:
    sb = project.get("storyboard") or {}
    current = content_hash(project)
    return {"status": sb.get("status", "none"), "approved_hash": sb.get("approved_hash"), "current_hash": current,
            "valid": sb.get("status") == "approved" and sb.get("approved_hash") == current}


def _frame_for(proj: Path, s: dict) -> list:
    paths = []
    if s.get("first_frame_path") and (proj / s["first_frame_path"]).exists():
        paths.append(proj / s["first_frame_path"])
    if s.get("last_frame_path") and (proj / s["last_frame_path"]).exists():
        lp = proj / s["last_frame_path"]
        if lp not in paths:
            paths.append(lp)
    for c in s.get("frame_candidates", []):
        p = proj / c["path"]
        if p.exists() and p not in paths:
            paths.append(p)
    return paths[:3]


def groups(project: dict) -> list:
    """[(beat | None, [shots])] theo thứ tự xuất hiện; shot không thuộc beat thành nhóm riêng."""
    beats = bt.beats_by_id(project)
    out, cur = [], None
    for s in mf.ordered_shots(project):
        if s.get("exclude_from_edit"):
            continue
        b = beats.get(s.get("beat"))
        key = b["beat_id"] if b else f"_{s['shot_id']}"
        if not cur or cur[0] != key:
            cur = (key, b, [])
            out.append(cur)
        cur[2].append(s)
    return [(b, shots) for _, b, shots in out]


def build(proj: Path, project: dict, cfg: dict, credits_per_shot: int) -> dict:
    proj = Path(proj)
    mf.resolve_chained_keyframes(project, proj)
    out_dir = proj / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "storyboard.html"
    rel = lambda p: os.path.relpath(p, out_dir).replace("\\", "/")  # noqa: E731
    rows, n_shots, missing = [], 0, []
    for b, shots in groups(project):
        title = (f"{b['beat_id']} · {html.escape(b.get('purpose', ''))}" if b else f"{shots[0]['shot_id']} (không thuộc beat)")
        narration = (b.get("narration") if b else mf.shot_audio(shots[0]).get("line")) or ""
        jcut = f" · J-cut {b['j_cut_sec']}s" if b and b.get("j_cut_sec") else ""
        cells = []
        for s in shots:
            n_shots += 1
            frames = _frame_for(proj, s)
            if not frames and s.get("generation_mode") in ("first_frame", "first_last"):
                missing.append(s["shot_id"])
            imgs = "".join(f'<img src="{rel(f)}" alt="{s["shot_id"]}">' for f in frames) or '<div class="noimg">chưa có frame</div>'
            cells.append(f'<div class="shot"><div class="imgs">{imgs}</div><b>{s["shot_id"]}</b> · {html.escape(s.get("camera", ""))}'
                         f'<p>{html.escape(s.get("action", ""))}</p></div>')
        rows.append(f'<section><h2>{title}{jcut}</h2><blockquote>{html.escape(narration)}</blockquote>'
                    f'<div class="row">{"".join(cells)}</div></section>')
    state = approval_state(project)
    to_make = [s for _, ss in groups(project) for s in ss if not s.get("selected_take")]
    est = len(to_make) * credits_per_shot  # shot đã có take được chọn (dùng lại) không tốn thêm
    doc = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard</title><style>
:root{{--bg:#fff;--fg:#1a1a1a;--muted:#666;--card:#f4f4f2}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141414;--fg:#eee;--muted:#999;--card:#1f1f1f}}}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:16px;max-width:1200px;margin:auto}}
section{{background:var(--card);border-radius:10px;padding:12px 16px;margin:14px 0}}
h2{{font-size:16px;margin:4px 0}} blockquote{{margin:6px 0 10px;font-style:italic;color:var(--muted)}}
.row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.shot img{{width:100%;border-radius:6px;display:block;margin-bottom:4px}} .shot p{{margin:4px 0;font-size:13px;color:var(--muted)}}
.noimg{{height:140px;display:grid;place-items:center;border:1px dashed var(--muted);border-radius:6px;color:var(--muted)}}
</style></head><body>
<h1>Storyboard — {html.escape(project.get('project_name', proj.name))}</h1>
<p>{len(rows)} nhịp · {n_shots} shot ({len(to_make)} cần tạo mới) · ước tính video: <b>{est} credit</b> · trạng thái: <b>{state['status']}</b>
 · tạo lúc {datetime.now():%Y-%m-%d %H:%M}</p>
{''.join(rows)}
</body></html>"""
    page.write_text(doc, encoding="utf-8")
    sheet = _contact(proj, project, out_dir / "storyboard.jpg")
    project["storyboard"] = {**(project.get("storyboard") or {}), "status": "approved" if state["valid"] else "pending",
                             "built_hash": state["current_hash"], "built_at": datetime.now().isoformat(timespec="seconds")}
    return {"html": str(page), "contact_sheet": str(sheet) if sheet else None, "beats": len(rows), "shots": n_shots,
            "shots_to_generate": [s["shot_id"] for s in to_make],
            "estimated_video_credits": est, "missing_frames": missing, "approval": approval_state(project)}


def _contact(proj: Path, project: dict, out: Path):
    """Ảnh tổng hợp: mỗi hàng 1 beat (frame đầu từng shot + nhãn) — để agent/người xem nhanh."""
    import numpy as np

    cv2 = media.cv2_module()
    rows = []
    for b, shots in groups(project):
        cells = []
        for s in shots:
            fr = _frame_for(proj, s)
            im = cv2.imread(str(fr[0])) if fr else None
            im = cv2.resize(im, (384, 216)) if im is not None else np.full((216, 384, 3), 40, np.uint8)
            label = f"{b['beat_id'] if b else ''} {s['shot_id']}".strip()
            cv2.rectangle(im, (0, 0), (12 + 11 * len(label), 26), (0, 0, 0), -1)
            cv2.putText(im, label, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
            cells.append(im)
        while len(cells) < 4:
            cells.append(np.zeros((216, 384, 3), np.uint8))
        rows.append(np.hstack(cells[:4]))
    if not rows:
        return None
    cv2.imwrite(str(out), np.vstack(rows), [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return out
