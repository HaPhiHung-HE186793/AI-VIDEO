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
- **Cập nhật lần cuối:** 2026-10-20T13:32:05 trên máy **user** (lệnh `lint-prompts`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 4. 🧑 Chờ người dùng duyệt storyboard

15 shot chưa có video. Storyboard chưa duyệt.

```powershell
python scripts/studio_helper.py storyboard --project podcast-giac-mo-thiep-cuoi
(người dùng xem output/storyboard.html)
python scripts/studio_helper.py storyboard-approve --project podcast-giac-mo-thiep-cuoi --by "<tên>"
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | b01_hook | pending | - / 0 |  |  |
| 2 | shot_02 | b01_hook | pending | - / 0 |  |  |
| 3 | shot_03 | b02_rooftop_reunion | pending | - / 0 |  |  |
| 4 | shot_04 | b02_rooftop_reunion | pending | - / 0 |  |  |
| 5 | shot_05 | b03_mystery_bride | pending | - / 0 |  |  |
| 6 | shot_06 | b03_mystery_bride | pending | - / 0 |  |  |
| 7 | shot_07 | b04_tease_and_silence | pending | - / 0 |  |  |
| 8 | shot_08 | b04_tease_and_silence | pending | - / 0 |  |  |
| 9 | shot_09 | b05_wife_bombshell | pending | - / 0 |  |  |
| 10 | shot_10 | b05_wife_bombshell | pending | - / 0 |  |  |
| 11 | shot_11 | b06_clone_acc_and_missing_card | pending | - / 0 |  |  |
| 12 | shot_12 | b06_clone_acc_and_missing_card | pending | - / 0 |  |  |
| 13 | shot_13 | b07_sulking_paparazzi | pending | - / 0 |  |  |
| 14 | shot_14 | b08_alarm_and_psa | pending | - / 0 |  |  |
| 15 | shot_15 | b08_alarm_and_psa | pending | - / 0 |  |  |

## Beat & lời dẫn

- **b01_hook** (hook) 🔊 Uhm, sắp trưa đang nghỉ rảnh rỗi, tự nhiên nhớ lại quả giấc mơ vô tri đêm qua làm sáng dậy tao lú mất năm phút, vừa cay vừa buồn cười không chịu được nên phải kể ngay cho bọn mày nghe!
- **b02_rooftop_reunion** (need) 🔊 Đêm qua tao mơ thấy cả hội mình gặp lại nhau sau bao lâu ra trường ở một quán cà phê rooftop quen quen. Tao hí hửng đẩy cửa bước vào, thấy nguyên bàn dài toàn mặt chúng mày đang ngồi cười nói rôm rả như chưa hề có cuộc chia ly.
- **b03_mystery_bride** (senses) 🔊 Tao phi lại gần định vỗ vai chào từng thằng thì đập ngay vào mắt là cu Vũ Tấn ngồi chễm chệ giữa bàn, bên cạnh là một em gái nhìn dịu dàng, ngoan hiền cực kỳ. Mơ nên ảo lắm, chỉ còn nhớ cảm giác tóc đen dài, cười nhẹ nhàng thôi.
- **b04_tease_and_silence** (target) 🔊 Tao mới trêu: uầy khá nhỉ, thấy Việt Đức, Nguyễn Phong, Quang Bình tiên phong rồi, tới Hoàng Anh, Việt Đường, Phi Hùng, Nhật Anh cũng khởi sắc nên nay Tấn cũng gia nhập đường đua, giấu kỹ thế nay mới ra mắt à? Ngay sau câu đấy cả bọn im phăng phắc, nhìn tao như người từ hành tinh khác rơi xuống!
- **b05_wife_bombshell** (escalation) 🔊 Hoàng Anh với Việt Đường ngồi cạnh phì cười vừa đấm vừa xoa vai tao: Người yêu cái đầu mày! Vợ nó đấy, hai đứa vừa đi tuần trăng mật về tuần trước, ngơ vãi Đạt đụt! Tao đứng hình luôn, còn Vũ Tấn phởn phơ gật đầu cái rụp, vợ nó thì cười ngại ngại như chuyện bình thường lắm rồi!
- **b06_clone_acc_and_missing_card** (escalation) 🔊 Xong cả bọn dí điện thoại vào mặt tao cho xem tài khoản phụ của Tấn đăng cả bộ sưu tập ảnh cưới mà tao không hề biết. Tao quay ra hỏi: ủa thế thiệp cưới tao đâu? Cả lũ cười khẩy kiểu: ơ em không được mời à, hẹ hẹ!
- **b07_sulking_paparazzi** (climax) 🔊 Tao giãy nảy lên ăn vạ bất lực, vợ chồng Tấn rối rít dỗ dành đáng yêu cực, còn Nguyễn Phong với Duy Khiêm giơ máy quay cảnh tao ngồi dỗi đập bàn cười hô hố!
- **b08_alarm_and_psa** (resolution) 🔊 Đang định chốt kèo bù thì tíng tình tình tính ting, báo thức sáu giờ ba mươi lăm réo vang, mở mắt ra là cái trần nhà hụt hẫng! Qua giấc mơ này tao cảnh báo toàn thể anh em: sau này đứa nào cưới nhớ gửi tao tấm thiệp hồng để xác nhận tình anh em còn tồn tại nhé!

## Media trên máy này

⚠ Máy **user** thiếu 15/51 file — chạy `media-pull` (hoặc tải lại take từ Flow).

- `assets/clips/shot_01.mp4` — shot_01 clip dựng
- `assets/clips/shot_02.mp4` — shot_02 clip dựng
- `assets/clips/shot_03.mp4` — shot_03 clip dựng
- `assets/clips/shot_04.mp4` — shot_04 clip dựng
- `assets/clips/shot_05.mp4` — shot_05 clip dựng
- `assets/clips/shot_06.mp4` — shot_06 clip dựng
- `assets/clips/shot_07.mp4` — shot_07 clip dựng
- `assets/clips/shot_08.mp4` — shot_08 clip dựng
- `assets/clips/shot_09.mp4` — shot_09 clip dựng
- `assets/clips/shot_10.mp4` — shot_10 clip dựng
- `assets/clips/shot_11.mp4` — shot_11 clip dựng
- `assets/clips/shot_12.mp4` — shot_12 clip dựng
- `assets/clips/shot_13.mp4` — shot_13 clip dựng
- `assets/clips/shot_14.mp4` — shot_14 clip dựng
- `assets/clips/shot_15.mp4` — shot_15 clip dựng

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 13:32 | user | `lint-prompts --strict` | ok |
| 10-20 13:31 | user | `storyboard ` | ok |
| 10-20 13:31 | user | `voiceover ` | ok |
| 10-20 13:31 | user | `build-prompts ` | ok |
| 10-20 13:28 | user | `voiceover ` | ok |
| 10-20 13:23 | user | `storyboard ` | ok |
| 10-20 13:20 | user | `storyboard ` | ok |
| 10-20 13:20 | user | `flow-harvest --kind image --shots shot_14,shot_15` | ok |
| 10-20 13:19 | user | `storyboard ` | ok |
| 10-20 13:19 | user | `flow-harvest --kind image --wait` | ok |
| 10-20 13:16 | user | `flow-generate --kind frames --count 2` | ok |
| 10-20 13:13 | user | `flow-harvest --kind image --wait` | ok |
| 10-20 13:08 | user | `flow-harvest --kind image --wait` | ❌ TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for |
| 10-20 13:08 | user | `voiceover ` | ok |
| 10-20 13:08 | user | `flow-generate --kind frames --shots shot_03,shot_05,shot_07,shot_09,shot_10,shot_11,shot_12,shot_13,shot_14,shot_15 --count 2` | ok |
