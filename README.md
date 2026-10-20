# AI Video Studio — Sản xuất video AI chuyên nghiệp (Google AI Ultra)

Biến VS Code / Antigravity thành một studio sản xuất video AI: **Gemini** (nghiên cứu, kịch bản, QA thị giác, lời dẫn TTS) + **Nano Banana** (ảnh tham chiếu, frame khởi đầu) + **Veo 3.1** (clip video), điều phối bởi Agent và bộ công cụ `scripts/studio_helper.py`.

## Cài đặt

```powershell
pip install -r requirements.txt
# Tùy chọn — bật QA thị giác & TTS lời dẫn qua Gemini API:
$env:GEMINI_API_KEY = "..."
```
Cấu hình máy, model, đơn giá credit, ngân sách: [studio_config.json](studio_config.json).

## Cấu trúc

- [GEMINI.md](GEMINI.md) — quy tắc điều phối cho Agent (luôn bật).
- [.agents/skills/ai-video-studio/SKILL.md](.agents/skills/ai-video-studio/SKILL.md) — runbook sản xuất từng bước.
- [references/prompt_templates.md](.agents/skills/ai-video-studio/references/prompt_templates.md) — công thức prompt.
- [references/universal_director_engine.md](.agents/skills/ai-video-studio/references/universal_director_engine.md) — tư duy đạo diễn.
- [scripts/studio/](scripts/studio/) — mã nguồn công cụ (`cli`, `prompts`, `qa`, `audio`, `timeline`, `render`...).
- `projects/<slug>/` — manifest, tài nguyên, take, QA, bản dựng của từng dự án.
- [tests/](tests/) — `python -m pytest tests`.

## Lệnh chính

| Giai đoạn | Lệnh |
|---|---|
| Lập kế hoạch | `plan`, `init` |
| Tiền kỳ | `forge-assets`, `audit-assets` |
| Prompt | `build-prompts`, `lint-prompts` |
| Tạo & lưu take | `register-clip`, `select-take`, `download-batch`, `extract-frame` |
| QA | `qa`, `qa-vision`, `approve`, `status` |
| Hậu kỳ | `voiceover`, `timeline`, `assemble` |
| Dự án cũ | `migrate` |

## Cách dùng (gửi vào khung chat)

**Chỉ có chủ đề:**
> *"Chủ đề: [..]. Thời lượng: [..]. Ngôn ngữ: [..]. Nền tảng: [YouTube 16:9 / TikTok 9:16]. Hãy nghiên cứu và đề xuất concept."*

**Có sẵn câu chuyện:**
> *"Đây là câu chuyện của tôi: [..]. Chuyển thể thành video [phong cách], [thời lượng], lời [ngôn ngữ], phát hành trên [nền tảng]."*

## Làm việc trên nhiều máy

Windows ↔ Ubuntu, media qua rclone + Google Drive: [docs/SYNC_SETUP.md](docs/SYNC_SETUP.md). Đầu phiên: `git pull` → `python scripts/studio_helper.py resume`.
