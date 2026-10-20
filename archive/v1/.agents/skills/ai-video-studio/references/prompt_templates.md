# Bộ Meta-Prompt Động Đa Chiều (Universal Dynamic Meta-Prompts — Gemini Ultra + Nano Banana + Veo 3.1)

Tài liệu này định nghĩa bộ Meta-Prompt **Không Fix Cứng (Zero-Hardcode)**. Khi User đưa **BẤT KỲ chủ đề, lĩnh vực hay câu chuyện nào**, hệ thống tự động yêu cầu Gemini Ultra giải phẫu chủ đề đó theo **6 Trục Điện Ảnh Động** ([universal_director_engine.md](./universal_director_engine.md)) để sinh ra kịch bản và bộ Prompt tối ưu nhất.

---

## 1. Prompt Khảo Sát Xu Hướng & Giải Phẫu Chủ Đề Động (Dán vào `gemini.google.com` khi User đưa Chủ đề)

```text
Đóng vai Giám đốc Sáng tạo Nội dung Viral kiêm Đạo diễn Điện ảnh & Hoạt hình AI cấp Senior.

Tôi muốn sản xuất một video với đầu vào:
- Chủ đề / Ý tưởng / Lĩnh vực: "{TOPIC}"
- Thời lượng mục tiêu: {DURATION_SECONDS} giây ({NUM_SHOTS} cảnh x 8 giây)
- Ngôn ngữ: {LANGUAGE}
- Yêu cầu phong cách (nếu có): {STYLE_OR_AUTO}

Hãy thực hiện khảo sát xu hướng triệu view hiện tại trên YouTube / TikTok về chủ đề này và phân tích tự động theo 6 Trục Điện Ảnh Động:

1. GIẢI PHẪU CHỦ ĐỀ & XU HƯỚNG VIRAL (DYNAMIC DECONSTRUCTION):
   - Góc tiếp cận (Angle), công thức Tiêu đề và Hook 3 giây đầu nào đang thu hút người xem nhất cho chủ đề "{TOPIC}"?
   - **Chất liệu thị giác (Visual Medium)**: Chủ đề này lên hình đẹp và cuốn hút nhất ở định dạng nào (2D, 3D CGI, Live-Action điện ảnh, Tư liệu lịch sử tái hiện, Mô phỏng khoa học/vũ trụ/vi mô, hay kết hợp)?
   - **Cấu trúc Thực thể & Bố cục Khung hình (Entity & Staging Topology)**: Các cảnh trong chủ đề này cần những thực thể nào (Nhân vật chính, nhân vật phụ, đám đông quần chúng, hệ sinh thái, hay hiện tượng tự nhiên/vật lý)? Khi nào cần cảnh đơn, cảnh đôi tương tác trực tiếp, hay đại cảnh có quần chúng?
   - **Cơ chế Âm thanh (Audio Modality)**: Nên dùng nhân vật nói trực tiếp trên hình (On-Screen Lip-Sync), giọng thuyết minh dẫn chuyện (Off-Screen Narrator Voiceover), hay kết hợp cả hai theo từng phân đoạn?

2. ĐỀ XUẤT 4 PHƯƠNG ÁN (CONCEPTS) ĐỂ LỰA CHỌN:
   Với mỗi phương án (Option 1 -> Option 4), trình bày rõ:
   - Tên Concept & Tiêu đề Viral đề xuất
   - Chất liệu Hình ảnh (Visual Direction) & Cơ chế Âm thanh (Lip-Sync / Voiceover / Hybrid)
   - Cấu trúc Thực thể / Nhân vật xuất hiện (Chính - Phụ - Quần chúng & Tương tác vật lý môi trường)
   - Hook 3 giây đầu + Tóm tắt mạch triển khai qua {NUM_SHOTS} cảnh với sự biến thiên góc máy điện ảnh.
```

---

## 2A. Universal Meta-Prompt Generator (Bước 1: Nhờ Gemini Ultra thiết kế Master Prompt Chuyên Biệt Cho Chủ Đề Đã Chọn)

