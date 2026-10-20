# Tư duy Đạo diễn — Áp dụng cho mọi chủ đề

Tài liệu này là phần "nghề làm phim" mà công cụ không tự làm thay được. Veo 3.1 là máy quay; chất lượng phim nằm ở kịch bản, dàn dựng, dựng phim và âm thanh.

---

## 1. Kể chuyện

- **Hook 3 giây đầu** là hình ảnh mạnh nhất hoặc một câu hỏi gây tò mò cụ thể. Tránh câu mở sáo rỗng ("Hàng triệu năm trước...", "Bạn có biết...").
- **Cấu trúc**: vấn đề / câu hỏi → 2–3 nhịp leo thang → payoff (câu trả lời, twist, cảm xúc) → kết. Video giải thích phải thực sự trả lời câu hỏi của tiêu đề.
- **Cho xem, đừng kể**: mỗi câu lời dẫn phải có hình minh họa đúng nội dung câu đó. Nếu lời dẫn nói "khứu giác siêu nhạy", hình phải cho thấy hành vi đánh hơi/lần theo dấu vết.
- **Nhân vật có mục tiêu và trở ngại.** Hai nhân vật cùng khung hình, tương tác với nhau, luôn hấp dẫn hơn chuỗi độc thoại nói vào camera.
- **Chính xác nội dung**: kiểm tra sự thật khoa học/lịch sử với Gemini kèm nguồn; hình ảnh phải khớp (ví dụ: đã nói T-Rex có môi che răng thì hình không được lộ răng khi ngậm miệng).

## 2. Chọn chế độ Veo theo shot

| Nhu cầu | Chế độ | Ghi chú |
|---|---|---|
| Cảnh không nhân vật cố định | `text` | B-roll, thiên nhiên, hiện tượng. |
| Nhân vật/sản phẩm nhất quán | `ingredients` | 1–3 ảnh tham chiếu sạch. |
| Bố cục/góc máy chính xác | `first_frame` | Frame từ Nano Banana Pro dựng trên ảnh tham chiếu, đúng tỷ lệ khung. |
| Chuyển động có điểm đến | `first_last` | Hai frame cùng cỡ cảnh, góc máy, ánh sáng. |
| Hành động kéo dài cùng cảnh | `extend` | Giữ quán tính; chất lượng giảm sau vài lần extend. |

Độ khó cao (Quality): tương tác tay/đạo cụ, nhiều chủ thể chạm nhau, cận chi tiết giải phẫu, nhép miệng, hook/kết. Cảnh dễ (Fast): phong cảnh, 1 chủ thể chuyển động đơn giản. `build-prompts` tự chấm điểm và định tuyến.

## 3. Ngôn ngữ máy quay

- Xen kẽ cỡ cảnh có chủ đích: wide (thiết lập không gian) → medium (hành động) → close-up (cảm xúc/chi tiết) → cảnh phản ứng.
- **Quy tắc 180°**: giữ hướng nhìn/di chuyển nhất quán giữa các shot liên tiếp (con mồi bên phải, kẻ săn bên trái...).
- Chuyển động máy có động cơ: máy đi theo chủ thể, không "bay lượn" vô cớ.
- Ống kính gợi cảm giác: 24–35mm (không gian, hùng vĩ), 50mm (tự nhiên), 85mm+ (thân mật, tách nền).

## 4. Dựng phim

- **Clip 8s ≠ shot 8s.** Shot sau dựng thường 2–5s (video ngắn 1.5–3s). Tạo nguyên liệu dư, chọn đoạn đẹp nhất (`edit_in`/`edit_out`).
- **Coverage**: nhịp truyện quan trọng nên có 2–3 góc (wide + close + reaction) để dựng có lựa chọn.
- **Hard cut là mặc định.** Dissolve = thời gian trôi / đổi chương. Không dùng hiệu ứng chuyển cảnh để che lỗi.
- **Dựng theo lời dẫn và nhạc**: hình cắt theo nhịp câu và phách nhạc; để khoảng thở (0.5–1.5s không lời) sau ý quan trọng.
- **Màu đồng bộ**: clip AI lệch màu nhau → áp 1 LUT chung (`assemble --lut`), chọn take có tông gần nhau.

## 5. Âm thanh (một nửa trải nghiệm xem)

- 3 lớp: **lời** (lời dẫn TTS/thu âm 1 giọng, hoặc thoại Veo ngắn) + **SFX/không khí** (Veo làm rất tốt) + **nhạc** (tự hạ khi có lời).
- Chuẩn hóa −14 LUFS (YouTube/TikTok), đỉnh ≤ −1.5 dBTP — `assemble` tự làm.
- Lời dẫn nhiều shot không để Veo đọc: mỗi lần tạo là một giọng khác.

## 6. Phát hành

- **9:16** cho TikTok/Shorts/Reels — tạo ở 9:16 từ đầu; crop từ 16:9 chỉ là phương án dự phòng (`crop_focus_x`).
- **Phụ đề**: in cứng cho video ngắn (`--burn-subs`); file `.srt` đăng kèm cho YouTube.
- **1080p** tối thiểu: tải bản 1080p/upscale từ Flow — ffmpeg phóng to 720p không thêm chi tiết.
- Thumbnail, tiêu đề, 3 giây đầu được thiết kế cùng nhau.

## 7. Bảo đảm chất lượng

- QA kỹ thuật (`qa`) bắt lỗi đo được: letterbox, độ phân giải, đứng hình, audio.
- QA thị giác (`qa-vision`) bắt lỗi nội dung: sai danh tính, sai giải phẫu, vật thể mọc ra, không bám prompt.
- Lỗi lặp lại → sửa nguyên nhân gốc (ảnh tham chiếu, chế độ, frame đầu), không thêm "luật" vào prompt.
- Mỗi take lưu nguồn gốc (prompt, input, model, hash) để tái tạo hoặc so sánh.
