"""Bộ đăng kênh: tiêu đề / mô tả / tag / chương / ghi chú công bố AI cho YouTube (16:9) và Shorts/TikTok (9:16).

Nội dung "trí tuệ" (tiêu đề, mô tả) do agent viết vào `manifest.publish`; module này chỉ dựng bản nháp khi thiếu,
kiểm tra giới hạn nền tảng và gom đường dẫn file cần tải lên.
"""

from pathlib import Path

LIMITS = {"title": 100, "description": 5000, "tags_total": 500}
AI_NOTE = {"en": "Visuals and narration were created with generative AI (Google Veo 3.1, Nano Banana, Gemini TTS). "
                 "Scientific details follow current palaeontology but are dramatised.",
           "vi": "Hình ảnh và lời dẫn được tạo bằng AI (Google Veo 3.1, Nano Banana, Gemini TTS). "
                 "Chi tiết khoa học theo cổ sinh vật học hiện nay nhưng được kịch tính hóa."}


def hashtag(tag: str) -> str:
    """'T. rex' → '#TRex' (hashtag chỉ gồm chữ/số)."""
    import re

    words = re.findall(r"[^\W_]+", tag)
    return "#" + "".join(w[:1].upper() + w[1:] for w in words)


def fmt_ts(sec: float) -> str:
    s = int(round(sec))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def chapters(segs: list, project: dict) -> list:
    """Chương YouTube theo beat — chỉ hợp lệ khi ≥ 3 chương, chương đầu 0:00, mỗi chương ≥ 10 s."""
    from . import beats as bt

    by_id = bt.beats_by_id(project)
    out = []
    for s in segs:
        bid = s["shot"].get("beat")
        if bid and (not out or out[-1]["beat"] != bid):
            out.append({"beat": bid, "t": s["timeline_start"],
                        "label": by_id.get(bid, {}).get("chapter_title") or by_id.get(bid, {}).get("purpose", bid)})
    total = segs[-1]["timeline_start"] + segs[-1]["duration"] if segs else 0
    ends = [c["t"] for c in out[1:]] + [total]
    ok = len(out) >= 3 and out[0]["t"] < 0.5 and all(e - c["t"] >= 10 for c, e in zip(out, ends))
    return out if ok else []


def check(entry: dict) -> list:
    errs = []
    if len(entry.get("title", "")) > LIMITS["title"]:
        errs.append(f"title {len(entry['title'])} > {LIMITS['title']} ký tự")
    if len(entry.get("description", "")) > LIMITS["description"]:
        errs.append("description quá 5000 ký tự")
    if sum(len(t) + 1 for t in entry.get("tags", [])) > LIMITS["tags_total"]:
        errs.append("tổng tag > 500 ký tự")
    if any(c in entry.get("title", "") for c in "<>"):
        errs.append("title chứa < hoặc > (YouTube từ chối)")
    return errs


def build(segs: list, project: dict, out_dir: Path) -> dict:
    lang = project.get("language", "en")
    pub = project.get("publish") or {}
    beats = sorted(project.get("beats", []), key=lambda b: b.get("order", 0))
    hook = beats[0]["narration"] if beats else ""
    base_title = pub.get("title") or project.get("title") or project.get("project_name", "")
    tags = pub.get("tags", [])
    note = pub.get("ai_disclosure") or AI_NOTE.get(lang, AI_NOTE["en"])
    chs = chapters(segs, project)
    desc = pub.get("description") or hook
    if chs:
        desc += "\n\n" + "\n".join(f"{fmt_ts(c['t'])} {c['label']}" for c in chs)
    desc += "\n\n" + note
    if tags:
        desc += "\n\n" + " ".join(hashtag(t) for t in tags[:3])
    out_dir = Path(out_dir)
    youtube = {"title": base_title, "description": desc, "tags": tags, "chapters": bool(chs),
               "files": {"video": pub.get("video_landscape"), "subtitles": "output/subtitles.srt",
                         "thumbnail": "output/thumbnail.jpg"},
               "checklist": ["Bật 'Altered or synthetic content' (nội dung tạo bằng AI) khi tải lên",
                             f"Ngôn ngữ video: {lang}; tải phụ đề .srt", "Made for kids: No"]}
    s_title = pub.get("shorts_title") or base_title
    if "#shorts" not in s_title.lower() and len(s_title) + 8 <= LIMITS["title"]:
        s_title += " #Shorts"
    shorts = {"title": s_title, "description": (pub.get("shorts_description") or hook) + "\n\n" + note,
              "tags": tags, "files": {"video": pub.get("video_vertical"), "cover": "output/thumbnail_9x16.jpg"},
              "checklist": ["Phụ đề đã in cứng", "Bật nhãn nội dung AI (YouTube / TikTok 'AI-generated')"]}
    res = {"youtube": youtube, "shorts": shorts,
           "warnings": {k: check(v) for k, v in (("youtube", youtube), ("shorts", shorts)) if check(v)},
           "drafted": [k for k in ("title", "description", "tags") if not pub.get(k)]}
    md = [f"# Đăng kênh — {base_title}", ""]
    for name, e in (("YouTube (16:9)", youtube), ("Shorts / TikTok (9:16)", shorts)):
        md += [f"## {name}", "", "**Tiêu đề**", "", "```", e["title"], "```", "", "**Mô tả**", "", "```", e["description"], "```", ""]
        if e["tags"]:
            md += ["**Tag**", "", "```", ", ".join(e["tags"]), "```", ""]
        md += ["**File**", ""] + [f"- {k}: `{v}`" for k, v in e["files"].items() if v] + ["", "**Trước khi bấm Đăng**", ""]
        md += [f"- [ ] {c}" for c in e["checklist"]] + [""]
    (out_dir / "publish.md").write_text("\n".join(md), encoding="utf-8")
    res["publish_md"] = str(out_dir / "publish.md")
    return res