Khi đã có phương án được chọn hoặc câu chuyện có sẵn của User, gửi prompt này vào `https://gemini.google.com/` để Gemini Ultra tự động đóng gói một **MASTER PROMPT** chuyên biệt cho đúng lĩnh vực và phong cách đó:

```text
Bạn là Principal AI Film Director & Senior Prompt Engineer làm việc trên hệ sinh thái Google AI Ultra (Nano Banana 2.1/Pro và Veo 3.1 trên Google Flow).

Tôi cần sản xuất tác phẩm video sau:
- Chủ đề / Câu chuyện: "{STORY_OR_CHOSEN_CONCEPT}"
- Thời lượng: {DURATION_SECONDS} giây (chia thành chính xác {NUM_SHOTS} shots, mỗi shot 8 giây trên Veo 3.1).
- Ngôn ngữ: {LANGUAGE}
- Định hướng Hình ảnh & Thể loại: {VISUAL_STYLE}
- Tỷ lệ khung hình: {ASPECT_RATIO}

NHIỆM VỤ BƯỚC 1:
Chưa viết kịch bản chi tiết vội. Hãy phân tích sâu đặc thù của chủ đề "{STORY_OR_CHOSEN_CONCEPT}" và viết cho tôi một **MASTER PROMPT CHUYÊN NGHIỆP NHẤT** (đặt trong 1 code block duy nhất) để ở bước tiếp theo tôi copy dán lại cho chính bạn.

Master Prompt của bạn phải tự động thiết kế bộ quy tắc riêng phù hợp nhất với chủ đề này, đồng thời bắt buộc tích hợp 5 NGUYÊN TẮC KỸ THUẬT CẤP SENIOR AI ENGINEER sau đây để sản phẩm đầu ra sạch 100% không có "sạn" AI:

1. TÁCH BẠCH THỰC THỂ GỐC VÀ ĐẠO CỤ RỜI (ZERO-PROP CLEAN BASE INGREDIENTS):
   - Khi tạo Prompt cho các thực thể/nhân vật cố định (`Base Ingredients` trên Nano Banana 2.1/Pro): Tuyệt đối không gắn sẵn các đạo cụ rời sẽ bị buông/ném/thay đổi trạng thái vào tay nhân vật trong ảnh tham chiếu gốc (`clean anatomy, natural neutral posture, empty hands, no detached held objects`).
   - Điều này ngăn chặn triệt để lỗi Veo 3.1 vẽ mọc thêm tay thứ 3, thứ 4 hoặc vẽ nhân đôi đồ vật khi nhân vật cử động hay làm rơi đồ vật.

2. BỐ CỤC ĐA THỰC THỂ & PHÂN TẦNG KHÔNG GIAN ĐỘNG (DYNAMIC MULTI-ENTITY & CROWD STAGING):
   - Tùy theo diễn biến nội dung của từng cảnh (Shot), tự động dàn dựng số lượng thực thể tự nhiên nhất:
     * Cảnh 1 chủ thể (`Solo Focus`)
     * Cảnh 2–N chủ thể tương tác trực tiếp với nhau trong cùng khung hình (`Two-Shot / Group Interaction`)
     * Cảnh có phân tầng Tiền cảnh (Chính) - Trung cảnh (Phụ) - Hậu cảnh (Quần chúng / Đám đông / Hệ sinh thái / Bối cảnh động)
     * Cảnh thuần hiện tượng vật lý / môi trường vĩ mô hoặc vi mô (`Pure Phenomenon / Environment`).

3. NGỮ PHÁP DỰNG PHIM PHÂN CẤP: NỐI MƯỢT TRONG CÙNG CẢNH DÀI (`INTRA_SCENE_CONTINUE`) VS. CHUYỂN CẢNH BÌNH THƯỜNG (`INTER_SCENE_CUT`):
   - **CẤM nối liền vô tội vạ toàn bộ các shot trong video!** Hãy chia kịch bản thành các **Cảnh (`scene_id`)**:
     * **Trường hợp 1 — Cảnh dài 16s–24s cần 2–3 đoạn 8s ở CÙNG góc máy / CÙNG mạch hành động (`transition_to_next = "INTRA_SCENE_CONTINUE"`)**: Ví dụ nhân vật đọc bản tin 16s ở cùng một góc máy, hoặc chạy từ đầu sân đến cuối sân mất 16s (`Shot A [0–8s]` chạy từ đầu sân đến giữa sân `K_mid`, `Shot B [8–16s]` chạy từ giữa sân `K_mid` đến cuối sân `K_end`). Khi đó bắt buộc khóa `end_keyframe_id` của `Shot A` trùng với `start_keyframe_id` của `Shot B` (hoặc dùng `Last-Frame / Extend` từ `Shot A`).
     * **Trường hợp 2 — Hết cảnh đó và chuyển sang Cảnh khác / Góc máy khác (`transition_to_next = "INTER_SCENE_CUT"`)**: Cắt chuyển cảnh điện ảnh bình thường (`Hard Cut`). Cảnh mới bắt đầu bằng `start_keyframe_id` độc lập của góc máy mới, tuyệt đối không lấy frame cuối của cảnh cũ ép nối sang!
   - Với mỗi Shot, xuất rõ: `scene_id`, `sub_shot_index`, `sub_shot_total`, `transition_to_next` (`INTRA_SCENE_CONTINUE` hoặc `INTER_SCENE_CUT`), `first_frame_prompt`, `last_frame_prompt` (nếu có), và `veo_prompt`.

4. TƯƠNG TÁC VẬT LÝ NHÂN QUẢ & ĐA DẠNG GÓC MÁY ĐIỆN ẢNH (`CAUSAL PHYSICS & CINEMATOGRAPHY`):
   - Mọi hành động đều phải mô tả rõ phản ứng vật lý hai chiều với môi trường (ánh sáng, trọng lực, khói bụi, chất lỏng, rung chấn, biến dạng vật liệu...).
   - Thiết kế chuỗi góc máy (`Camera Progression`) biến thiên giàu tính điện ảnh xuyên suốt {NUM_SHOTS} cảnh (luân phiên hợp lý giữa `Wide / Aerial`, `Two-Shot`, `Over-the-Shoulder`, `Close-Up / Macro`, `Dynamic Tracking / Orbit`), tuyệt đối không lặp lại góc máy tĩnh đơn điệu.

5. KIỂM SOÁT ÂM THANH, KHẨU HÌNH & THỜI LƯỢNG (`AUDIO MODALITY & EXACT PACING`):
   - Mỗi cảnh 8 giây có lượng lời thoại hoặc thuyết minh bằng {LANGUAGE} tối đa {MAX_WORDS_PER_SHOT} chữ/từ (kéo dài từ 0.5s đến 7.0s, có nhịp nghỉ 7.0s–8.0s để chuyển cảnh mượt).
   - Tự động phân định rõ từng cảnh dùng `On-Screen Lip-Sync` (chỉ định chính xác vị trí nhân vật nào đang mở miệng nói, các nhân vật khác trong khung hình giữ miệng khép và phản ứng tự nhiên) hay dùng `Off-Screen Voiceover / Narrator` (giọng thuyết minh ngoài khung hình, nhân vật trên hình không mấp máy miệng), kèm âm thanh hiện trường (`SFX`) và cấm chèn chữ/subtitles rác lên hình (`no subtitles, no on-screen text`).

Hãy xuất ra **MASTER PROMPT** hoàn chỉnh này trong 1 khung code block duy nhất.
```

