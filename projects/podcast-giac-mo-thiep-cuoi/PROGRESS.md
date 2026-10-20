# Tiến độ: podcast-giac-mo-thiep-cuoi

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project podcast-giac-mo-thiep-cuoi "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project podcast-giac-mo-thiep-cuoi   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project podcast-giac-mo-thiep-cuoi       # kiểm tra máy + in bước tiếp theo
```

Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).

Máy mới (Windows / Ubuntu) hoặc thiếu rclone / `.env`: làm theo [docs/SYNC_SETUP.md](../../docs/SYNC_SETUP.md).

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `podcast-giac-mo-thiep-cuoi` — thư mục `projects/podcast-giac-mo-thiep-cuoi/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/ae209c27-c53b-44e4-b736-245f059d3ba1
- **Ngôn ngữ / khung:** vi / 16:9; giọng dẫn `Charon`
- **Cập nhật lần cuối:** 2026-10-20T16:17:13 trên máy **user** (lệnh `assemble`)
- **Storyboard:** đã duyệt (2ca588ba998c18d0)

## ▶ Bước tiếp theo: 5. Tải kết quả Flow đang tạo dở

Đã gửi tạo nhưng CHƯA tải về: shot_10 (video). Kết quả nằm sẵn trên Flow (cùng tài khoản Google) — KHÔNG gửi tạo lại (mất credit).

```powershell
python scripts/studio_helper.py flow-harvest --project podcast-giac-mo-thiep-cuoi --kind video --wait
```

### ⚠ Job Flow đang tạo dở (đã tiêu credit, chưa tải)

| Shot | Loại | Model | Số bản | Credit | Gửi lúc |
|---|---|---|---|---|---|
| shot_10 | video | Veo 3.1 - Fast | 2 | 20 | 2026-10-20T15:16:03 |

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | b01_hook | approved | 1 / 2 |  | 3.26–8.00 |
| 2 | shot_02 | b01_hook | approved | 1 / 1 |  | 0.00–4.74 |
| 3 | shot_03 | b02_rooftop_reunion | approved | 2 / 2 |  | 2.45–8.00 |
| 4 | shot_04 | b02_rooftop_reunion | approved | 1 / 2 |  | 0.00–5.55 |
| 5 | shot_05 | b03_mystery_bride | approved | 2 / 2 |  | 1.76–8.00 |
| 6 | shot_06 | b03_mystery_bride | approved | 1 / 1 |  | 0.00–6.24 |
| 7 | shot_07 | b04_tease_and_silence | approved | 2 / 2 |  | 0.13–8.00 |
| 8 | shot_08 | b04_tease_and_silence | approved | 1 / 1 |  | 0.00–7.87 |
| 9 | shot_09 | b05_wife_bombshell | approved | 1 / 2 |  | 0.46–7.53 |
| 10 | shot_10 | b05_wife_bombshell | approved | 1 / 2 |  | 0.46–7.53 |
| 11 | shot_11 | b06_clone_acc_and_missing_card | approved | 1 / 1 |  | 1.13–6.87 |
| 12 | shot_12 | b06_clone_acc_and_missing_card | approved | 1 / 2 |  | 1.13–6.87 |
| 13 | shot_13 | b07_sulking_paparazzi | approved | 1 / 1 |  | 0.03–7.97 |
| 14 | shot_14 | b08_alarm_and_psa | approved | 1 / 2 |  | 0.67–7.34 |
| 15 | shot_15 | b08_alarm_and_psa | approved | 2 / 2 |  | 0.67–7.34 |

## Beat & lời dẫn

