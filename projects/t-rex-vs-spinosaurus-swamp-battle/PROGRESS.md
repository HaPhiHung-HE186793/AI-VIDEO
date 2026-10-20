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
- **Cập nhật lần cuối:** 2026-10-21T00:33:01 trên máy **DESKTOP-HUP72C4** (lệnh `lint-prompts`)
- **Storyboard:** đã sửa sau khi duyệt (cần duyệt lại: 4104a924f329a648)

## ▶ Bước tiếp theo: 7. Upscale 1080p

Còn 720p: shot_01, shot_02, shot_02b, shot_03, shot_04, shot_04b, shot_05, shot_06a, shot_06b, shot_06c, shot_07, shot_08

```powershell
python scripts/studio_helper.py flow-upscale --project t-rex-vs-spinosaurus-swamp-battle --shots shot_01,shot_02,shot_02b,shot_03,shot_04,shot_04b,shot_05,shot_06a,shot_06b,shot_06c,shot_07,shot_08
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | qa_pass | 1 / 2 |  | 1.84–5.59 |
| 2 | shot_02 | beat_01 | qa_pass | 2 / 2 |  | 2.76–6.11 |
| 3 | shot_02b | beat_01 | qa_pass | 1 / 2 |  | 2.43–4.18 |
| 4 | shot_03 | beat_02 | qa_pass | 1 / 2 |  | 1.51–4.46 |
| 5 | shot_04 | beat_02 | qa_pass | 2 / 2 |  | 1.14–3.49 |
| 6 | shot_04b | beat_02 | qa_pass | 1 / 2 |  | 2.51–4.46 |
| 7 | shot_05 | beat_03 | qa_pass | 2 / 2 |  | 3.18–6.13 |
| 8 | shot_06a | beat_03 | qa_pass | 1 / 2 |  | 5.25–8.00 |
| 9 | shot_06b | beat_03 | qa_pass | 2 / 2 |  | 0.00–2.75 |
| 10 | shot_06c | beat_03 | qa_pass | 2 / 2 |  | 4.31–6.16 |
| 11 | shot_07 | beat_04 | qa_pass | 1 / 2 |  | 0.88–4.43 |
| 12 | shot_08 | beat_04 | qa_pass | 2 / 2 |  | 3.42–7.37 |

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

Đủ 55/55 file media trên máy **DESKTOP-HUP72C4**.

## Quyết định & ghi chú bàn giao

- 2026-10-20 21:19 · DESKTOP-HUP72C4 · decision: Người dùng duyệt storyboard (18/18 Keyframes START+END) và đồng ý chi 1.620 credits tạo 9 sub-shot video.

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-21 00:33 | DESKTOP-HUP72C4 | `lint-prompts --strict` | ok |
| 10-21 00:33 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 00:11 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-21 00:10 | DESKTOP-HUP72C4 | `qa-takes-submit ` | ok |
| 10-21 00:09 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-21 00:09 | DESKTOP-HUP72C4 | `qa-takes-submit ` | ok |
| 10-21 00:07 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01 --reviewer agent` | ok |
| 10-21 00:07 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01 --reviewer agent` | ok |
| 10-21 00:06 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01 --reviewer agent` | ok |
| 10-21 00:06 | DESKTOP-HUP72C4 | `qa-takes --shots shot_01 --reviewer agent` | ok |
| 10-21 00:03 | DESKTOP-HUP72C4 | `qa-takes --reviewer agent` | ok |
| 10-20 23:59 | DESKTOP-HUP72C4 | `flow-harvest --kind video --wait` | ok |
| 10-20 23:57 | DESKTOP-HUP72C4 | `flow-generate --kind video --shots shot_04,shot_04b,shot_05,shot_06a,shot_06b,shot_06c,shot_07,shot_08` | ok |
| 10-20 23:54 | DESKTOP-HUP72C4 | `flow-generate --kind video --shots shot_01,shot_02,shot_02b,shot_03` | ok |
| 10-20 23:53 | DESKTOP-HUP72C4 | `storyboard-approve --by user` | ok |