---

## 3. Công Thức Tạo "Bản Thiết Kế Model Nhân Vật Đa Góc Độ" (AAA Character Model Sheets cho Nano Banana 2.1/Pro)

Thay vì chỉ tạo 1 tấm ảnh chụp nhân vật từ 1 góc đơn lẻ, mỗi Nhân vật / Thực thể chính phải được tạo **Bộ Bản Thiết Kế Model (Character Model Blueprint Pack)** gồm:

### 3A. Bản Thiết Kế 1 — `Orthographic Multi-Angle Turnaround Sheet` (Trước – Sau – Trái – Phải – Trên Xuống)
* **Dùng cho Nhân vật Người / Hoạt hình 2D / 3D / Game**:
  ```text
  Professional AAA game & animation studio character model turnaround sheet of [Character Name & Detailed Visual Description], in [Visual Style]. Multi-angle orthographic reference layout on a single 16:9 sheet showing 5 consistent views of the exact same character: (1) Full-body Front View, (2) Full-body Back View, (3) Left Side Profile View, (4) Right 3/4 View, and (5) High-Angle Top-Down Perspective. Neutral A-pose with empty hands, 100% identical proportions, colors, and outfit across all angles, clean neutral studio grid background, no text labels, 16:9.
  ```
* **Dùng cho Sinh vật / Động vật / Khủng long 3D Đời thực**:
  ```text
  Professional VFX creature model turnaround sheet of [Creature Name & Detailed Anatomical Description], photorealistic 3D CGI in BBC Prehistoric Planet / ILM style. Multi-angle orthographic reference layout on a single 16:9 sheet showing 5 consistent views of the exact same creature: (1) Full-body Left Side Profile, (2) Full-body Right Side Profile, (3) Direct Front View, (4) Direct Rear/Back View, and (5) Top-Down Dorsal View showing head-to-tail proportions. 100% consistent scale pattern, battle scars, coloration, and muscle anatomy across all views, neutral studio lighting, no text, 16:9.
  ```

