# Tiến độ: Clash of Titans: Rex vs Vasto (Part 1)

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project clash-of-titans-rex-vs-vasto-part-1 "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project clash-of-titans-rex-vs-vasto-part-1   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project clash-of-titans-rex-vs-vasto-part-1       # kiểm tra máy + in bước tiếp theo
```

Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).

Máy mới (Windows / Ubuntu) hoặc thiếu rclone / `.env`: làm theo [docs/SYNC_SETUP.md](../../docs/SYNC_SETUP.md).

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `clash-of-titans-rex-vs-vasto-part-1` — thư mục `projects/clash-of-titans-rex-vs-vasto-part-1/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/2771c196-bd45-40e4-bd63-da2daafb79d1
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `-`
- **Cập nhật lần cuối:** 2026-10-21T16:31:36 trên máy **DESKTOP-HUP72C4** (lệnh `storyboard`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 4. 🧑 Chờ người dùng duyệt storyboard

60 shot chưa có video. Storyboard chưa duyệt.

```powershell
python scripts/studio_helper.py storyboard --project clash-of-titans-rex-vs-vasto-part-1
(người dùng xem output/storyboard.html)
python scripts/studio_helper.py storyboard-approve --project clash-of-titans-rex-vs-vasto-part-1 --by "<tên>"
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | pending | - / 0 |  |  |
| 2 | shot_02 | beat_01 | pending | - / 0 |  |  |
| 3 | shot_03 | beat_01 | pending | - / 0 |  |  |
| 4 | shot_04 | beat_01 | pending | - / 0 |  |  |
| 5 | shot_05 | beat_02 | pending | - / 0 |  |  |
| 6 | shot_06 | beat_02 | pending | - / 0 |  |  |
| 7 | shot_07 | beat_02 | pending | - / 0 |  |  |
| 8 | shot_08 | beat_02 | pending | - / 0 |  |  |
| 9 | shot_09 | beat_03 | pending | - / 0 |  |  |
| 10 | shot_10 | beat_03 | pending | - / 0 |  |  |
| 11 | shot_11 | beat_03 | pending | - / 0 |  |  |
| 12 | shot_12 | beat_03 | pending | - / 0 |  |  |
| 13 | shot_13 | beat_04 | pending | - / 0 |  |  |
| 14 | shot_14 | beat_04 | pending | - / 0 |  |  |
| 15 | shot_15 | beat_04 | pending | - / 0 |  |  |
| 16 | shot_16 | beat_04 | pending | - / 0 |  |  |
| 17 | shot_17 | beat_05 | pending | - / 0 |  |  |
| 18 | shot_18 | beat_05 | pending | - / 0 |  |  |
| 19 | shot_19 | beat_05 | pending | - / 0 |  |  |
| 20 | shot_20 | beat_05 | pending | - / 0 |  |  |
| 21 | shot_21 | beat_06 | pending | - / 0 |  |  |
| 22 | shot_22 | beat_06 | pending | - / 0 |  |  |
| 23 | shot_23 | beat_06 | pending | - / 0 |  |  |
| 24 | shot_24 | beat_06 | pending | - / 0 |  |  |
| 25 | shot_25 | beat_07 | pending | - / 0 |  |  |
| 26 | shot_26 | beat_07 | pending | - / 0 |  |  |
| 27 | shot_27 | beat_07 | pending | - / 0 |  |  |
| 28 | shot_28 | beat_07 | pending | - / 0 |  |  |
| 29 | shot_29 | beat_08 | pending | - / 0 |  |  |
| 30 | shot_30 | beat_08 | pending | - / 0 |  |  |
| 31 | shot_31 | beat_08 | pending | - / 0 |  |  |
| 32 | shot_32 | beat_08 | pending | - / 0 |  |  |
| 33 | shot_33 | beat_09 | pending | - / 0 |  |  |
| 34 | shot_34 | beat_09 | pending | - / 0 |  |  |
| 35 | shot_35 | beat_09 | pending | - / 0 |  |  |
| 36 | shot_36 | beat_09 | pending | - / 0 |  |  |
| 37 | shot_37 | beat_10 | pending | - / 0 |  |  |
| 38 | shot_38 | beat_10 | pending | - / 0 |  |  |
| 39 | shot_39 | beat_10 | pending | - / 0 |  |  |
| 40 | shot_40 | beat_10 | pending | - / 0 |  |  |
| 41 | shot_41 | beat_11 | pending | - / 0 |  |  |
| 42 | shot_42 | beat_11 | pending | - / 0 |  |  |
| 43 | shot_43 | beat_11 | pending | - / 0 |  |  |
| 44 | shot_44 | beat_11 | pending | - / 0 |  |  |
| 45 | shot_45 | beat_12 | pending | - / 0 |  |  |
| 46 | shot_46 | beat_12 | pending | - / 0 |  |  |
| 47 | shot_47 | beat_12 | pending | - / 0 |  |  |
| 48 | shot_48 | beat_12 | pending | - / 0 |  |  |
| 49 | shot_49 | beat_13 | pending | - / 0 |  |  |
| 50 | shot_50 | beat_13 | pending | - / 0 |  |  |
| 51 | shot_51 | beat_13 | pending | - / 0 |  |  |
| 52 | shot_52 | beat_13 | pending | - / 0 |  |  |
| 53 | shot_53 | beat_14 | pending | - / 0 |  |  |
| 54 | shot_54 | beat_14 | pending | - / 0 |  |  |
| 55 | shot_55 | beat_14 | pending | - / 0 |  |  |
| 56 | shot_56 | beat_14 | pending | - / 0 |  |  |
| 57 | shot_57 | beat_15 | pending | - / 0 |  |  |
| 58 | shot_58 | beat_15 | pending | - / 0 |  |  |
| 59 | shot_59 | beat_15 | pending | - / 0 |  |  |
| 60 | shot_60 | beat_15 | pending | - / 0 |  |  |

## Beat & lời dẫn

- **beat_01** (hook) — 
- **beat_02** (escalation) — 
- **beat_03** (arena_bridge_to_marsh) — 
- **beat_04** (escalation) — 
- **beat_05** (reversal_1_marsh_knockdown) — 
- **beat_06** (arena_bridge_to_shoreline) — 
- **beat_07** (escalation) — 
- **beat_08** (reversal_2_shoreline_leverage) — 
- **beat_09** (arena_bridge_hurl_into_sea) — 
- **beat_10** (escalation) — 
- **beat_11** (reversal_3_sea_submersion_and_counter) — 
- **beat_12** (arena_bridge_to_reef_spit) — 
- **beat_13** (climax_death_clamp) — 
- **beat_14** (climax_finisher_into_deep_sea) — 
- **beat_15** (resolution_apex_roar) — 

## Media trên máy này

⚠ Máy **DESKTOP-HUP72C4** thiếu 60/126 file — chạy `media-pull` (hoặc tải lại take từ Flow).

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
- `assets/clips/shot_16.mp4` — shot_16 clip dựng
- `assets/clips/shot_17.mp4` — shot_17 clip dựng
- `assets/clips/shot_18.mp4` — shot_18 clip dựng
- `assets/clips/shot_19.mp4` — shot_19 clip dựng
- `assets/clips/shot_20.mp4` — shot_20 clip dựng
- `assets/clips/shot_21.mp4` — shot_21 clip dựng
- `assets/clips/shot_22.mp4` — shot_22 clip dựng
- `assets/clips/shot_23.mp4` — shot_23 clip dựng
- `assets/clips/shot_24.mp4` — shot_24 clip dựng
- `assets/clips/shot_25.mp4` — shot_25 clip dựng
- … và 35 file khác

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-21 16:31 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-21 16:29 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait` | ok |
| 10-21 16:23 | DESKTOP-HUP72C4 | `flow-generate --kind frames --model Nano Banana Pro --count 1 --shots shot_25,shot_26,shot_27,shot_28,shot_29,shot_30,shot_31,shot_32,shot_33,shot_34,shot_35,shot_36,shot_37,` | ok |
| 10-21 16:14 | DESKTOP-HUP72C4 | `lint-prompts --strict` | ok |
| 10-21 16:14 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 16:09 | DESKTOP-HUP72C4 | `flow-harvest --kind image` | ok |
| 10-21 16:05 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait` | ok |
| 10-21 16:02 | DESKTOP-HUP72C4 | `flow-generate --kind frames --model Nano Banana Pro --count 1 --shots shot_01,shot_02,shot_03,shot_04,shot_05,shot_06,shot_07,shot_08,shot_09,shot_10,shot_11,shot_12,shot_13,` | ok |
| 10-21 15:55 | DESKTOP-HUP72C4 | `flow-harvest --kind image` | ok |
| 10-21 15:53 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_12` | ok |
| 10-21 15:49 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait` | ok |
| 10-21 15:46 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_01,shot_02,shot_03,shot_04,shot_05,shot_06,shot_07,shot_08,shot_09,shot_10,shot_11,shot_12 --count 1` | ok |
| 10-21 15:41 | DESKTOP-HUP72C4 | `audit-assets ` | ok |
| 10-21 15:40 | DESKTOP-HUP72C4 | `audit-assets ` | ok |
| 10-21 15:40 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait` | ok |
