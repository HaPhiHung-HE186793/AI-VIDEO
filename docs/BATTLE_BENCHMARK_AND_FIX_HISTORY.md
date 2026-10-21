# Báo Cáo Hậu Kiểm & Lịch Sử Cải Tiến: Đối Chiếu Trận Đại Chiến Khủng Long Với Chuẩn Hollywood (*Jurassic World Final Battle*)

- **Dự án áp dụng:** [`projects/clash-of-titans-rex-vs-vasto-part-1`](../projects/clash-of-titans-rex-vs-vasto-part-1/project_manifest.json)
- **Video mẫu đối chiếu (Ground-Truth Reference):** [*Final Battle Scene | Jurassic World* (`FtCslvCjZEY`)](https://www.youtube.com/watch?v=FtCslvCjZEY) — Đạo diễn Colin Trevorrow, Kỹ xảo ILM (Industrial Light & Magic)
- **Hai phiên bản thành phẩm hoàn chỉnh để đối chiếu:**
  1. **Phương án A (`100.54s` / 14 cú cắt tuyến tính 1-take/shot):** [`output/final_video_option_A.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A.mp4) & [`output/final_video_option_A_9x16.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A_9x16.mp4)
  2. **Phương án B (`300.00s` / 5 phút — 22 shot kịch bản nối tiếp / 70 cú cắt tuyến tính không lặp lại):** [`output/final_video_option_B_5min.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min.mp4) (đồng thời là [`output/final_video.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video.mp4)) & [`output/final_video_option_B_5min_9x16.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min_9x16.mp4)
- **Điểm tương đồng định lượng & liền mạch cuối cùng (`benchmark-compare`):** **`99.2 / 100` (`PASS_HOLLYWOOD_BENCHMARK`, `narrative_continuity_score_100 = 100.0`)**

---

## Phần 1: Phân Tích Định Lượng Video Mẫu Hollywood (`FtCslvCjZEY`)

Để tránh đánh giá cảm tính, chúng tôi đã tải trực tiếp video mẫu `FtCslvCjZEY` (`516.93s`, phân đoạn *Apex Dinosaur Duel* từ `254s` đến `474s`) và trích xuất các chỉ số quang học, nhịp dựng, góc máy bằng công cụ [`scripts/studio/qa.py`](../scripts/studio/qa.py):

| Tiêu chí kỹ thuật & Điện ảnh | Thông số đo thực tế từ mẫu *Jurassic World* (`FtCslvCjZEY`) | Ý nghĩa điện ảnh (Vì sao phim thật nhìn có "sức nặng" hàng trăm triệu USD?) |
| :--- | :--- | :--- |
| **Độ sáng trung bình (`Mean Luma`)** | **`19.15 / 255`** | Phim đánh nhau ban đêm dùng **Ultra-Low-Key Chiaroscuro**: dìm tối `89%` khung hình để che khuyết điểm bề mặt CGI và buộc mắt người xem tập trung vào hàm răng, mắt và phần lưng có ven sáng (rim light). |
| **Tỷ lệ vùng tối sâu (`Dark Shadow Ratio < 48`)** | **`0.890` (89.0%)** | Nền rừng/công viên chìm trong bóng tối lạnh (`Cyan/Teal`), chỉ có tia lửa/ánh trăng chiếu ven (`Specular Rim Ratio = 0.008`). |
| **Độ tương phản nội khung (`Contrast Std`)** | **`25.96`** | Tách bạch rõ rệt giữa vùng tối sâu và vùng highlight ẩm ướt trên da khủng long. |
| **Nhịp độ cắt cảnh (`Median Shot Length`)** | **`3.2s – 4.5s / cú cắt`** (`~68–70` cú cắt cho 5 phút) | Không bao giờ giữ 1 góc máy tĩnh quá 5 giây trong lúc giao chiến; cắt dồn dập vào đúng khoảnh khắc va chạm vật lý (Cut on Action). |
| **Tính liền mạch nhân-quả (`Narrative Continuity`)** | **`0` lần nhảy lùi thời gian, `0` lần lặp lại sự kiện một chiều** | Trận đánh diễn tiến một chiều: Rình rập → Chạm mặt → Giao chiến → Quật ngã → Phá hủy môi trường → Kết thúc. Không bao giờ đánh nhau trước khi gặp nhau hoặc rơi xuống vực rồi lại nhảy về rừng đánh tiếp. |
| **Hệ thống 6 Góc Máy Biểu Tượng (`6 Camera Archetypes`)** | 1. `foot_tremor_macro` (Đặc tả bàn chân dẫm rung mặt nước)<br>2. `eye_snarl_ecu` (Cận cảnh 85mm mắt & nhe nanh)<br>3. `visceral_jaw_clamp_cu` (Cận cảnh 2 hàm ngoạm nhau)<br>4. `asymmetric_knockdown` (Bất đối xứng: quật ngã xuống bùn)<br>5. `environmental_destruction` (Phá hủy cây cối/đá văng)<br>6. `abyss_standoff_wide` (Toàn cảnh gầm vang đối đầu) | Xen kẽ liên tục giữa **Toàn cảnh (`24mm–35mm`)** và **Cận cảnh/Đặc tả (`85mm Macro`)** để tạo cảm giác khổng lồ và tàn khốc. |

---

## Phần 2: Vì Sao Các Video AI Tạo Ra Ở Các Vòng Đầu Bị Lỗi Và Không Bằng Mẫu? (9 Nguyên Nhân Gốc Rễ)

Qua 4 vòng lặp tạo video và kiểm tra trực quan (`Vòng 1` → `Vòng 2` → `Vòng 3` → `Vòng 4`), chúng tôi đã xác định chính xác **9 nguyên nhân gốc rễ**:

1. **Lỗi "Phơi Sáng Ban Ngày" (`Overexposed Daylight CGI Look` — Vòng 1 & 2):**
   - Độ sáng trung bình ban đầu là `Mean Luma = 56.60` (sáng gấp 3 lần mẫu *Jurassic World* `19.15`), làm lộ da khủng long như mô hình nhựa 3D.
2. **Lỗi "Bẫy Toàn Cảnh 35mm" (`Medium-Wide Two-Shot Monotony` — Vòng 1 & 2):**
   - 10 shot đầu tiên đều đặt máy ở cự ly trung-toàn cảnh (`24mm–35mm`), thiếu hoàn toàn các góc đặc tả `85mm` (mắt co giãn, răng nhe nanh, bàn chân dẫm nổ vũng bùn).
3. **Lỗi "Đối Xứng Ngang Tài Ngang Sức Máy Móc" (`Symmetric Stalemate` — Vòng 1 & 2):**
   - Hai con chỉ đứng đối diện táp nhau 50/50, thiếu cảnh **bất đối xứng (`asymmetric_knockdown`)** nơi một con bị quật ngã nằm bẹp dưới bùn và bị dẫm chân lên lưng như mẫu *Jurassic World* (`374s`).
4. **Lỗi "Ảo Giác Giải Phẫu Khi Xoắn Cận Chiến" (`5-Legged Hallucination` — Vòng 1):**
   - Ở `shot_05_take02` (`t=2.5s–6.5s`), hai thân khủng long xoắn vào nhau mọc thành 5 chân khi không khóa frame đầu/cuối.
5. **Lỗi "Đông Cứng Hạt Nước Ở Cuối Clip" (`First-Last Water Droplet Freeze` — Vòng 1):**
   - Khi ảnh `END` keyframe có vẽ giọt nước bắn, Veo 3.1 treo giọt nước lơ lửng từ giây thứ 5 đến giây thứ 8 để khớp với ảnh `END`.
6. **Lỗi "Đảo Lộn Trật Tự Nhân-Quả & Nhảy Bối Cảnh Khi Kéo Dài 5 Phút" (`Broken Narrative Chronology` — Phát hiện ở Vòng 3):**
   - Ở Vòng 3, khi kéo dài 14 shot ra 300 giây bằng cách trộn `cutaway_segs` (`shot_11..14`) vào mọi Hồi, thuật toán đã bốc cảnh cắn nhau (`shot_13`) và quật ngã (`shot_14`) lên ngay giây thứ 17 (trước cả khi 2 con gặp nhau ở `shot_03`), đồng thời cho phép cảnh đứng hai bờ vực (`shot_10`) xen kẽ tới lui 6 lần với cảnh cắn nhau trong rừng (`backward_jumps = 24`, `non_contiguous_revisits = 14`).
7. **Lỗi "Vắt Kiệt 14 Shot Ngắn Thành 5 Phút Gây Lặp Cảnh (`Repetitive Déjà Vu Loop` — Phát hiện ở Vòng 3):"**
   - 14 shot chỉ cung cấp ~90–100 giây nội dung sự kiện. Khi ép thành 300 giây mà không tạo thêm các shot nối mạch (`bridging shots`), mỗi cảnh bị chiếu đi chiếu lại 5–6 lần.
8. **Lỗi "Cắt Cúp Quang Học (`foot_tremor_ground`) Cắt Mất Đầu Khủng Long" (Phát hiện ở Vòng 3):**
   - Bộ lọc `foot_tremor_ground` dịch khung cắt xuống `ih*0.30` làm mất toàn bộ phần đầu khủng long khi áp lên cảnh toàn.
9. **Lỗi "Quá Tải Bộ Giải Mã FFmpeg Khi Render 70 Phân Đoạn Cùng Lúc":**
   - Mở 70 bộ giải mã H.264 đồng thời trong 1 lệnh `filter_complex` gây nghẽn bộ nhớ; cần chia cụm 14 phân đoạn render qua `h264_nvenc`.

---

## Phần 3: Lịch Sử Cải Tiến & Giải Pháp Triệt Để Ở Vòng 4 (Phương Án A & Phương Án B)

1. **Bổ sung Chỉ số Chấm Điểm Liền Mạch Kể Chuyện (`narrative_continuity_score_100`) vào [`scripts/studio/qa.py`](../scripts/studio/qa.py):**
   - Kiểm tra thứ tự `order` của toàn bộ các phân đoạn trên timeline: phạt nặng mọi cú nhảy lùi thời gian (`backward_jumps`) và mọi lần quay lại shot cũ sau khi đã chuyển sang shot mới (`non_contiguous_revisits`).
2. **Mở rộng Kịch bản lên **22 Shot Tuyến Tính Một Chiều (`shot_01` .. `shot_22` = 44 takes = 352 giây raw Veo 3.1 footage)** trên Google Flow:**
   - Giữ 14 shot cốt lõi (`shot_01..14`) và tạo mới **8 shot nối mạch nhân-quả (`shot_15..22`)** bằng cách trích xuất trực tiếp frame chuyển tiếp `1920x1080` từ shot liền trước để đảm bảo **liền mạch không gian 100%**:
     - `shot_15` (`order 6`): Cận cảnh 85mm Vasto nhe nanh thở khói đáp trả Rex trước khi lao vào nhau.
     - `shot_16` (`order 10`): Vasto giật đầu thoát khỏi hàm Rex và húc ngược vào ngực Rex giữa suối tung bọt trắng xóa.
     - `shot_17` (`order 12`): Hai con khóa cổ đẩy nhau từ lòng suối cạn lên bãi bùn đen.
     - `shot_18` (`order 14`): Nối tiếp ngay sau cảnh Vasto bị quật ngã (`shot_14`) — Vasto đạp tung bùn đen bật dậy phản công.
     - `shot_19` (`order 16`): Nối tiếp ngay sau cảnh húc gãy cây Tùng (`shot_07`) — hai con lao vào cắn xé giữa đám bụi gỗ và thân cây vừa đổ.
     - `shot_20` (`order 17`): Đẩy cuộc chiến từ rừng Tùng ra sát gờ đá chênh vênh bên bờ vực.
     - `shot_21` (`order 19`): Nối tiếp `shot_08` — mặt đá dưới chân nứt toác và nổ tung bụi đá, buộc 2 con nhảy lùi về 2 phía trước khi sập vực (`shot_09`).
     - `shot_22` (`order 21`): Nối tiếp `shot_09` — hai bạo chúa đứng ở hai bờ vực vừa tách đôi, thở khói trắng xóa và gầm gừ nhìn nhau trước cú gầm toàn cảnh cuối cùng (`shot_10`).
3. **Thiết kế Bộ Dựng Tuyến Tính Không Lặp Cảnh (`Strict Chronological Non-Overlapping Engine`) trong [`scripts/studio/timeline.py`](../scripts/studio/timeline.py):**
   - **Phương án A (`100.54s`, 14 cuts):** Đi tuần tự 1-take/shot qua 14 shot (`backward_jumps = 0`, `non_contiguous_revisits = 0`), giữ nguyên 100% khung hình gốc `wide_master`.
   - **Phương án B (`300.00s`, 70 cuts):** Đi tuần tự một chiều từ `order 1` (`shot_01`) đến `order 22` (`shot_10`) qua toàn bộ 44 takes sạch (`backward_jumps = 0`, `non_contiguous_revisits = 0`). Mỗi take dài 8 giây được chia tại điểm giữa `4.0s` thành nửa đầu `[0.0s–4.0s]` (`wide_master`) và nửa sau `[4.0s–8.0s]` (`ots_dirty_frame` / `cu_left_85mm` / `cu_right_85mm` giữ nguyên phần đầu `ih*0.02..0.03`), không bao giờ tua lại đoạn đã chiếu!
4. **Tinh chỉnh Bảng Màu 3D LUT `ilm_night_battle` trong [`scripts/studio/grade.py`](../scripts/studio/grade.py):**
   - Đặt `gamma = 1.54`, `exposure = 0.78`, `contrast = 0.36`, đưa `Mean Luma` của bản phim về đúng **`19.94`** (khớp gần như tuyệt đối với `19.15` của *Jurassic World*) và `Dark Shadow Ratio = 0.875` (so với `0.890` của *Jurassic World*).

---

## Phần 4: Bảng Đối Chiếu Định Lượng Qua 4 Vòng Lặp (Kèm Phương Án A & Phương Án B)

| Chỉ số đánh giá (`benchmark-compare`) | Vòng 1 (Bản nháp đầu) | Vòng 2 (10 shot lọc QA) | Vòng 3 (5 phút từ 14 shot — bị nhảy lùi mạch truyện) | **Vòng 4 — Phương án A (`100.5s` Tuyến tính 1-take/shot)** | **Vòng 4 — Phương án B (`300.0s` / 5 Phút Tuyến tính 22 Shot)** | Mẫu chuẩn *Jurassic World* (`FtCslvCjZEY`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Thời lượng (`Duration`)** | `63.65s` | `46.62s` | `300.00s` | **`100.54s` (`100.0/100`)** | **`300.00s` (`100.0/100`)** | `300.00s` |
| **Số cú cắt (`Cut Count` / `ASL`)** | `14 cuts` | `10 cuts` | `70 cuts` | **`14 cuts` (`ASL 7.18s`)** | **`70 cuts` (`ASL 4.29s`, `100.0/100`)** | `~68 cuts` (`ASL 4.41s`) |
| **Số lần nhảy lùi thời gian (`Backward Jumps`)** | `1` (lặp cuối) | `0` | `24 lần` (Lỗi nặng) | **`0 lần`** | **`0 lần`** | `0 lần` |
| **Số lần lặp cảnh cũ (`Non-Contiguous Revisits`)** | `1` | `0` | `14 lần` (Lỗi nặng) | **`0 lần`** | **`0 lần`** | `0 lần` |
| **Điểm Liền mạch Kể chuyện (`narrative_continuity_score_100`)** | `75.0 / 100` | `100.0 / 100` | `0.0 / 100` (`FAIL`) | **`100.0 / 100`** | **`100.0 / 100`** | `100.0 / 100` |
| **Độ sáng TB (`Mean Luma`)** | `57.10` | `56.60` | `14.67` | **`11.98`** | **`19.94` (`98.0/100`)** | `19.15` |
| **Tỷ lệ vùng tối (`Dark Shadow Ratio`)** | `54.0%` | `54.6%` | `92.5%` | **`94.9%`** | **`87.5%`** | `89.0%` |
| **Độ phủ 6 Góc Máy Biểu Tượng (`Camera Variety`)** | `2 / 6` | `2 / 6` | `6 / 6` | **`6 / 6` (`100.0/100`)** | **`6 / 6` (`100.0/100`)** | `6 / 6` |
| **Tỷ lệ sạch lỗi giải phẫu (`Defect-Free`)** | `50.0 / 100` | `100.0 / 100` | `100.0 / 100` | **`100.0 / 100`** | **`100.0 / 100`** | `100.0 / 100` |
| **TỔNG ĐIỂM (`overall_similarity_score_100`)** | **`42.1 / 100`** | **`70.0 / 100`** | **`80.8 / 100` (sau khi tính phạt đứt mạch truyện)** | **`91.5 / 100`** | **`99.2 / 100` (`PASS_HOLLYWOOD_BENCHMARK`)** | **`100.0 / 100`** |

---

## Phần 5: Danh Mục Đầy Đủ File Video & Bảng Kiểm Tra Trực Quan

1. **Phương án A (Bản Tinh Gọn `100.54s` — 14 cú cắt, mỗi shot xuất hiện đúng 1 lần, giữ 100% khung hình gốc):**
   - Video Ngang `16:9`: [`projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A.mp4)
   - Video Dọc `9:16`: [`projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A_9x16.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_A_9x16.mp4)
   - Bảng 14 khung hình kiểm tra Phương án A: [`projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/option_A_14_cuts_sheet.jpg`](../projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/option_A_14_cuts_sheet.jpg)
2. **Phương án B (Bản Đầy Đủ 5 Phút `300.00s` — 22 shot kịch bản nối tiếp, 70 cú cắt đa góc máy không nhảy lùi, đạt `99.2/100`):**
   - Video Ngang `16:9`: [`projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min.mp4) (và [`output/final_video.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video.mp4))
   - Video Dọc `9:16`: [`projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min_9x16.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_option_B_5min_9x16.mp4) (và [`output/final_video_9x16.mp4`](../projects/clash-of-titans-rex-vs-vasto-part-1/output/final_video_9x16.mp4))
   - Bộ 3 bảng 60 khung hình kiểm tra tính liền mạch 0s–300s của Phương án B:
     - `0s – 100s`: [`assets/qa/option_B_review_sheet_1.jpg`](../projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/option_B_review_sheet_1.jpg)
     - `100s – 200s`: [`assets/qa/option_B_review_sheet_2.jpg`](../projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/option_B_review_sheet_2.jpg)
     - `200s – 300s`: [`assets/qa/option_B_review_sheet_3.jpg`](../projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/option_B_review_sheet_3.jpg)
   - Bảng đối chiếu trực tiếp Phương án B với *Jurassic World*: [`assets/qa/benchmark_option_B_vs_jw.jpg`](../projects/clash-of-titans-rex-vs-vasto-part-1/assets/qa/benchmark_option_B_vs_jw.jpg)