### 3B. Bản Thiết Kế 2 — `Articulation, Expression & Hand/Limb State Sheet` (Chi Tiết Bộ Phận & Khi Cầm Đồ vs. Không Cầm Đồ)
* **Dùng cho Nhân vật có Bàn tay Linh hoạt (Con người / Hoạt hình 2D/3D)**:
  ```text
  Professional character articulation and hand-state model sheet of [Character Name], in [Visual Style], 16:9 layout. Left half shows 3 facial expression & mouth states: (1) Neutral closed mouth, (2) Open speaking mouth (lip-sync ready), (3) Expressive reaction face. Right half shows 3 detailed anatomical hand & arm states of the character: (1) Relaxed open empty hands (front and back of palm, strictly 5 fingers), (2) Natural gripping/holding hand posture wrapped around [Prop/Object], and (3) Expressive pointing/gesturing hand posture. Clean studio reference sheet, consistent colors and anatomy, no text.
  ```
* **Dùng cho Sinh vật / Khủng long 3D Đời thực (Chi tiết Hộp sọ, Hàm Khép/Mở, Chi trước & Bàn chân)**:
  ```text
  Professional VFX creature anatomical articulation callout sheet of [Creature Name], photorealistic 3D CGI, 16:9 layout. Detailed close-up reference views of the exact same creature's body parts: (1) Head with jaws closed naturally showing lip scales and forward-facing eyes, (2) Head with jaws open 45 degrees showing realistic inner jaw muscles and teeth proportions, (3) Detailed close-up of the small two-fingered forelimbs in resting and gripping positions, and (4) Heavy three-toed hind foot anatomy pressing into the ground. Ultra-realistic skin texture and biomechanics, no text.
  ```

### 3C. Bản Thiết Kế 3 — `Scale & Anatomy Reference Sheet` (Khóa Tỷ Lệ Thực 1:1)
* **Dùng cho Nhân vật Người / Anime / 3D**:
  ```text
  Professional Character Scale Reference Sheet in [Visual Style]. Full side-by-side comparison on a flat neutral ground plane showing [Character Name & Description] standing naturally next to a standard 1.8-meter height marker, doorframe, or co-star at strict 1:1 human scale, realistic ground contact shadows, neutral daylight studio lighting, 8k, 16:9, no text.
  ```
