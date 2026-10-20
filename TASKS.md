# Lộ trình cải tiến AI Video Studio

Thứ tự ưu tiên đã thống nhất (2026-10-19). Agent làm theo đúng thứ tự, tick `[x]` khi xong và ghi kết quả ngắn.
Ký hiệu: 🧑 = cần người dùng quyết định / cung cấp.

**Chính sách chi phí (người dùng chốt 2026-10-20): KHÔNG trả thêm phí.** Chỉ dùng credit Flow có sẵn trong gói Ultra + bậc miễn phí Gemini API + công cụ miễn phí. Không bật thanh toán Cloud (bỏ Lyria, TTS trả phí, QA argon). `studio_config.json: cost_policy = free_only`.

## Đã xong
- [x] Ưu tiên 1 (phần lớn): module `flow.py` + `flow-generate` / `flow-harvest` (selector theo aria-label, tải theo hàng, khớp shot theo prompt).
- [x] Ưu tiên 2: `qa-takes` (lỗi có mốc giờ, `qa_rubric` theo dự án) + `auto-select` (chọn take, cắt tránh lỗi, `needs_retake` / `needs_director`).
- [x] Chương 1 T-Rex v2 dựng lại hoàn toàn tự chọn take (`output/T-Rex_Chapter1_v2*.mp4`).

## Bước 1 — Làm nốt hạ tầng (không tốn credit)
- [x] 1.1 `flow-harvest` chỉ tải đúng số hàng mới nhất ứng với job chưa tải (`flow_jobs[].harvested`); hàng trùng chữ được phân biệt theo thứ tự; `--all` để quét lại. *Kiểm chứng: không còn job chờ → không tải gì.*
- [x] 1.2 `flow-upscale`: upscale 1080p lần lượt cho take đã chọn. Nhận đúng clip bằng sha256 bản 720p (dự phòng: chữ ký hình ở 2,5s/5,5s). Duyệt dải thu nhỏ của trình chỉnh sửa, phần còn lại quét lưới theo nội dung hàng; click xuyên lớp phủ thanh prompt; lưu sau từng clip. *8/8 shot lên 1920×1080; ~70–110 s/clip.*
- [x] 1.3 QA qua API: bậc miễn phí **không có** hạn mức cho `gemini-4-argon` / `gemini-3.1-pro` (limit 0) → tự chuyển sang `gemini_vision_qa_fallbacks` (`gemini-3.5-flash`), tự thử lại khi 503. So với agent trên 3 take: mốc lỗi gần trùng (vd. há miệng 1.0–4.0s vs 1.0–3.5s), API khắt khe hơn ~1 điểm, đôi khi áp tiêu chí T-Rex lên Triceratops; 26–180s/take do quá tải. → Chạy không người được; không bật thanh toán → model QA mặc định đổi thẳng sang `gemini-3.5-flash` (bỏ lượt gọi argon chắc chắn thất bại).
- [x] 1.4 `output/T-Rex_Chapter1_v2_1080*.mp4`: QA kỹ thuật 8/8 pass (không còn LOW_RESOLUTION), −14,7 LUFS / −2,1 dBTP; dựng 17 s (16:9) + 23 s (9:16). **Ước tính phim 1 phút (~12 shot): 45–60 phút** (gửi tạo ~10, Veo ~5, tải ~3, upscale ~18, QA agent ~10 / QA API miễn phí 20–60, dựng 1) → chưa đạt mục tiêu 30 phút; nút thắt: upscale tuần tự + QA. Hướng (miễn phí): QA do agent chat làm, gọi thẳng model miễn phí `gemini-3.5-flash` khi chạy độc lập; upscale chỉ shot đã chọn (đã làm, 4 clip/234 s).

## Bước 2 — Nâng nội dung (giá trị lớn nhất)
- [x] 2.1 `manifest.beats` + `shot.beat`: lời dẫn theo beat trải qua nhiều shot (L-cut), `j_cut_sec` cho lời vào trước hình; hình mỗi shot chia đều theo lời của beat (`min_beat_shot_sec`); cảnh báo lời chồng nhau; `voiceover` tạo 1 file/beat, không ép tốc độ. *7 test mới.*
- [x] 2.2 `storyboard` → `output/storyboard.html` + `.jpg` (frame, lời dẫn, góc máy theo beat, credit ước tính chỉ cho shot mới); `storyboard-approve` lưu hash nội dung; `flow-generate --kind video` bị chặn nếu chưa duyệt hoặc sửa sau khi duyệt.
- [x] 2.3 Chương 1 v3: 7 beat (hook → nhu cầu → giác quan → mục tiêu → leo thang → cao trào → câu hỏi treo), 16 shot = 8 shot v2 dùng lại + 8 shot mới (cận sườn đói, dấu chân, Triceratops gặm cỏ / cảnh giác, bước chân rón rén, lao ra, Triceratops chĩa sừng, đôi mắt thứ hai). Frame mới tạo bằng Nano Banana (0 credit), lời dẫn 7 beat ~35 s một giọng (`gemini-3.1-flash-tts-preview`, Charon).
- [x] 2.4 Storyboard được duyệt → 8 shot mới (1.600 credit, 0 tạo lại) → QA → auto-select (cắt theo phần chia của beat) → `output/T-Rex_Chapter1_v3*.mp4`: 44,8 s, 16 shot, 7 lời dẫn trải qua nhiều shot, J-cut b02/b04, −14,6 LUFS / −2,4 dBTP. Lỗi lộ ra & đã sửa: tải nhầm hàng (c1_09 nhận file của shot_04) → kiểm tra hàng trước khi bấm + chặn file trùng shot khác + so frame đầu (đúng 0,93–0,99 / nhầm −0,17); ghi đè manifest khi 2 lệnh chạy song song → khóa dự án. ~~Tồn: 4 shot c1_09–c1_12 chưa upscale~~ → đã upscale 1080p (234 s) ở v4, 2026-10-20.

