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
- **Flow:** https://flow.google.com/project/6924a83e-c093-44ee-8229-c27facfb7721
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `-`
- **Cập nhật lần cuối:** 2026-10-21T11:20:04 trên máy **DESKTOP-HUP72C4** (lệnh `build-prompts`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 7. Upscale 1080p

Còn 720p: shot_01, shot_02, shot_03, shot_04, shot_05, shot_06, shot_07, shot_08, shot_09, shot_10

```powershell
python scripts/studio_helper.py flow-upscale --project clash-of-titans-rex-vs-vasto-part-1 --shots shot_01,shot_02,shot_03,shot_04,shot_05,shot_06,shot_07,shot_08,shot_09,shot_10
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | qa_pass | 1 / 2 |  | 0.35–5.00 |
| 2 | shot_02 | beat_01 | qa_pass | 2 / 2 |  | 0.35–5.00 |
| 3 | shot_03 | beat_01 | qa_pass | 1 / 2 |  | 2.88–7.53 |
| 4 | shot_04 | beat_02 | qa_pass | 1 / 2 |  | 0.35–5.00 |
| 5 | shot_05 | beat_02 | qa_pass | 1 / 2 |  | 0.35–5.00 |
| 6 | shot_06 | beat_03 | qa_pass | 1 / 2 |  | 0.35–5.00 |
| 7 | shot_07 | beat_03 | qa_pass | 1 / 2 |  | 0.76–5.41 |
| 8 | shot_08 | beat_03 | qa_pass | 2 / 2 |  | 1.84–6.49 |
| 9 | shot_09 | beat_04 | qa_pass | 2 / 2 |  | 0.35–5.00 |
| 10 | shot_10 | beat_04 | qa_pass | 2 / 2 |  | 2.39–7.04 |

## Beat & lời dẫn

- **beat_01** (hook) — 
- **beat_02** (escalation) — 
- **beat_03** (climax) — 
- **beat_04** (cliffhanger) — 

## Đầu ra gần nhất

- `output/final_video_9x16.mp4` (2026-10-21 11:14)
- `output/final_video.mp4` (2026-10-21 11:12)

## Media trên máy này

Đủ 38/38 file media trên máy **DESKTOP-HUP72C4**.

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-21 11:20 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 11:14 | DESKTOP-HUP72C4 | `assemble --format both` | ok |
| 10-21 11:11 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-21 11:10 | DESKTOP-HUP72C4 | `qa-takes-submit --reviewer agent` | ok |
| 10-21 11:09 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-21 11:09 | DESKTOP-HUP72C4 | `qa-takes-submit --reviewer agent` | ok |
| 10-21 11:08 | DESKTOP-HUP72C4 | `lint-prompts ` | ok |
| 10-21 11:08 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-21 11:08 | DESKTOP-HUP72C4 | `auto-select ` | ok |
| 10-21 11:08 | DESKTOP-HUP72C4 | `qa-takes-submit --reviewer agent` | ok |
| 10-21 09:56 | DESKTOP-HUP72C4 | `lint-prompts --strict` | ok |
| 10-21 09:56 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
