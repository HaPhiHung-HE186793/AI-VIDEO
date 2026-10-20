# Công thức Prompt — Gemini / Nano Banana / Veo 3.1

Nguyên tắc chung cho mọi model sinh ảnh/video:
- **Khẳng định, không phủ định.** "scaly lips covering the teeth" tốt hơn "NEVER show teeth". Thứ cần loại → `negative_prompt`.
- **Một câu mô tả nhân vật cố định** (`identity_line`), dán nguyên văn mọi nơi. Không diễn đạt lại.
- **Ngôn ngữ quay phim chuẩn**: cỡ cảnh, góc máy, ống kính (mm), chuyển động máy, ánh sáng.
- **Bỏ token rác**: `8k`, `masterpiece`, `AAA`, `ultra-realistic`, mã phiên bản, `Strict ...`.

---

## 1. Gemini — nghiên cứu & đề xuất concept

```text
Bạn là biên kịch kiêm giám đốc sáng tạo cho kênh {NỀN_TẢNG} (khán giả: {KHÁN_GIẢ}).
Chủ đề: "{TOPIC}". Thời lượng: {DURATION}s. Ngôn ngữ: {LANGUAGE}. Định dạng: {16:9 | 9:16}.

1. Tóm tắt 3 insight/sự thật bất ngờ nhất về chủ đề (kèm nguồn đáng tin).
2. Đề xuất 4 concept. Mỗi concept:
   - Tiêu đề + hook 3 giây đầu (hình ảnh gì, câu nói/câu hỏi gì).
   - Cấu trúc kể: mở (vấn đề/câu hỏi) → phát triển (2–3 nhịp có leo thang) → payoff (câu trả lời/twist) → CTA.
   - Phong cách hình ảnh và lý do hợp chủ đề.
   - Âm thanh: lời dẫn ngoài hay nhân vật nói trên hình; nhạc nền mood gì.
   - Rủi ro sản xuất với Veo 3.1 (cảnh khó: tương tác tay, nhiều nhân vật, chữ trên hình...).
Không bắt chước phong cách nhận diện của một kênh/thương hiệu cụ thể.
```

## 2. Gemini — kịch bản & shot list (xuất JSON đúng schema manifest)

```text
Chuyển concept đã chọn thành shot list cho Veo 3.1. Trả về JSON array, mỗi phần tử:
{"shot_id","scene_id","order","camera","subjects","action","environment","lighting",
 "audio":{"mode","line","speaker","delivery","sfx"},"generation_mode","transition_to_next","transition_out","is_hook"}

Ràng buộc:
- Tổng {N} shot; mỗi clip Veo 8s sẽ được dựng còn ~{AVG}s → mỗi shot 1 ý hình ảnh rõ ràng.
- "action": 1–2 hành động, viết bằng tên ngắn của nhân vật ({SHORT_NAMES}). Cho xem, đừng kể: hình phải minh họa đúng câu lời dẫn.
- "camera": cỡ cảnh + ống kính + chuyển động; xen kẽ wide / medium / close-up / cảnh phản ứng; giữ hướng di chuyển nhất quán (quy tắc 180°).
- "audio.mode": voiceover_external cho lời dẫn; veo_dialogue chỉ khi nhân vật nói trên hình (≤ {MAX_UNITS} {UNIT} / clip).
- "generation_mode": ingredients nếu có nhân vật chính và không cần bố cục chính xác; first_frame nếu cần bố cục; extend cho nối tiếp cùng cảnh; text cho cảnh không nhân vật.
- Hook 3 giây đầu phải là hình ảnh mạnh nhất, không mở bằng câu sáo rỗng.
```

Dán kết quả vào `shots` của manifest rồi chạy `build-prompts` + `lint-prompts`.

---

## 3. Nano Banana — ảnh tham chiếu nhân vật (từng ảnh riêng)

Sinh tự động bằng `forge-assets`. Mẫu:

```text
{SHORT_NAME}: {IDENTITY_LINE}. {VIEW}. {STYLE}. Plain neutral grey studio background, soft even lighting, single subject, no text.
```
`{VIEW}` lần lượt: front-facing portrait / full-body three-quarter view / full-body side profile (sinh vật: head close-up, three-quarter, profile; hoạt hình: thêm expression sheet).

