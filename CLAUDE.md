# Hướng dẫn cho Claude Code

Dự án dùng chung quy tắc điều phối với Gemini/Antigravity:

@GEMINI.md

Runbook chi tiết: @.agents/skills/ai-video-studio/SKILL.md

## Riêng cho Claude

- **Đầu mỗi phiên chat:** `git pull` rồi `python scripts/studio_helper.py resume` và đọc `projects/<slug>/PROGRESS.md` trước khi làm gì khác (quy tắc 10). Máy mới / thiếu media → [docs/SYNC_SETUP.md](docs/SYNC_SETUP.md).

- Bạn là agent đang chat → tự làm QA thị giác (`qa-vision` tự nhận chế độ `agent` nhờ biến `CLAUDECODE`). Xem ảnh bằng công cụ Read, chấm khắt khe, ghi JSON, rồi `qa-vision-submit`.
- Không gọi Gemini API cho việc bạn tự làm được. Chỉ TTS lời dẫn cần API/công cụ ngoài — hỏi người dùng trước khi dùng dịch vụ tốn phí.
- Chạy lệnh Python với `PYTHONIOENCODING=utf-8` trên Windows để in tiếng Việt. Ubuntu: `source .venv/bin/activate` trước.
- Test: `python -m pytest tests -q`.