* **Dùng cho Sinh vật / Khủng long / Động vật 3D**:
  ```text
  AAA Studio Biomechanical Scale & Interaction Reference Sheet in [Visual Style]. Full side-profile comparison on a unified Late Cretaceous ground plane locking exact real-world anatomical proportions between [Main Creature] and a standard metric reference / secondary entity [Prey / Co-star] at strict 1:1 paleontological scale, natural daylight lighting, realistic ground contact shadows, zero exaggerated props, 8k, 16:9, no text.
  ```
* **Dùng cho Robot / Cơ khí / Phương tiện (Mech / Hard-Surface)**:
  ```text
  AAA Hard-Surface Scale Reference Sheet in [Visual Style]. Full side-profile comparison on a clean hangar ground plane locking exact metric height of [Mech Name] against a 1.8-meter human operator and support vehicle at strict 1:1 scale, realistic contact shadows, 8k, 16:9, no text.
  ```

---

## 4. Công Thức Tạo Bối Cảnh Sạch Không Người (`Environment Clean Plates` — Nano Banana 2.1)

Mọi cảnh quay trong cùng phân đoạn bắt buộc phải dùng chung một **Bối cảnh Sạch (Clean Plate)** làm tọa độ không gian và ánh sáng gốc:

```text
Pristine environment plate in [Visual Style], [Environment Name]: [Detailed Terrain, Architecture, Lighting & Atmospheric Conditions]. Master wide cinematic establishing plate, volumetric lighting and atmospheric perspective. Strict Clean Plate Rule: completely empty environment, no people, no characters, no creatures, no flying creatures, no vehicles, clear natural canopy and pristine ground plane ready for composite staging, 8k, 16:9, no text.
```

---

## 5. Công Thức Tạo Thư Viện Đạo Cụ Tách Rời (`Isolated Props Library` — Nano Banana Pro)

Bất kỳ đồ vật nào nhân vật sẽ cầm, ném, nhặt hoặc cắn xé phải được thiết kế độc lập trước:

```text
Professional AAA prop design and 3-angle turnaround sheet of [Prop Name & Detailed Visual Materials], in [Visual Style]. Multi-angle isolated orthographic layout on neutral studio grey background: (1) Front View, (2) Side Profile View, and (3) Perspective 3/4 View showing materials, wear, reflections, and mechanical seams. Strict isolated studio asset: completely detached from any character, no hands holding it, natural contact shadow on ground, scaled accurately to standard physical dimensions ([Length cm x Width cm]), 8k, 16:9, no text.
```

---

## 6. Công Thức Tạo Khung Hình Tiếp Xúc & Va Chạm (`Contact & Interaction Pair Sheet` — Nano Banana Pro)

Dùng khi có 2 nhân vật tương tác trực tiếp (đánh nhau, ôm, cắn xé, rượt đuổi) để khóa tư thế tiếp xúc trước khi render video:

```text
Photorealistic cinematic contact keyframe in [Environment Name], [Visual Style]. Exact real-world anatomical scale comparison and natural biomechanical interaction: [Character A] and [Character B / Prop] locked in direct physical contact at t=0.0s: [Describe exact physical contact point, hand grip position or closed-jaw occluded clamp, muscle tension, ground weight displacement, contact shadows]. Strict BBC Occluded-Contact Physics: zero floating props in mid-air, zero detached loose objects, authentic physical contact and weight balance, 8k, 16:9, no text.
```

---

## 7. Công Thức Dàn Dựng Khung Hình Ghép Tiền Trạm (`Composite Start Keyframe Bridging`)

Ghép **[Char Rig] + [Clean Plate] + [Prop Sheet]** thành Start Frame tại `t = 0.0s` cho Veo 3.1:

```text
Photorealistic master keyframe in [Visual Style]. In the pristine setting of [Environment Name from Clean Plate], [Character Name from Rig Pack] is positioned in [Foreground / Midground] at t=0.0s: [Describe exact initial pose, posture, and gaze]. [Character Name] interacts naturally with [Prop Name from Props Library / Secondary Entity], maintaining 100% anatomical consistency with the approved character model turnaround sheet. Natural atmospheric lighting matching the environment plate, realistic ground contact shadows, 8k, 16:9, no text.
```

