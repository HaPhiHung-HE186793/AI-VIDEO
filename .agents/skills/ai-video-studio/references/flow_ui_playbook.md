# Google Flow — Tự động hóa (module `scripts/studio/flow.py`)

Agent điều khiển Chrome thật của người dùng (cổng debug 9222, profile `chrome_ai_bot`) — người dùng đã cho phép.
Không thao tác tay bằng tọa độ nữa: dùng các lệnh dưới đây. Lệnh `browser` chỉ để gỡ lỗi.

## Vòng sản xuất tự động

```powershell
python scripts/studio_helper.py check-browser --launch
# 1. Frame mở đầu (Nano Banana Pro, đính ảnh tham chiếu nhân vật tự động)
python scripts/studio_helper.py flow-generate --project <slug> --kind frames --count 2
python scripts/studio_helper.py flow-harvest  --project <slug> --kind image --wait
#    → shots[].frame_candidates; agent xem và đặt first_frame_path cho mỗi shot
# 2. Video (Veo) — chế độ theo generation_mode của shot; tự gắn frame đầu / ảnh tham chiếu / giọng
python scripts/studio_helper.py flow-generate --project <slug> --kind video --count 2 --max-credits 2000
python scripts/studio_helper.py flow-harvest  --project <slug> --kind video --wait
# 3. QA từng take + tự chọn
python scripts/studio_helper.py qa-takes        --project <slug>
python scripts/studio_helper.py qa-takes-submit --project <slug>     # (chế độ agent/manual)
python scripts/studio_helper.py auto-select     --project <slug>
# 4. Upscale 1080p cho take đã chọn (lần lượt; bản dựng tự dùng bản 1080p)
python scripts/studio_helper.py flow-upscale  --project <slug>
# 5. Tạo lại shot hỏng (vòng lặp tới khi needs_retake rỗng)
python scripts/studio_helper.py flow-generate --project <slug> --kind video --retakes --max-credits 800
python scripts/studio_helper.py flow-harvest  --project <slug> --kind video --wait
```

- Luôn chạy `--dry-run` cho lô đầu tiên của dự án: soạn đủ (frame, ảnh tham chiếu, prompt), chụp `.flow/<shot>_*_compose.png`, không tốn credit. Xem ảnh rồi mới chạy thật.
- `--max-credits` dừng gửi khi vượt ngân sách lượt đó. Mỗi lần gửi ghi vào `manifest.flow_jobs`.
- `flow_project_url` lưu trong manifest; `--new-project` để tạo dự án Flow mới.

## Cách module nhận diện giao diện (sửa ở `UI` trong flow.py nếu Flow đổi)

| Thành phần | Selector |
|---|---|
| Ô prompt | `div[role=textbox][aria-label='Bạn muốn tạo những gì?']` |
| Cài đặt | `button[aria-label='Điều kiện kích hoạt cài đặt']` → nhóm `flow-toggles[aria-label=Chế độ / Tỷ lệ khung hình / Thời lượng video / Số lượng kết quả đầu ra]` với `button[role=radio][aria-checked]` |
| Model | `.model-select-trigger-content` → chọn theo tên |
| Chi phí | `flow-credit-cost-label` ("Quá trình tạo sẽ tốn N tín dụng") |
| Xóa ô prompt (cả frame/thành phần) | `button[aria-label='Xoá câu lệnh']` |
| Gửi | `button[aria-label='Bắt đầu tạo']` |
| Frame đầu | nút có tên chính xác "Bắt đầu" → bảng chọn → tìm theo tên file, tải lên nếu chưa có |
| Thành phần / giọng | nút "+" (chữ `add`) trong khung prompt, hoặc gõ `@` ở chế độ Khung hình → `input[placeholder='Tìm kiếm thành phần']` → "Thêm vào câu lệnh" |
| Tải về | `button[aria-label='Tải xuống hàng loạt']` theo HÀNG; hàng được nhận diện bằng prompt hiển thị trong hàng; file zip được giải nén |

## Bài học đã kiểm chứng
- Tọa độ không ổn định (khung prompt đổi cao theo nội dung) → chỉ dùng selector.
- `Escape` trong trình chỉnh sửa thoát về lưới; mở trình chỉnh sửa từng clip để tải rất chậm và dễ lệch → tải theo hàng.
- Upscale 1080p chỉ ổn khi làm lần lượt từng clip; bấm đồng loạt sẽ treo. `flow-upscale` nhận clip bằng sha256 bản 720p.
- Dải thu nhỏ trong trình chỉnh sửa chỉ hiện một phần dự án; ô ở cuối lưới bị thanh prompt che → click phần tử của ô qua `elementsFromPoint`.
- `flow-harvest` chỉ tải số hàng mới nhất ứng với job chưa tải (`flow_jobs`); `--all` để quét lại.
- QA qua API ở bậc miễn phí: argon/pro không có hạn mức → tự dùng `gemini_vision_qa_fallbacks`.
- Gắn giọng cố định (vd. Charon) trên 2 clip khác nhau cho cùng giọng (chênh cao độ 2,1%).