## Bước 3 — Âm thanh
- [x] 3.1 Nguồn nhạc: **bỏ Lyria (trả phí)**. Mặc định `score` tự tổng hợp (0 đồng). Muốn nhạc thật: tải file miễn phí (vd. YouTube Audio Library) → `assemble --music <file>`.
- [x] 3.2 Nhạc nền theo chương: **xong** lệnh `score` — nhạc tự tổng hợp bám beat (drone D thứ, dây dâng, trống trầm nhanh dần tới cao trào, cú boom ở câu hỏi treo), 0 credit, miễn bản quyền, ~10 s cho 45 s nhạc; ducking dưới lời dẫn sẵn có. **Nhạc bám hình:** trống trong leo thang/cao trào rơi đúng điểm cắt (9/27 nhịp trùng cắt ở Chương 1, nhấn mạnh hơn), riser 1,8 s dẫn vào cao trào + cú nhấn lớn. (SFX theo hành động vẫn lấy từ âm thanh gốc của Veo.)
- [x] 3.3 TTS: **bỏ bậc trả phí**. Dùng bậc miễn phí Gemini TTS (10 lần/ngày/model; 1 chương ~7 beat → đủ 1 chương/ngày). Tiết kiệm hạn mức: mỗi câu có dấu vân tay (chữ + giọng + chỉ đạo + model) → chỉ đọc lại câu đã sửa; hết hạn mức thì dừng, giữ phần đã tạo, chạy lại hôm sau.

## Bước 4 — Hậu kỳ & phát hành
- [ ] 4.1 🧑 Video ngắn tạo thẳng 9:16 (frames + video ở 9:16), không crop từ 16:9. Dùng credit Flow có sẵn (không phải phí thêm) — cần người dùng đồng ý số credit.
- [x] 4.2 Fade mở/kết chương + lệnh `make-lut`: LUT .cube tạo bằng code (preset `documentary`: S-curve nhẹ, split-tone ấm/lạnh, giảm xanh lá "neon" của AI), ảnh so sánh trước/sau, `manifest.lut_path` → `assemble` tự áp. Đã áp cho v4.
- [x] 4.3 Lệnh `thumbnail`: tự chọn frame nét/tương phản tốt nhất (hoặc `--shot`), tiêu đề có viền, 16:9 + 9:16, tự chọn font đủ dấu tiếng Việt. Lệnh `publish-kit` → `output/publish.md`: tiêu đề/mô tả/tag (agent viết vào `manifest.publish`), hashtag hợp lệ, chương YouTube theo beat (chỉ khi ≥ 3 chương ≥ 10 s), ghi chú công bố AI + checklist bật nhãn 'Altered or synthetic content', kiểm giới hạn 100 ký tự tiêu đề.

## Tồn đọng đã chấp nhận
- shot_02 v2 hé hàm ~1s (giây 9–11) — không tạo lại vì Chương 1 sẽ viết lại ở Bước 2.
- c1_16 tạo lại "chỉ đôi mắt trong bóng tối" (200 credit, 2026-10-20): cả 2 take Veo vẫn cho Rex bước ra + khói thở → chỉ 2.8s sạch; auto-select giữ take 2 cũ (con T-Rex thứ hai sau lưng Rex — khớp lời "kẻ săn mồi không bao giờ là duy nhất"). Manifest c1_16 đã trả về action + frame c02 khớp take đang dùng (prompt trùng khớp 100%) → storyboard cần duyệt lại trước lần tạo video sau.
- Bài học Veo: "nothing else moves / holds still" không giữ được chủ thể lớn đứng yên 8s — muốn cảnh tĩnh nên dùng `first_last` (2 frame gần giống nhau) hoặc chấp nhận cắt 2–3s.

## Nhật ký v4 (2026-10-20)
- Chương 1 v4: 16 shot đều 1080p (upscale 4 shot còn lại: 234s, trước đây 33 phút), nhạc `score` tự tổng hợp, fade mở/kết, thumbnail. 44.75s, −14.7 LUFS / −2.3 dBTP. Đầu ra: `output/T-Rex_Chapter1_v4.mp4`, `_v4_9x16.mp4` (phụ đề in cứng), `thumbnail.jpg`, `thumbnail_9x16.jpg`.
- Sửa `flow-harvest`: hàng cũ trùng phần đầu prompt (file đã là take của shot) bị bỏ qua, không trừ quota — trước đó hàng mới chưa xong khiến tải nhầm hàng cũ (đã bị chốt chặn first_frame_match chặn đúng, corr 0.41).
- Thumbnail đổi sang tiếng Anh (lời dẫn tiếng Anh): "24 HOURS IN HELL CREEK / Chapter 1 · The Hunt". Bộ đăng kênh `output/publish.md`.