Kiểm tra trước khi dùng: cùng màu, cùng tỷ lệ, cùng chi tiết nhận dạng giữa các ảnh. Ảnh lệch → tạo lại, đừng "chữa" bằng prompt video.

## 4. Nano Banana — bối cảnh sạch

```text
{ENV_NAME}: {ENV_IDENTITY_LINE}. Wide establishing view, {STYLE}. Empty scene without people or animals, natural lighting, no text.
```

## 5. Nano Banana Pro — frame khởi đầu (cho `first_frame` / `first_last`)

Đính kèm ảnh tham chiếu nhân vật + bối cảnh, rồi:

```text
{CAMERA: cỡ cảnh, góc máy, ống kính}. {SHORT_NAME} from the reference images, {tư thế & vị trí bắt đầu, hướng nhìn}, in {bối cảnh từ ảnh bối cảnh}. {ánh sáng}. {STYLE}. Exact 16:9 frame (hoặc 9:16), no text.
```
- Xuất đúng tỷ lệ khung của dự án (frame sai tỷ lệ → video bị letterbox, như shot_07 T-Rex).
- `first_last`: frame cuối dùng cùng góc máy, cỡ cảnh, ánh sáng; chỉ khác tư thế/vị trí.

---

## 6. Veo 3.1 — cấu trúc prompt (do `build-prompts` ghép)

```text
[Camera]. [Short name] is [identity_line]. [Action: 1–2 việc, có diễn tiến]. [Setting], [lighting]. [Style line]. [Audio]. No subtitles, no on-screen text.
```

Phần âm thanh theo `audio.mode`:
- `voiceover_external` / `sfx_only`: `Ambient sound only: {sfx}.`
- `veo_dialogue`: `{Speaker} speaks to camera in {Language}, {delivery}: "{line}"` + `{Others} listens with mouth closed.`
- `veo_narration` (tránh dùng cho phim nhiều shot): `A calm narrator voiceover says in {Language}: "{line}"`.

Ví dụ (shot_08 T-Rex, 626 ký tự):

```text
Low-angle close-up, 65mm lens, slow push-in. Rex is a massive adult Tyrannosaurus rex with dark charcoal-brown pebbled scales, a warm ochre-tan underbelly, a scarred snout, amber eyes, and scaly lips that fully cover its teeth when the mouth is closed. Rex's jaw muscles bulge as it lowers its head, then it lunges forward and out of frame. Wet ferns at the forest edge, golden dawn backlight. Photorealistic natural history documentary, large-format cinema camera look, naturalistic color, shallow depth of field. Ambient sound only: deep throat rumble, snapping fern stems, a heavy footfall. No subtitles, no on-screen text.
```
Negative prompt: `exposed teeth while the mouth is closed, red facial skin, cartoon look, extra limbs, duplicate animals, text, watermark, black letterbox bars`

## 7. Veo 3.1 — mẹo theo tình huống

| Tình huống | Cách làm |
|---|---|
| Nhân vật trôi danh tính | Thêm ảnh tham chiếu (ingredients) hoặc dựng frame đầu từ ảnh tham chiếu; kiểm tra `identity_line` dán nguyên văn. |
| Tương tác tay/đạo cụ lỗi | Đạo cụ có ảnh riêng; dựng frame đầu đã cầm sẵn; hành động đơn giản, chậm; cận cảnh tay là cảnh riêng. |
| Vật thể tự mọc giữa khung | Đưa nó vào frame đầu, hoặc viết "enters from the left edge of frame". |
| Đi tại chỗ (treadmill) | Mô tả camera rõ ("camera stays still as Rex walks past from left to right") và có vật mốc tiền cảnh. |
| Nhép miệng tiếng Việt sai | Câu ngắn (≤ 19 âm tiết), một người nói, cận trung; hoặc dùng lời dẫn ngoài. |
| Kết thúc clip đứng hình | Hành động kéo dài tự nhiên (đi, quay đầu chậm); cắt bỏ phần thừa khi dựng thay vì nhồi "never stop". |
| Shot nối tiếp cùng cảnh giật | Dùng **Extend** thay vì nối bằng 1 frame tĩnh. |
