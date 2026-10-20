# AI Video Studio — Hệ Thống Sản Xuất Phim & Hoạt Hình AI Tự Động (Google AI Ultra)

Dự án này biến VS Code / Antigravity thành một **Hãng Phim & Studio Hoạt Hình AI Tự Động (Autonomous AI Video Studio)** sử dụng sức mạnh của gói **Google AI Ultra**:
- **Gemini Argon 4 / Pro** (`https://gemini.google.com/`): Khảo sát xu hướng YouTube/TikTok, tự động viết **Meta-Prompt**, lên kịch bản phân cảnh (Storyboard) và viết Prompt chuyên sâu.
- **Nano Banana 2.1 & Nano Banana Pro** (`https://flow.google.com/`): Tạo hình nhân vật (Character Sheets / Ingredients) và bối cảnh chuẩn xác, khóa ngoại hình 100% xuyên suốt video.
- **Veo 3.1** (`https://flow.google.com/`): Tạo video 2D/3D Animation, Pixar-style, Anime hoặc Điện ảnh có tiếng động, lời thoại và **khớp khẩu hình miệng (Lip-Sync)**.

---

## Cấu Trúc Dự Án

- [GEMINI.md](file:///d:/myProject/AI-video/GEMINI.md): Quy tắc điều phối tự động (Always-on Rule) giúp AI trong khung chat tự động hiểu vai trò Đạo diễn / Kỹ sư AI Video ngay khi bạn gửi yêu cầu.
- [.agents/skills/ai-video-studio/SKILL.md](file:///d:/myProject/AI-video/.agents/skills/ai-video-studio/SKILL.md): Bộ quy trình 5 giai đoạn (5-Stage Runbook) điều khiển trình duyệt `@/browser` trên Gemini và Google Flow.
- [.agents/skills/ai-video-studio/references/prompt_templates.md](file:///d:/myProject/AI-video/.agents/skills/ai-video-studio/references/prompt_templates.md): Bộ công thức Meta-Prompt, Character Ingredient Prompt và Veo 3.1 Lip-Sync Prompt.
- [scripts/studio_helper.py](file:///d:/myProject/AI-video/scripts/studio_helper.py): Công cụ Python xử lý tính toán thời lượng, kiểm tra giới hạn từ Lip-Sync, trích xuất Frame cuối (`extract-last-frame`) để nối cảnh mượt mà và ghép video thành phẩm (`assemble`).
- `projects/`: Thư mục chứa toàn bộ kịch bản, hình ảnh nhân vật, các cảnh quay 8s và video hoàn chỉnh của từng dự án.

---

## Cách Sử Dụng (Chỉ Cần Gửi Vào Khung Chat)

Bạn chỉ cần nhắn trực tiếp vào khung chat theo 1 trong 2 cách sau:

### Cách 1: Chỉ đưa Chủ đề (Để AI tự khảo sát Trend & Đề xuất lựa chọn)
> *"Chủ đề: [Tên chủ đề]. Thời lượng: [X giây/phút]. Ngôn ngữ: [Tiếng Việt / Tiếng Anh]. Phong cách: [Hoạt hình 2D kiểu Vui Vẻ / 3D Pixar / Chuyển thể phim...]. Hãy khảo sát trend và đề xuất cho tôi chọn."*

### Cách 2: Đưa sẵn Câu chuyện / Tác phẩm (Để AI chuyển thể thẳng thành Phim/Video)
> *"Đây là câu chuyện của tôi: [Nội dung truyện]. Hãy chuyển thể thành video hoạt hình [Phong cách], thời lượng [X giây/phút], ngôn ngữ nói [Tiếng Việt]."*

