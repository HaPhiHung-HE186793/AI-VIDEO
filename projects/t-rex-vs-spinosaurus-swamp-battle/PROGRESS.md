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
- **Cập nhật lần cuối:** 2026-10-20T22:10:29 trên máy **DESKTOP-HUP72C4** (lệnh `media-push`)
- **Storyboard:** đã duyệt (19f65ca1104f15fc)

## ▶ Bước tiếp theo: 11. Xong — chờ người dùng đăng / yêu cầu mới

Bản cuối: output/final_video.mp4

```powershell
python scripts/studio_helper.py publish-kit --project t-rex-vs-spinosaurus-swamp-battle
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | qa_pass | 2 / 2 | ✓ | 1.67–6.32 |
| 2 | shot_02 | beat_01 | qa_pass | 2 / 2 | ✓ | 1.67–6.32 |
| 3 | shot_03 | beat_02 | qa_pass | 2 / 2 | ✓ | 1.67–6.32 |
| 4 | shot_04 | beat_02 | qa_pass | 2 / 2 | ✓ | 1.67–6.32 |
| 5 | shot_05 | beat_03 | qa_pass | 1 / 2 | ✓ | 1.67–6.32 |
| 6 | shot_06a | beat_03 | qa_pass | 1 / 2 | ✓ | 3.15–8.00 |
| 7 | shot_06b | beat_03 | qa_pass | 2 / 2 | ✓ | 0.00–4.85 |
| 8 | shot_07 | beat_04 | qa_pass | 1 / 2 | ✓ | 1.67–6.32 |
| 9 | shot_08 | beat_04 | qa_pass | 2 / 2 | ✓ | 1.67–6.32 |

## Beat & lời dẫn

- **beat_01** (Hook & Standoff: Spinosaurus erupts from the storm swamp and T. rex answers with a shockwave roar) — 
- **beat_02** (First Clash: Full-speed swamp collision and Spinosaurus forelimb claw slash) — 
- **beat_03** (Escalation & Counter: Spinosaurus shatters a burning cypress trunk; T. rex ducks and clamps Spinosaurus's neck) — 
- **beat_04** (Climax & Finisher: T. rex slams Spinosaurus into a massive 3D water geyser and roars in victory) — 

## Đầu ra gần nhất

- `output/final_video.mp4` (2026-10-20 22:07)

## Media trên máy này

Đủ 52/52 file media trên máy **DESKTOP-HUP72C4**.

## Quyết định & ghi chú bàn giao

- 2026-10-20 21:19 · DESKTOP-HUP72C4 · decision: Người dùng duyệt storyboard (18/18 Keyframes START+END) và đồng ý chi 1.620 credits tạo 9 sub-shot video.

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 22:10 | DESKTOP-HUP72C4 | `media-push ` | ❌ ManifestError: Chưa đặt thư mục chung: thêm STUDIO_MEDIA_DIR=rclone:gdrive:AI-vi |
| 10-20 22:07 | DESKTOP-HUP72C4 | `assemble --format landscape` | ok |
| 10-20 22:06 | DESKTOP-HUP72C4 | `qa ` | ok |
| 10-20 22:05 | DESKTOP-HUP72C4 | `flow-upscale ` | ok |
| 10-20 21:51 | DESKTOP-HUP72C4 | `thumbnail --title T-REX VS SPINOSAURUS --subtitle 3D SWAMP BATTLE` | ok |
| 10-20 21:51 | DESKTOP-HUP72C4 | `make-lut --preset documentary` | ok |
| 10-20 21:51 | DESKTOP-HUP72C4 | `score --mood tension` | ok |
| 10-20 21:50 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-20 21:50 | DESKTOP-HUP72C4 | `qa-takes-submit --reviewer agent` | ok |
| 10-20 21:49 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01 --force --reviewer agent` | ok |
| 10-20 21:43 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01,shot_06a --force --reviewer agent` | ok |
| 10-20 21:43 | DESKTOP-HUP72C4 | `flow-harvest --kind video --shots shot_06a --all` | ok |
| 10-20 21:39 | DESKTOP-HUP72C4 | `flow-harvest --kind video --shots shot_06a --all` | ok |
| 10-20 21:33 | DESKTOP-HUP72C4 | `flow-harvest --kind video --shots shot_06a --all` | ok |
| 10-20 21:33 | DESKTOP-HUP72C4 | `qa-takes --reviewer agent` | ok |
