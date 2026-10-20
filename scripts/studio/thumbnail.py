"""Thumbnail 16:9 (YouTube) + 9:16 (Shorts/TikTok): chọn frame nét, tương phản tốt nhất trong các đoạn đã dựng, thêm tiêu đề."""

from pathlib import Path

from . import media

FONTS = ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]


def frame_score(frame) -> float:
    """Độ nét (phương sai Laplacian) × tương phản, phạt frame quá tối/quá sáng."""
    cv2 = media.cv2_module()
    g = cv2.cvtColor(cv2.resize(frame, (640, 360)), cv2.COLOR_BGR2GRAY)
    sharp = cv2.Laplacian(g, cv2.CV_64F).var()
    mean, std = float(g.mean()), float(g.std())
    exposure = 1.0 - min(1.0, abs(mean - 105) / 105)
    return (sharp ** 0.5) * (std / 64) * (0.3 + 0.7 * exposure)


def best_frame(segs: list, shot: str = None, at: float = None, per_seg: int = 4):
    if shot:
        seg = next((s for s in segs if s["shot_id"] == shot), None)
        if seg is None:
            raise media.MediaError(f"Shot {shot} không có trong timeline")
        t = at if at is not None else (seg["tin"] + seg["tout"]) / 2
        frame, _ = media.read_frame_at(seg["clip"], t)
        return frame, {"shot": shot, "t": round(t, 2)}
    best = (None, -1.0, None)
    for seg in segs:
        for k in range(per_seg):
            t = seg["tin"] + (seg["tout"] - seg["tin"]) * (k + 0.5) / per_seg
            frame, _ = media.read_frame_at(seg["clip"], t)
            if frame is None:
                continue
            sc = frame_score(frame)
            if sc > best[1]:
                best = (frame, sc, {"shot": seg["shot_id"], "t": round(t, 2), "score": round(sc, 2)})
    return best[0], best[2]


def _covers(path: str, text: str) -> bool:
    """Font có đủ glyph cho chữ (vd. Impact thiếu dấu tiếng Việt → hiện ô vuông)."""
    try:
        from fontTools.ttLib import TTFont

        cmap = TTFont(path, fontNumber=0, lazy=True).getBestCmap()
        return all(ord(ch) in cmap for ch in text if not ch.isspace())
    except ImportError:
        return text.isascii() or "impact" not in path.lower()


def _font(size, text=""):
    from PIL import ImageFont

    for f in FONTS:
        if Path(f).exists() and _covers(f, text):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def compose(img, size, title, subtitle="", focus_x=0.5):
    """Cắt khung theo tỷ lệ đích (giữ focus_x), tăng tương phản nhẹ, gradient tối đáy, chữ hoa có viền."""
    from PIL import Image, ImageDraw, ImageEnhance

    W, H = size
    src_w, src_h = img.size
    scale = max(W / src_w, H / src_h)
    img = img.resize((round(src_w * scale), round(src_h * scale)), Image.LANCZOS)
    x0 = int(min(max(0, img.width * focus_x - W / 2), img.width - W))
    y0 = (img.height - H) // 2
    img = img.crop((x0, y0, x0 + W, y0 + H))
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(1.08)
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(215 * max(0.0, (y / H - 0.45) / 0.55) ** 1.4))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), grad.resize((W, H)))
    d = ImageDraw.Draw(img)
    vertical = H > W
    fs = int((W * 0.115) if vertical else (H * 0.15))
    font = _font(fs, title.upper())
    lines = _wrap(d, title.upper(), font, W * 0.88)
    sub_font = _font(int(fs * 0.42), subtitle)
    block = len(lines) * fs * 1.08 + (fs * 0.7 if subtitle else 0)
    y = H * (0.80 if vertical else 0.93) - block
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=(255, 214, 90), stroke_width=max(3, fs // 14), stroke_fill=(0, 0, 0))
        y += fs * 1.08
    if subtitle:
        w = d.textlength(subtitle, font=sub_font)
        d.text(((W - w) / 2, y + fs * 0.12), subtitle, font=sub_font, fill=(240, 240, 240),
               stroke_width=max(2, fs // 28), stroke_fill=(0, 0, 0))
    return img


def make(segs: list, out_dir: Path, title: str, subtitle: str = "", shot: str = None, at: float = None) -> dict:
    from PIL import Image

    cv2 = media.cv2_module()
    frame, pick = best_frame(segs, shot, at)
    if frame is None:
        raise media.MediaError("Không đọc được frame nào cho thumbnail")
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    focus = next((s["shot"].get("crop_focus_x", 0.5) for s in segs if s["shot_id"] == pick["shot"]), 0.5)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, size in (("thumbnail.jpg", (1280, 720)), ("thumbnail_9x16.jpg", (1080, 1920))):
        p = out_dir / name
        compose(img, size, title, subtitle, focus).save(p, quality=92)
        paths[name] = str(p)
    return {"frame": pick, "files": paths}
