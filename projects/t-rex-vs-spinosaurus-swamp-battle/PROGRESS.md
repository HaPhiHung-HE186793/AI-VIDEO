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
- **Flow:** https://flow.google.com/project/5e06c00b-e4b1-4460-b012-4454fd94fa25
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `-`
- **Cập nhật lần cuối:** 2026-10-21T09:44:54 trên máy **DESKTOP-HUP72C4** (lệnh `lint-prompts`)
- **Storyboard:** đã sửa sau khi duyệt (cần duyệt lại: a131d8bc0bb5097d)

## ▶ Bước tiếp theo: 5. Tải kết quả Flow đang tạo dở

Đã gửi tạo nhưng CHƯA tải về: shot_01, shot_02, shot_04b (image). Kết quả nằm sẵn trên Flow (cùng tài khoản Google) — KHÔNG gửi tạo lại (mất credit).

```powershell
python scripts/studio_helper.py flow-harvest --project t-rex-vs-spinosaurus-swamp-battle --kind image --wait
```

### ⚠ Job Flow đang tạo dở (đã tiêu credit, chưa tải)

| Shot | Loại | Model | Số bản | Credit | Gửi lúc |
|---|---|---|---|---|---|
| shot_01 | image | Nano Banana Pro | 2 | 0 | 2026-10-21T01:41:42 |
| shot_02 | image | Nano Banana Pro | 2 | 0 | 2026-10-21T01:41:52 |
| shot_04b | image | Nano Banana Pro | 2 | 0 | 2026-10-21T01:42:05 |

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | pending | - / 0 |  | 1.84–5.59 |
| 2 | shot_02 | beat_01 | pending | - / 0 |  | 2.76–6.11 |
| 3 | shot_02b | beat_01 | pending | - / 0 |  | 2.43–4.18 |
| 4 | shot_03 | beat_02 | pending | - / 0 |  | 1.51–4.46 |
| 5 | shot_04 | beat_02 | pending | - / 0 |  | 1.14–3.49 |
| 6 | shot_04b | beat_02 | pending | - / 0 |  | 2.51–4.46 |
| 7 | shot_05 | beat_03 | pending | - / 0 |  | 3.18–6.13 |
| 8 | shot_06a | beat_03 | pending | - / 0 |  | 5.25–8.00 |
| 9 | shot_06b | beat_03 | pending | - / 0 |  | 0.00–2.75 |
| 10 | shot_06c | beat_03 | pending | - / 0 |  | 4.31–6.16 |
| 11 | shot_07 | beat_04 | pending | - / 0 |  | 0.88–4.43 |
| 12 | shot_08 | beat_04 | pending | - / 0 |  | 3.42–7.37 |

## Beat & lời dẫn

- **beat_01** (Hook & Standoff: Spinosaurus erupts from the storm swamp and T. rex answers with a shockwave roar) — 
- **beat_02** (First Clash: Full-speed swamp collision and Spinosaurus forelimb claw slash) — 
- **beat_03** (Escalation & Counter: Spinosaurus shatters a burning cypress trunk; T. rex ducks and clamps Spinosaurus's neck) — 
- **beat_04** (Climax & Finisher: T. rex slams Spinosaurus into a massive 3D water geyser and roars in victory) — 

## Đầu ra gần nhất

- `output/final_video.mp4` (2026-10-20 23:16)
- `output/final_video_v3_ilm_master.mp4` (2026-10-20 23:16)
- `output/final_video_v2_blockbuster.mp4` (2026-10-20 22:37)

## Media trên máy này

⚠ Máy **DESKTOP-HUP72C4** thiếu 12/43 file — chạy `media-pull` (hoặc tải lại take từ Flow).

- `assets/clips/shot_01.mp4` — shot_01 clip dựng
- `assets/clips/shot_02.mp4` — shot_02 clip dựng
- `assets/clips/shot_02b.mp4` — shot_02b clip dựng
- `assets/clips/shot_03.mp4` — shot_03 clip dựng
- `assets/clips/shot_04.mp4` — shot_04 clip dựng
- `assets/clips/shot_04b.mp4` — shot_04b clip dựng
- `assets/clips/shot_05.mp4` — shot_05 clip dựng
- `assets/clips/shot_06a.mp4` — shot_06a clip dựng
- `assets/clips/shot_06b.mp4` — shot_06b clip dựng
- `assets/clips/shot_06c.mp4` — shot_06c clip dựng
- `assets/clips/shot_07.mp4` — shot_07 clip dựng
- `assets/clips/shot_08.mp4` — shot_08 clip dựng

## Quyết định & ghi chú bàn giao

- 2026-10-20 21:19 · DESKTOP-HUP72C4 · decision: Người dùng duyệt storyboard (18/18 Keyframes START+END) và đồng ý chi 1.620 credits tạo 9 sub-shot video.

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-21 09:44 | DESKTOP-HUP72C4 | `lint-prompts ` | ok |
| 10-21 09:44 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 09:22 | DESKTOP-HUP72C4 | `lint-prompts ` | ok |
| 10-21 09:22 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 08:48 | DESKTOP-HUP72C4 | `flow-storyboard --grid 3x3 --slice-only` | ok |
| 10-21 08:46 | DESKTOP-HUP72C4 | `flow-storyboard --grid 3x3 --harvest-only` | ok |
| 10-21 08:42 | DESKTOP-HUP72C4 | `flow-storyboard --grid 3x3 --count 2` | ❌ [ERROR] Ch?a c? ?nh Storyboard Grid t?i D:\myProject\AI-video\projects\t-rex-vs- |
| 10-21 08:40 | DESKTOP-HUP72C4 | `flow-storyboard --grid 3x3 --count 2` | ❌ AttributeError: module 'studio.manifest' has no attribute '_project_prefix' |
| 10-21 08:39 | DESKTOP-HUP72C4 | `flow-storyboard --grid 3x3 --count 2` | ❌ AttributeError: module 'studio.manifest' has no attribute 'project_prefix' |
| 10-21 02:27 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-21 02:26 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_06c --wait` | ok |
| 10-21 02:25 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_06c --count 2` | ok |
| 10-21 02:24 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 02:19 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-21 02:18 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_01,shot_02,shot_04b --wait` | ok |
