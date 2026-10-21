# Báo Cáo Đối Chiếu Chuẩn Hollywood (`benchmark-compare`) — Phương Án A & Phương Án B

> Tài liệu chi tiết đầy đủ được lưu tại: [`docs/BATTLE_BENCHMARK_AND_FIX_HISTORY.md`](../../docs/BATTLE_BENCHMARK_AND_FIX_HISTORY.md)

## So Sánh Trực Tiếp Phương Án A (`100.54s`) và Phương Án B (`300.00s`)

| Tiêu chí | **Phương án A (`final_video_option_A.mp4`)** | **Phương án B (`final_video_option_B_5min.mp4`)** | Mẫu *Jurassic World* (`FtCslvCjZEY`) |
| :--- | :---: | :---: | :---: |
| **Triết lý dựng** | Tinh gọn 1-take/shot qua 14 shot cốt lõi (`wide_master` 100%) | Đầy đủ 5 phút (`300.0s`) qua 22 shot nối mạch (44 takes chia nửa không lặp cảnh) | Đại chiến 5 hồi (`300.0s`) |
| **Thời lượng thực tế** | `100.54s` (1 phút 40 giây) | **`300.00s` (5 phút 00 giây)** | `300.00s` |
| **Số cú cắt (`Cut Count` / `ASL`)** | `14 cuts` (`ASL = 7.18s`) | **`70 cuts` (`ASL = 4.29s`)** | `~68 cuts` (`ASL = 4.41s`) |
| **Tính liền mạch (`backward_jumps` / `revisits`)** | **`0` nhảy lùi / `0` lặp cảnh (`100.0/100`)** | **`0` nhảy lùi / `0` lặp cảnh (`100.0/100`)** | `0 / 0` (`100.0/100`) |
| **Ánh sáng (`Mean Luma` / `Dark Ratio`)** | `11.98` / `94.9%` | **`19.94` / `87.5%` (`98.0/100`)** | `19.15` / `89.0%` |
| **Độ phủ 6 Góc Máy Biểu Tượng** | **`6 / 6` (`100.0/100`)** | **`6 / 6` (`100.0/100`)** | `6 / 6` (`100.0/100`) |
| **TỔNG ĐIỂM (`overall_similarity_score_100`)** | **`91.5 / 100`** | **`99.2 / 100` (`PASS_HOLLYWOOD_BENCHMARK`)** | **`100.0 / 100`** |
| **File Video `16:9`** | [`output/final_video_option_A.mp4`](output/final_video_option_A.mp4) | [`output/final_video_option_B_5min.mp4`](output/final_video_option_B_5min.mp4) | — |
| **File Video `9:16`** | [`output/final_video_option_A_9x16.mp4`](output/final_video_option_A_9x16.mp4) | [`output/final_video_option_B_5min_9x16.mp4`](output/final_video_option_B_5min_9x16.mp4) | — |
| **Bảng Contact Sheet kiểm tra** | [`assets/qa/option_A_14_cuts_sheet.jpg`](assets/qa/option_A_14_cuts_sheet.jpg) | [`option_B_review_sheet_1.jpg`](assets/qa/option_B_review_sheet_1.jpg), [`2.jpg`](assets/qa/option_B_review_sheet_2.jpg), [`3.jpg`](assets/qa/option_B_review_sheet_3.jpg) | [`assets/qa/benchmark_option_B_vs_jw.jpg`](assets/qa/benchmark_option_B_vs_jw.jpg) |
