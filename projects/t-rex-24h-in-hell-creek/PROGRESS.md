# Tiến độ: t-rex-24h-in-hell-creek

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project t-rex-24h-in-hell-creek "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project t-rex-24h-in-hell-creek   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project t-rex-24h-in-hell-creek       # kiểm tra máy + in bước tiếp theo
```

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `t-rex-24h-in-hell-creek` — thư mục `projects/t-rex-24h-in-hell-creek/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/2f69c7dc-37da-443e-bcc6-0bc3de7d3e03
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `Charon`, TTS `gemini-3.8-flash-lite-tts`
- **Cập nhật lần cuối:** 2026-10-20T10:33:37 trên máy **DESKTOP-HUP72C4** (lệnh `note`)
- **Storyboard:** đã sửa sau khi duyệt (cần duyệt lại: 5a57fc0eb89842ec)

## ▶ Bước tiếp theo: 11. Xong — chờ người dùng đăng / yêu cầu mới

Bản cuối: projects\t-rex-24h-in-hell-creek\output\T-Rex_Chapter1_v4.mp4

```powershell
python scripts/studio_helper.py publish-kit --project t-rex-24h-in-hell-creek
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | b01 | qa_pass | 3 / 3 | ✓ | 2.33–5.66 |
| 2 | shot_02 | b01 | qa_pass | 5 / 5 | ✓ | 2.33–5.66 |
| 3 | shot_03 | b02 | qa_pass | 2 / 3 | ✓ | 2.68–5.32 |
| 4 | c1_09 | b02 | qa_pass | 1 / 2 | ✓ | 2.68–5.32 |
| 5 | c1_10 | b02 | qa_pass | 2 / 2 | ✓ | 2.68–5.32 |
| 6 | shot_04 | b03 | qa_pass | 6 / 7 | ✓ | 3.79–7.97 |
| 7 | shot_05 | b03 | qa_pass | 3 / 3 | ✓ | 0.79–4.97 |
| 8 | shot_06 | b04 | qa_pass | 3 / 3 | ✓ | 3.00–5.00 |
| 9 | c1_11 | b04 | qa_pass | 1 / 2 | ✓ | 3.00–5.00 |
| 10 | shot_07 | b05 | qa_pass | 2 / 3 | ✓ | 2.94–5.06 |
| 11 | c1_12 | b05 | qa_pass | 1 / 2 | ✓ | 2.94–5.06 |
| 12 | c1_13 | b05 | qa_pass | 1 / 2 | ✓ | 2.94–5.06 |
| 13 | shot_08 | b06 | qa_pass | 3 / 3 | ✓ | 4.12–6.12 |
| 14 | c1_14 | b06 | qa_pass | 1 / 2 | ✓ | 3.00–5.00 |
| 15 | c1_15 | b06 | qa_pass | 1 / 2 | ✓ | 3.00–5.00 |
| 16 | c1_16 | b07 | qa_pass | 2 / 4 | ✓ | 1.25–6.76 |

## Beat & lời dẫn

- **b01** (hook) 🔊 Before sunrise, the most dangerous animal in Hell Creek opens his eyes.
- **b02** (need) 🔊 He hasn't eaten in four days. Nine tons of hunger, moving almost without a sound.
- **b03** (senses) 🔊 He can smell his prey from miles away. And when he looks, both eyes lock forward, like a hawk's.
- **b04** (target) 🔊 Across the river: breakfast. Unaware.
- **b05** (escalation) 🔊 Patience is his greatest weapon. One wrong step, and the meal is gone.
- **b06** (climax) 🔊 Then, he commits.
- **b07** (cliffhanger) 🔊 But in Hell Creek, the hunter is never the only one watching.

## Đầu ra gần nhất

- `output/T-Rex_Chapter1_v4_9x16.mp4` (2026-10-20 10:11)
- `output/T-Rex_Chapter1_v4.mp4` (2026-10-20 10:10)
- `output/T-Rex_Chapter1_v3_9x16.mp4` (2026-10-20 01:26)
- `output/T-Rex_Chapter1_v3.mp4` (2026-10-20 01:26)
- `output/T-Rex_Chapter1_v2_1080_9x16.mp4` (2026-10-20 00:18)
- `output/T-Rex_Chapter1_v2_1080.mp4` (2026-10-20 00:18)

## Media trên máy này

Đủ 76/76 file media trên máy **DESKTOP-HUP72C4**.

## Quyết định & ghi chú bàn giao

- 2026-10-20 10:33 · DESKTOP-HUP72C4 · decision: Không trả thêm phí: chỉ dùng credit Flow trong gói Ultra + bậc miễn phí Gemini API (cost_policy free_only). Tiêu credit Flow phải báo trước.
- 2026-10-20 10:33 · DESKTOP-HUP72C4 · decision: Lời dẫn tiếng Anh, giọng Charon; giữ đúng model TTS ghi ở manifest.voiceover_model cho cả phim (đổi model = giọng khác).
- 2026-10-20 10:33 · DESKTOP-HUP72C4 · decision: Chương 1 v4 hoàn tất: 16 shot 1080p, nhạc score tự tổng hợp, LUT documentary, thumbnail tiếng Anh, publish.md. Chờ người dùng đăng.
- 2026-10-20 10:33 · DESKTOP-HUP72C4 · issue: c1_16: thử 'chỉ đôi mắt, đứng yên' (take 3–4) thất bại, giữ take 2 (2 con T-Rex). Storyboard phải duyệt lại trước lần tạo video sau.
- 2026-10-20 10:33 · DESKTOP-HUP72C4 · todo: Tiếp theo: viết kịch bản Chương 2 (0 credit) → storyboard → người dùng duyệt; hoặc 4.1 video 9:16 gốc (tốn credit, hỏi trước).

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 10:33 | DESKTOP-HUP72C4 | `note ` | ok |
| 10-20 10:33 | DESKTOP-HUP72C4 | `note ` | ok |
| 10-20 10:33 | DESKTOP-HUP72C4 | `note ` | ok |
| 10-20 10:33 | DESKTOP-HUP72C4 | `note ` | ok |
| 10-20 10:33 | DESKTOP-HUP72C4 | `note ` | ok |
