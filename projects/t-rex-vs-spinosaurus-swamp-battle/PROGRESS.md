# Tiến độ: T-Rex vs Spinosaurus Swamp Battle

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project t-rex-vs-spinosaurus-swamp-battle "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project t-rex-vs-spinosaurus-swamp-battle   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project t-rex-vs-spinosaurus-swamp-battle       # kiểm tra máy + in bước tiếp theo
```

Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).

Máy mới (Windows / Ubuntu) hoặc thiếu rclone / `.env`: làm theo [docs/SYNC_SETUP.md](../../docs/SYNC_SETUP.md).

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `t-rex-vs-spinosaurus-swamp-battle` — thư mục `projects/t-rex-vs-spinosaurus-swamp-battle/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/6d4a0c22-1a61-47bc-aac8-d2224a0dcbc2
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `-`
- **Cập nhật lần cuối:** 2026-10-20T21:16:04 trên máy **DESKTOP-HUP72C4** (lệnh `storyboard`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 4. 🧑 Chờ người dùng duyệt storyboard

9 shot chưa có video. Storyboard chưa duyệt.

```powershell
python scripts/studio_helper.py storyboard --project t-rex-vs-spinosaurus-swamp-battle
(người dùng xem output/storyboard.html)
python scripts/studio_helper.py storyboard-approve --project t-rex-vs-spinosaurus-swamp-battle --by "<tên>"
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | pending | - / 0 |  |  |
| 2 | shot_02 | beat_01 | pending | - / 0 |  |  |
| 3 | shot_03 | beat_02 | pending | - / 0 |  |  |
| 4 | shot_04 | beat_02 | pending | - / 0 |  |  |
| 5 | shot_05 | beat_03 | pending | - / 0 |  |  |
| 6 | shot_06a | beat_03 | pending | - / 0 |  |  |
| 7 | shot_06b | beat_03 | pending | - / 0 |  |  |
| 8 | shot_07 | beat_04 | pending | - / 0 |  |  |
| 9 | shot_08 | beat_04 | pending | - / 0 |  |  |

## Beat & lời dẫn

- **beat_01** (Hook & Standoff: Spinosaurus erupts from the storm swamp and T. rex answers with a shockwave roar) — 
- **beat_02** (First Clash: Full-speed swamp collision and Spinosaurus forelimb claw slash) — 
- **beat_03** (Escalation & Counter: Spinosaurus shatters a burning cypress trunk; T. rex ducks and clamps Spinosaurus's neck) — 
- **beat_04** (Climax & Finisher: T. rex slams Spinosaurus into a massive 3D water geyser and roars in victory) — 

## Media trên máy này

⚠ Máy **DESKTOP-HUP72C4** thiếu 9/32 file — chạy `media-pull` (hoặc tải lại take từ Flow).

- `assets/clips/shot_01.mp4` — shot_01 clip dựng
- `assets/clips/shot_02.mp4` — shot_02 clip dựng
- `assets/clips/shot_03.mp4` — shot_03 clip dựng
- `assets/clips/shot_04.mp4` — shot_04 clip dựng
- `assets/clips/shot_05.mp4` — shot_05 clip dựng
- `assets/clips/shot_06a.mp4` — shot_06a clip dựng
- `assets/clips/shot_06b.mp4` — shot_06b clip dựng
- `assets/clips/shot_07.mp4` — shot_07 clip dựng
- `assets/clips/shot_08.mp4` — shot_08 clip dựng

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 21:16 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-20 21:16 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_01 --all` | ok |
| 10-20 21:11 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-20 21:11 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_07,shot_08 --wait --wait-timeout 180` | ok |
| 10-20 21:11 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-20 21:11 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_06a,shot_06b,shot_07,shot_08 --wait --wait-timeout 300` | ok |
| 10-20 21:10 | DESKTOP-HUP72C4 | `flow-generate --kind frames --count 2 --shots shot_06a,shot_06b,shot_07,shot_08` | ok |
| 10-20 21:09 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_07,shot_08 --wait --wait-timeout 180` | ok |
| 10-20 21:08 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-20 21:08 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait --wait-timeout 420` | ok |
| 10-20 21:07 | DESKTOP-HUP72C4 | `flow-generate --kind frames --count 2` | ok |
| 10-20 21:05 | DESKTOP-HUP72C4 | `flow-harvest --kind image --wait --wait-timeout 420` | ok |
| 10-20 21:05 | DESKTOP-HUP72C4 | `flow-generate --kind frames --count 2` | ok |
| 10-20 21:02 | DESKTOP-HUP72C4 | `audit-assets ` | ok |
| 10-20 21:01 | DESKTOP-HUP72C4 | `audit-assets ` | ok |
