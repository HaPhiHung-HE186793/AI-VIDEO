"""Tạo LUT màu (.cube) bằng code — 0 đồng, dùng với `assemble --lut`.

Preset "documentary": S-curve tương phản nhẹ, bóng đổ hơi lạnh / vùng sáng hơi ấm (split-tone), giảm nhẹ độ bão hòa
của màu xanh lá quá rực (cây cối AI hay bị "neon"), giữ trung tính da/vảy. Cường độ `strength` 0–1 trộn với ảnh gốc.
"""

from pathlib import Path

PRESETS = {
    "documentary": {"contrast": 0.18, "shadow_tint": (-0.010, 0.000, 0.018), "high_tint": (0.020, 0.008, -0.016),
                    "sat": 0.94, "green_sat": 0.85},
    "warm_dawn": {"contrast": 0.14, "shadow_tint": (0.000, -0.004, 0.012), "high_tint": (0.030, 0.012, -0.022),
                  "sat": 1.0, "green_sat": 0.9},
    "blockbuster": {"contrast": 0.26, "shadow_tint": (-0.018, -0.004, 0.028), "high_tint": (0.032, 0.010, -0.024),
                    "sat": 0.96, "green_sat": 0.72},
    "cyberpunk_neon": {"contrast": 0.28, "shadow_tint": (-0.024, 0.006, 0.036), "high_tint": (0.034, -0.006, 0.022),
                       "sat": 1.08, "green_sat": 0.78},
    "noir_thriller": {"contrast": 0.30, "shadow_tint": (-0.014, -0.002, 0.020), "high_tint": (0.008, 0.006, -0.008),
                      "sat": 0.72, "green_sat": 0.65},
    "romance_pastel": {"contrast": 0.08, "shadow_tint": (0.006, 0.002, 0.010), "high_tint": (0.026, 0.014, -0.012),
                       "sat": 0.98, "green_sat": 0.92},
    "wuxia_jade": {"contrast": 0.22, "shadow_tint": (-0.016, 0.008, 0.016), "high_tint": (0.028, 0.014, -0.018),
                   "sat": 0.95, "green_sat": 0.82},
    "anime_vibrant": {"contrast": 0.20, "shadow_tint": (-0.006, -0.002, 0.016), "high_tint": (0.018, 0.008, -0.010),
                      "sat": 1.12, "green_sat": 1.0},
    "ilm_night_battle": {
        "gamma": 1.78,
        "exposure": 0.68,
        "contrast": 0.34,
        "shadow_tint": (-0.030, -0.004, 0.038),
        "high_tint": (0.036, 0.010, -0.018),
        "sat": 0.82,
        "green_sat": 0.42,
    },
}

GENRE_TO_LUT = {
    "action_blockbuster": "blockbuster",
    "wuxia_xianxia": "wuxia_jade",
    "cyberpunk_scifi": "cyberpunk_neon",
    "horror_thriller": "noir_thriller",
    "romance_kdrama": "romance_pastel",
    "anime_2d_3d": "anime_vibrant",
    "sitcom_podcast": "warm_dawn",
    "nature_documentary": "documentary",
    "commercial_product": "blockbuster",
    "historical_epic": "wuxia_jade",
}


def auto_preset_for_genre(genre: str) -> str:
    return GENRE_TO_LUT.get((genre or "").strip().lower(), "documentary")


def transform(rgb, preset: str = "documentary", strength: float = 1.0):
    """rgb: mảng (..., 3) giá trị 0–1 → đã chỉnh màu."""
    import numpy as np

    p = PRESETS[preset]
    x = np.clip(rgb, 0, 1)
    if p.get("gamma") or p.get("exposure"):
        x = np.clip((x ** float(p.get("gamma", 1.0))) * float(p.get("exposure", 1.0)), 0, 1)
    # S-curve quanh 0.5 (giữ đen/trắng tại chỗ)
    s = x + p["contrast"] * (x - 0.5) * (1 - np.abs(2 * x - 1))
    luma = (0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2])[..., None]
    # Split-tone theo độ sáng
    w_sh = np.clip(1 - luma * 2, 0, 1)
    w_hi = np.clip(luma * 2 - 1, 0, 1)
    s = s + w_sh * np.array(p["shadow_tint"]) + w_hi * np.array(p["high_tint"])
    # Bão hòa chung + giảm riêng các điểm ảnh thiên xanh lá
    greenness = np.clip(s[..., 1:2] - np.maximum(s[..., 0:1], s[..., 2:3]), 0, 0.3) / 0.3
    sat = p["sat"] * (1 - greenness * (1 - p["green_sat"]))
    s = luma + (s - luma) * sat
    out = np.clip(s, 0, 1)
    return rgb + (out - rgb) * strength


def write_cube(path: Path, preset: str = "documentary", strength: float = 1.0, size: int = 33) -> Path:
    import numpy as np

    g = np.linspace(0, 1, size)
    # .cube: R thay đổi nhanh nhất, rồi G, rồi B
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    grid = np.stack([r, gg, b], axis=-1).reshape(-1, 3)
    out = transform(grid, preset, strength)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'TITLE "{preset} {strength:.2f}"', f"LUT_3D_SIZE {size}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    lines += [f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in out]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def preview(frame_bgr, preset: str = "documentary", strength: float = 1.0):
    """Ảnh so sánh trước | sau (BGR) để duyệt bằng mắt."""
    import numpy as np

    rgb = frame_bgr[..., ::-1].astype(np.float32) / 255
    after = (transform(rgb, preset, strength)[..., ::-1] * 255).round().astype(np.uint8)
    return np.concatenate([frame_bgr, after], axis=1)
