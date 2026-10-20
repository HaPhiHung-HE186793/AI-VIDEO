"""Mẫu prompt tài nguyên tiền kỳ cho Nano Banana: bộ ảnh tham chiếu nhân vật, bối cảnh sạch, đạo cụ.

Ảnh tham chiếu cho Veo nên là TỪNG ẢNH RIÊNG, một chủ thể, nền trung tính, cùng ánh sáng —
hiệu quả hơn một tấm sheet ghép nhiều góc. Turnaround sheet vẫn hữu ích làm tài liệu thiết kế.
"""

REFERENCE_VIEWS = {
    "human": [
        ("front", "front-facing portrait from chest up, neutral expression, looking at camera"),
        ("three_quarter", "full-body three-quarter view standing in a relaxed neutral pose, empty hands"),
        ("profile", "full-body side profile view, empty hands"),
    ],
    "creature": [
        ("head", "three-quarter close-up of the head, mouth closed"),
        ("three_quarter", "full-body three-quarter view in a natural standing pose"),
        ("profile", "full-body side profile view showing head-to-tail proportions"),
    ],
    "robot": [
        ("front", "front view of the full body in a neutral standing pose, empty hands"),
        ("three_quarter", "full-body three-quarter view"),
        ("profile", "full-body side profile view"),
    ],
    "cartoon": [
        ("front", "full-body front view, neutral friendly expression, arms relaxed"),
        ("three_quarter", "full-body three-quarter view"),
        ("expressions", "expression sheet of the same character: neutral, talking, surprised, laughing"),
    ],
}


def character_pack(char_id: str, name: str, identity_line: str, style: str, char_type: str = "human") -> dict:
    views = REFERENCE_VIEWS.get(char_type, REFERENCE_VIEWS["human"])
    refs = []
    for key, view in views:
        refs.append({
            "view": key,
            "path": f"assets/characters/{char_id}_{key}.png",
            "prompt": (f"{name}: {identity_line.rstrip('.')}. {view.capitalize()}. {style}. "
                       "Plain neutral grey studio background, soft even lighting, single subject, no text."),
        })
    turnaround = (f"Character turnaround design sheet of {name}: {identity_line.rstrip('.')}. {style}. "
                  "Front, back, left profile and right profile views of the exact same design side by side on a plain grey "
                  "background, identical proportions and colors in every view, no text.")
    return {
        "id": char_id,
        "name": name,
        "type": char_type,
        "identity_line": identity_line.strip(),
        "reference_prompts": refs,
        "reference_images": [r["path"] for r in refs],
        "turnaround_sheet_prompt": turnaround,
        "recommended_image_model": "pro",
    }


def environment_plate(env_id: str, name: str, identity_line: str, style: str) -> dict:
    return {
        "id": env_id,
        "name": name,
        "identity_line": identity_line.strip(),
        "clean_plate_prompt": (f"{name}: {identity_line.rstrip('.')}. Wide establishing view, {style}. "
                               "Empty scene without people or animals, natural lighting, no text."),
        "path": f"assets/environments/{env_id}.png",
        "recommended_image_model": "standard",
    }


def prop_sheet(prop_id: str, name: str, size: str, style: str) -> dict:
    size_txt = f", real size {size}" if size else ""
    return {
        "id": prop_id,
        "name": name,
        "prop_prompt": (f"Product-style reference of {name}{size_txt}, {style}. Front, side and three-quarter views "
                        "on a plain grey studio background, soft contact shadows, no hands, no text."),
        "path": f"assets/props/{prop_id}.png",
        "recommended_image_model": "pro",
    }