- **b01_hook** (hook) 🔊 Uhm, sắp trưa đang nghỉ rảnh rỗi, tự nhiên nhớ lại quả giấc mơ vô tri đêm qua làm sáng dậy tao lú mất năm phút, vừa cay vừa buồn cười không chịu được nên phải kể ngay cho bọn mày nghe!
- **b02_rooftop_reunion** (need) 🔊 Đêm qua tao mơ thấy cả hội mình gặp lại nhau sau bao lâu ra trường ở một quán cà phê rooftop quen quen. Tao hí hửng đẩy cửa bước vào, thấy nguyên bàn dài toàn mặt chúng mày đang ngồi cười nói rôm rả như chưa hề có cuộc chia ly.
- **b03_mystery_bride** (senses) 🔊 Tao phi lại gần định vỗ vai chào từng thằng thì đập ngay vào mắt là cu Vũ Tấn ngồi chễm chệ giữa bàn, bên cạnh là một em gái nhìn dịu dàng, ngoan hiền cực kỳ. Mơ nên ảo lắm, chỉ còn nhớ cảm giác tóc đen dài, cười nhẹ nhàng thôi.
- **b04_tease_and_silence** (target) 🔊 Tao mới trêu: uầy khá nhỉ, thấy Việt Đức, Nguyễn Phong, Quang Bình tiên phong rồi, tới Hoàng Anh, Việt Đường, Phi Hùng, Nhật Anh cũng khởi sắc nên nay Tấn cũng gia nhập đường đua, giấu kỹ thế nay mới ra mắt à? Ngay sau câu đấy cả bọn im phăng phắc, nhìn tao như người từ hành tinh khác rơi xuống!
- **b05_wife_bombshell** (escalation) 🔊 Hoàng Anh với Việt Đường ngồi cạnh phì cười vừa đấm vừa xoa vai tao: Người yêu cái đầu mày! Vợ nó đấy, hai đứa vừa đi tuần trăng mật về tuần trước, ngơ vãi Đạt đụt! Tao đứng hình luôn, còn Vũ Tấn phởn phơ gật đầu cái rụp, vợ nó thì cười ngại ngại như chuyện bình thường lắm rồi!
- **b06_clone_acc_and_missing_card** (escalation) 🔊 Xong cả bọn dí điện thoại vào mặt tao cho xem tài khoản phụ của Tấn đăng cả bộ sưu tập ảnh cưới mà tao không hề biết. Tao quay ra hỏi: ủa thế thiệp cưới tao đâu? Cả lũ cười khẩy kiểu: ơ em không được mời à, hẹ hẹ!
- **b07_sulking_paparazzi** (climax) 🔊 Tao giãy nảy lên ăn vạ bất lực, vợ chồng Tấn rối rít dỗ dành đáng yêu cực, còn Nguyễn Phong với Duy Khiêm giơ máy quay cảnh tao ngồi dỗi đập bàn cười hô hố!
- **b08_alarm_and_psa** (resolution) 🔊 Đang định chốt kèo bù thì tíng tình tình tính ting, báo thức sáu giờ ba mươi lăm réo vang, mở mắt ra là cái trần nhà hụt hẫng! Qua giấc mơ này tao cảnh báo toàn thể anh em: sau này đứa nào cưới nhớ gửi tao tấm thiệp hồng để xác nhận tình anh em còn tồn tại nhé!

## Đầu ra gần nhất

- `output/final_video.mp4` (2026-10-20 16:17)

## Media trên máy này

Đủ 73/73 file media trên máy **user**.

## Quyết định & ghi chú bàn giao

- 2026-10-20 15:43 · user · decision: Hoàn tất kết xuất final_video.mp4 (98.38s, 1920x1080, -14.0 LUFS, 3 lớp âm thanh + phụ đề in cứng) bằng quy trình 100% Keyframe-First (30 START/END frames) + Daisy-Chain bảo toàn biên nối + Hybrid Audio.

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 16:17 | user | `assemble --burn-subs` | ok |
| 10-20 16:16 | user | `score ` | ok |
| 10-20 16:16 | user | `approve --shots shot_01,shot_02,shot_03,shot_04,shot_05,shot_06,shot_07,shot_08,shot_09,shot_10,shot_11,shot_12,shot_13,shot_14,shot_15` | ok |
| 10-20 16:16 | user | `auto-select ` | ok |
| 10-20 16:12 | user | `assemble --burn-subs` | ok |
| 10-20 16:11 | user | `score ` | ok |
| 10-20 16:11 | user | `storyboard-approve ` | ok |
| 10-20 16:11 | user | `storyboard ` | ok |
| 10-20 16:11 | user | `storyboard-approve ` | ❌ [ERROR] Nội dung đã đổi từ lần xuất storyboard gần nhất — chạy `storyboard` và x |
| 10-20 16:10 | user | `lint-prompts ` | ok |
| 10-20 16:10 | user | `build-prompts ` | ok |
| 10-20 15:43 | user | `note ` | ok |
| 10-20 15:42 | user | `thumbnail --shot shot_15 --at 5.2 --title GIẤC MƠ VÔ TRI --subtitle VŨ TẤN CƯỚI VỢ & THIỆP HỒNG BỊ BỎ QUÊN` | ok |
| 10-20 15:42 | user | `approve --shots shot_01,shot_02,shot_03,shot_04,shot_05,shot_06,shot_07,shot_08,shot_09,shot_10,shot_11,shot_12,shot_13,shot_14,shot_15` | ok |
| 10-20 15:42 | user | `assemble --burn-subs` | ok |
