# Universal Generative Director Engine — Kiến Trúc Đạo Diễn Động Đa Chiều (Zero-Hardcode Architecture)

Tài liệu này định nghĩa kiến trúc **Không Fix Cứng (Zero-Hardcode)** cấp Senior AI Engineer. Hệ thống **KHÔNG** giới hạn vào bất kỳ danh sách thể loại cố định nào, mà tự động giải phẫu **BẤT KỲ chủ đề, lĩnh vực hay câu chuyện nào** (Lịch sử, Vũ trụ, Khoa học, Sinh học, Tâm lý, Kinh tế, Truyện hư cấu, Đời sống, Hài hước, Điện ảnh, Hoạt hình, Tài liệu...) theo **6 Trục Điện Ảnh Động (6 Universal Filmmaking Dimensions)**.

---

## PHẦN 1: 6 TRỤC GIẢI PHẪU ĐỘNG CHO MỌI CHỦ ĐỀ (6 UNIVERSAL DIMENSIONS)

Khi User đưa bất kỳ **Chủ đề (Topic)** hoặc **Câu chuyện (Story)** nào, Agent và Gemini Ultra sẽ tự động phân tích và tổng hợp bộ Prompt dựa trên 6 trục động sau:

### Trục 1: Chất Liệu Thị Giác & Mỹ Thuật (`Visual Medium & Art Direction`)
* Tự động suy luận từ yêu cầu của User hoặc đề xuất phong cách tối ưu nhất cho chủ đề:
  - *Bất kỳ phong cách 2D nào*: Hand-drawn, flat vector, motion graphics, infographic, manga/anime, comic, tranh thủy mặc, doodle...
  - *Bất kỳ phong cách 3D / CGI nào*: Stylized 3D, photorealistic CGI, stop-motion, claymation, low-poly, voxel...
  - *Bất kỳ phong cách Quay Thực / Khoa Học nào*: Live-action 35mm/IMAX, phim tài liệu lịch sử/tự nhiên, hiển vi sinh học (microscopic/cellular), thiên văn vũ trụ (astrophotography/cosmic scale), góc nhìn thứ nhất (POV/vlog/studio)...
* **Quy tắc**: Mọi thông số về ánh sáng, ống kính, bảng màu, chất liệu bề mặt đều được sinh động (dynamically synthesized) theo đúng bản chất của chủ đề đó.

### Trục 2: Cấu Trúc Thực Thể & Phân Tầng Xuất Hiện (`Entity & Cast Topology`)
* Khái niệm **"Thực thể" (Entity)** bao gồm bất cứ thứ gì xuất hiện trên khung hình: *Con người, sinh vật, đám đông lịch sử, tế bào/phân tử, hành tinh/ngôi sao, máy móc, hoặc nhân vật hư cấu*.
* Số lượng và vai trò thực thể trong **từng cảnh (Shot-level Staging)** hoàn toàn biến thiên tự nhiên theo kịch bản:
  - **Không có nhân vật (`Pure Phenomenon / Environment`)**: Cảnh vũ trụ giãn nở, núi lửa phun trào, thành phố cổ đại nhìn từ trên cao, dòng máu chảy trong tĩnh mạch...
  - **Đơn chủ thể (`Solo Focus`)**: 1 thực thể/nhân vật chính thực hiện hành động hoặc độc thoại.
  - **Đa chủ thể tương tác trực tiếp (`Multi-Entity Interaction`)**: 2, 3 hoặc nhóm nhân vật cùng xuất hiện trong một khung hình, đối thoại, tranh luận, chiến đấu hoặc phối hợp hành động.
  - **Phân tầng Chính – Phụ – Quần chúng (`Lead + Supporting + Crowd/Ecosystem`)**: Chủ thể chính ở tiền cảnh/trung cảnh, chủ thể phụ tương tác bên cạnh, và hàng chục/hàng trăm thực thể quần chúng (đội quân, người đi đường, bầy đàn, hệ sinh thái) hoạt động sống động ở hậu cảnh.

### Trục 3: Cơ Chế Âm Thanh & Giọng Nói (`Audio & Vocal Modality`)
* Tự động quyết định cơ chế âm thanh cho **từng cảnh riêng biệt** (có thể kết hợp linh hoạt ngay trong cùng 1 video):
  1. **`On-Screen Lip-Sync` (Nhân vật trên hình trực tiếp nói)**:
     - Dùng khi nhân vật đang phát biểu trực diện.
     - Nếu trong khung hình có nhiều nhân vật cùng xuất hiện, bắt buộc **Khóa Vị Trí Người Nói (Spatial Speaker Lock)**: chỉ định rõ nhân vật nào đang mở miệng nói câu thoại, còn các nhân vật khác trong khung hình giữ miệng khép và biểu cảm lắng nghe/phản ứng.
  2. **`Off-Screen Voiceover / Narrator` (Giọng thuyết minh ngoài khung hình)**:
     - Dùng cho các cảnh giải thích khoa học, lịch sử, vũ trụ, thiên nhiên, hoặc cảnh hành động đại cảnh.
     - Các thực thể trên hình thực hiện hành động vật lý tự nhiên, không mấp máy miệng theo lời thuyết minh.
  3. **`Diegetic Environmental SFX` (Âm thanh vật lý hiện trường)**:
     - Tiếng va chạm, tiếng bước chân, tiếng gió/nước, tiếng nổ, tiếng đám đông, âm thanh phòng thí nghiệm... khớp chính xác với chuyển động trên màn hình.

### Trục 4: Quy Luật Vật Lý Nhân Quả & Bảo Toàn Trạng Thái (`Causal Physics & State Continuity`)
* Mọi chuyển động trong cảnh phải có **tác động vật lý hai chiều với môi trường**:
  - Khi thực thể di chuyển hoặc tác động lực $\rightarrow$ môi trường xung quanh phải phản ứng hợp lý (mặt đất/bàn rung chuyển, bụi/nước/mảnh vỡ văng ra, cây cối/đồ vật dịch chuyển, ánh sáng/bóng đổ thay đổi theo nguồn sáng).
* **Bảo toàn giải phẫu & Trạng thái đạo cụ (Anti-Artifact Physics)**:
  - Tuyệt đối không để xảy ra hiện tượng nhân vật mọc thừa tay/chân khi cử động mạnh, hoặc đồ vật đã rơi/ném đi nhưng trên tay vẫn còn dính lại đồ vật đó.

### Trục 5: Ngôn Ngữ Máy Quay & Nhịp Dựng Phim (`Dynamic Cinematography & Editing Flow`)
* Tự động thiết kế chuỗi góc máy (`Camera Progression`) đa dạng, không lặp lại góc máy tĩnh đơn điệu:
  - Luân phiên mượt mà giữa các cỡ cảnh và chuyển động máy: `Establishing Wide / Aerial` $\leftrightarrow$ `Two-Shot / Group Interaction` $\leftrightarrow$ `Over-the-Shoulder (OTS)` $\leftrightarrow$ `Close-Up / Macro Detail` $\leftrightarrow$ `Dynamic Tracking / Pan / Orbit`.

### Trục 6: Kiểm Soát Thời Lượng & Nhịp Độ Ngôn Ngữ (`Temporal & Linguistic Pacing`)
* Mỗi phân cảnh được tính toán chính xác lượng từ/âm tiết theo tốc độ phát âm tự nhiên của ngôn ngữ mục tiêu (kết thúc câu nói trước khoảng nghỉ cuối cảnh `7.0s – 8.0s`) để không bao giờ bị cắt cụt câu nói khi chuyển cảnh.

---

## PHẦN 2: QUY TRÌNH KỸ THUẬT TRIỆT TIÊU 100% "SẠN" AI TRÊN NANO BANANA & VEO 3.1

Bất kể chủ đề hay phong cách nào được chọn ở Phần 1, khi đưa vào sản xuất trên **Nano Banana 2.1/Pro** và **Veo 3.1**, hệ thống luôn áp dụng **3 Kỹ thuật Cốt lõi**:

### Kỹ thuật 1: Tách Bạch "Thực Thể Gốc" và "Đạo Cụ Rời" (`Zero-Prop Base Identity Sheet`)
* Khi tạo ảnh tham chiếu nhân vật/thực thể (`Character / Subject Ingredient`) bằng Nano Banana:
  - Không bao giờ vẽ nhân vật cầm sẵn các đạo cụ rời sẽ bị buông/ném/thay đổi trong kịch bản (như điện thoại, ly nước, công cụ, vũ khí rời).
  - Giữ giải phẫu chuẩn xác, tư thế tự nhiên (`clean anatomy, natural neutral posture, empty hands, no detached props glued to hands`).
* Nhờ đó, Veo 3.1 hiểu đúng cấu trúc cơ thể gốc của nhân vật và không bao giờ vẽ mọc thêm tay thứ 3, thứ 4 hay vẽ nhân đôi đạo cụ khi nhân vật thao tác.

### Kỹ thuật 2: Dàn Dựng Khung Hình Đầu & Cuối Bằng Keyframe (`Composite Keyframe Bridging: Frames-to-Video`)
* Với các cảnh có:
  - **Nhiều nhân vật tương tác trong cùng khung hình** (2 người đối thoại, nhóm người, nhân vật chính + quần chúng), HOẶC
  - **Thay đổi trạng thái vật lý của đồ vật/môi trường** (đang cầm vật thể $\rightarrow$ làm rơi vật thể; trước va chạm $\rightarrow$ sau va chạm):
* Thay vì chỉ ném các ảnh Ingredients rời rạc vào Veo 3.1 để nó tự ghép ngẫu nhiên, Agent dùng **Nano Banana Pro** tạo ra:
  1. **First Frame (Khung hình Bắt đầu)**: Bố cục hoàn chỉnh cả bối cảnh, vị trí các nhân vật chính/phụ/quần chúng và trạng thái đạo cụ lúc bắt đầu cảnh.
  2. **Last Frame (Khung hình Kết thúc — khi cần khóa trạng thái cuối)**: Bố cục lúc kết thúc cảnh (ví dụ: vật thể đã nằm dưới sàn, hai tay nhân vật trống không, tư thế hoàn toàn sạch).
* Đưa `First Frame` (và `Last Frame`) vào chế độ **Khung hình sang Video (`Frames to Video`)** của Veo 3.1 $\rightarrow$ Chuyển động nội suy ở giữa mượt mà, sạch 100% và đúng ý đồ đạo diễn.

### Kỹ thuật 3: Kiểm Định Thị Giác Tự Động Bằng Lưới Frame (`Automated Contact-Sheet Vision QA`)
* Trước khi ghép nối bất kỳ clip nào vào thành phẩm cuối cùng, hệ thống chạy `python scripts/studio_helper.py qa-frames` (chạy đa luồng trên 12 luồng CPU Ryzen 5 5600H chỉ trong `0.8 giây`) để trích xuất lưới 4 khung hình (`10%, 40%, 70%, 92%` thời lượng) của từng clip.
* Agent trực tiếp quan sát lưới frame (`view_file`) để kiểm tra giải phẫu, vật lý đạo cụ và bố cục trước khi xuất bản.

---

## PHẦN 3: KIẾN TRÚC TĂNG TỐC ĐỘT PHÁ (HYPER-PARALLEL TURBO PIPELINE CHO VIDEO 1 PHÚT $\rightarrow$ 5 TIẾNG)

Để giảm thời gian sản xuất từ 40 phút xuống còn **4–6 phút cho video 1 phút** và mở rộng quy mô lên **phim dài 1 tiếng – 2 tiếng – 5 tiếng (450 $\rightarrow$ 2,250 cảnh)** mà vẫn giữ nguyên chất lượng:

### 1. Cơ Chế "Optimistic Zero-Auth-Check" & "In-Core Meta-Prompting" (Tiết kiệm 10–12 phút đầu tiên)
* **Không bao giờ kiểm tra đăng nhập trước**: Hồ sơ Chrome `C:\Users\Asus\chrome_ai_bot` (cổng `9222`) đã lưu phiên đăng nhập cố định của tài khoản Google AI Ultra. Hệ thống mặc định nhảy thẳng vào tạo/mở dự án trên `https://flow.google.com/`. Chỉ khi bị chuyển hướng sang `accounts.google.com` (Exception-driven) thì mới dừng lại báo User.
* **Thực thi Meta-Prompting ngay trong Nhân (`In-Core Gemini 4 Argon Execution`)**: Thay vì mở trình duyệt `gemini.google.com` gõ tay 2 lần và chờ web load mất 8–10 phút, Agent sử dụng trực tiếp trí tuệ nhân **Gemini 4 Argon (High)** để giải phẫu 6 trục và sinh toàn bộ Kịch bản + Bộ Prompt trong **10 giây** (chỉ mở web `gemini.google.com` khi cần khảo sát dữ liệu ngoài hoặc theo yêu cầu đặc biệt).

### 2. Ngữ Pháp Dựng Phim Chuẩn Điện Ảnh: Phân Biệt "Nối Mượt Trong Cùng Cảnh Dài 16s–24s (`Intra-Scene Continuation`)" vs. "Chuyển Cảnh Bình Thường Sang Góc Máy Mới (`Inter-Scene Hard Cut`)"
* **Sai lầm cần tránh tuyệt đối (`Indiscriminate Chaining`)**:
  - **CẤM nối liền vô tội vạ mọi shot trong toàn bộ video!** Nếu Cảnh 1 đang ở góc toàn cảnh trên không mà lại ép nối (`Frames to Video`) sang Cảnh 2 ở góc cận cảnh bàn chân, hoặc hết một cảnh rồi mà vẫn ép nối sang cảnh khác, AI sẽ phải biến hình (morphing) bối cảnh và kéo máy quay một cách giả tạo, phản điện ảnh.
* **Quy chuẩn Dựng Phim Phân Cấp 2 Chế Độ (`Scene -> Sub-Shots Grammar`)**:
  1. **Chế độ 1 — `INTRA_SCENE_CONTINUE` (Nối Mượt Các Đoạn 8s Trong CÙNG Một Cảnh Dài 16s – 24s+)**:
     - Vì Veo 3.1 mỗi lần chỉ tạo được tối đa `8 giây`, khi kịch bản có một cảnh quay hoặc hành động kéo dài **16 giây (2 clips)** hoặc **24 giây (3 clips)** trong **cùng một không gian / cùng một góc máy hoặc đường chạy máy liên tục**, ta chia Cảnh đó thành các **Sub-Shots (`Shot_A [0–8s]`, `Shot_B [8–16s]`, `Shot_C [16–24s]`)**:
       * *Ví dụ A (Chạy / Di chuyển dài 16 giây)*: Nhân vật chạy từ đầu sân đến cuối sân mất 16 giây $\rightarrow$ `Shot_A (0–8s)` chạy từ đầu sân (`K_start`) đến **giữa sân (`K_mid`)**; `Shot_B (8–16s)` bắt đầu từ **đúng vị trí giữa sân (`K_mid` hoặc trích xuất `Last Frame` của `Shot_A`)** chạy tiếp từ giữa sân đến cuối sân (`K_end`).
       * *Ví dụ B (Đọc bản tin / Thuyết trình / Hội thoại dài 16–24 giây ở cùng góc máy)*: Nhân vật ngồi đọc bản tin 16 giây $\rightarrow$ `Shot_A (0–8s)` nói nửa đầu câu chuyện; `Shot_B (8–16s)` lấy **chính Frame cuối của `Shot_A` (`Last Frame` / `Extend`)** làm Frame đầu để nói tiếp nửa sau mà không hề bị giật khung hình.
     - **Chỉ những cặp Sub-Shots thuộc cùng một cảnh dài (`transition_to_next = "INTRA_SCENE_CONTINUE"`) mới được khóa nối tiếp Frame (`End Frame của A == Start Frame của B`)!**
  2. **Chế độ 2 — `INTER_SCENE_CUT` (Chuyển Cảnh Bình Thường Sang Cảnh Khác / Góc Máy Khác)**:
     - Khi một cảnh (dù là cảnh 8s đơn lẻ hay cảnh dài 16s–24s sau khi đã chạy hết `Shot_B`/`Shot_C`) kết thúc và kịch bản chuyển sang **một góc máy mới, bối cảnh mới hoặc chủ thể mới** $\rightarrow$ Sử dụng **Cắt Chuyển Cảnh Điện Ảnh Bình Thường (`INTER_SCENE_CUT` / `Hard Cut`)**.
     - Ở đầu một Scene mới, khung hình bắt đầu (`Start Frame`) là bức ảnh thiết lập góc máy mới hoàn toàn độc lập, **TUYỆT ĐỐI KHÔNG** lấy frame cuối của cảnh trước ép nối sang!

### 3. Bắn Hàng Đợi Đám Mây Liên Hoàn 2 Làn (`2-Wave Scene-Parallel Cloud Queueing`)
* Nhờ phân tách rõ các **Scenes độc lập (`INTER_SCENE_CUT`)** và các **Sub-Shots nối tiếp nội bộ (`INTRA_SCENE_CONTINUE`)**:
  - **Làn 1 (`Wave 1 - Parallel Scene Openers`)**: Toàn bộ các cảnh đơn 8s và các phần mở đầu `Shot_A (0–8s)` của mọi cảnh dài đều độc lập với nhau $\rightarrow$ Bắn song song cùng lúc lên Google Cloud!
  - **Làn 2 (`Wave 2 - Parallel Intra-Scene Continuations`)**: Với các cảnh dài 16s–24s cần `Shot_B (8–16s)`, dùng khung hình giữa (`K_mid`) hoặc trích xuất `Last Frame` / `Extend` từ `Shot_A` để bắn song song toàn bộ các `Shot_B`!

### 4. Tăng Tốc Phần Cứng Đa Luồng Trên Máy Trạm (`12-Thread Ryzen 5 5600H` + `NVIDIA RTX 3050 NVENC`)
* **Tải file song song 12 luồng (`download-batch`)**: Tải toàn bộ ảnh và video của cả Chapter về ổ cứng cùng lúc chỉ trong **2–3 giây**.
* **Trích xuất QA song song 12 luồng (`qa-frames`)**: Xử lý toàn bộ lưới ảnh kiểm định của 8–12 clip chỉ trong **< 1 giây**.
* **Ghép nối Video Tức Thì (`Zero-Reencode -c copy` + `GPU h264_nvenc`)**:
  - Ghép nguyên bản (`-c copy`) nối 8 cảnh hay 500 cảnh chỉ trong **0.5 – 2 giây** mà không cần render lại từng frame.
  - Khi cần chuẩn hóa tốc độ hoặc xử lý hình ảnh, tự động sử dụng bộ mã hóa phần cứng **`h264_nvenc` trên card rời NVIDIA GeForce RTX 3050** của máy User, nhanh gấp **10–15 lần** so với CPU!

---

## PHẦN 4: HỆ THỐNG BẢN THIẾT KẾ MODEL NHÂN VẬT ĐA GÓC ĐỘ (`AAA CHARACTER MODEL SHEET & RIGGING`) & BỘ LỌC VẬT LÝ CƠ SINH HỌC CHỐNG GIẢ (`BIOMECHANICAL REALISM`)

Một bức ảnh chụp nhân vật ở 1 góc duy nhất **KHÔNG PHẢI** là bản thiết kế nhân vật (Character Model) — khi camera xoay góc hoặc khi nhân vật thực hiện động tác phức tạp, AI sẽ phải tự bịa ra các góc khuất dẫn đến sai lệch tỷ lệ, biến dạng khuôn mặt hoặc làm giả chất liệu.

Để đạt chuẩn thiết kế của các Studio Game AAA / Phim VFX, mỗi nhân vật hoặc chủ thể chính bắt buộc phải được khởi tạo bằng **Bộ Bản Thiết Kế Model Đa Góc Độ (Character Rig Blueprint Pack)** trên Nano Banana 2.1/Pro trước khi đưa vào tạo video:

### 1. Bộ 3 Bản Thiết Kế Model Chuẩn Studio Cho Mỗi Nhân Vật Chính (`3-Sheet Character Rig`)

1. **Bản Thiết Kế 1 — `Orthographic Multi-Angle Turnaround Sheet` (Bản vẽ Xoay Toàn Diện: Trước – Sau – Trái – Phải – Trên Xuống)**:
   - Trên cùng một khung ảnh 16:9 độ phân giải cao, trình bày nhân vật ở **5 góc nhìn chuẩn hình học**:
     * `Front View` (Chính diện trước)
     * `Back View` (Phía sau lưng)
     * `Left Profile View` (Nghiêng trái 90°)
     * `Right Profile View` (Nghiêng phải 90°)
     * `Top-Down / High-Angle 3/4 View` (Góc nhìn từ trên xuống khóa tỷ lệ đầu – vai – thân – đuôi/chân).
   - **Tác dụng kỹ thuật**: Cung cấp đầy đủ hình học 3D (`3D Geometry Prior`) cho bộ mã hóa thị giác của Veo 3.1, giúp nhân vật giữ nguyên 100% cấu trúc cơ thể và hoa văn/trang phục dù camera xoay bất kỳ góc nào.

2. **Bản Thiết Kế 2 — `Articulation, Expression & Hand-State Callout Sheet` (Bản vẽ Chi Tiết Bộ Phận, Khớp Động & Trạng Thái Cầm Nắm)**:
   - Trình bày cận cảnh các bộ phận chuyển động quan trọng của chính nhân vật đó trên một bảng thiết kế:
     * **Với Nhân vật có bàn tay linh hoạt (Con người, Nhân vật 2D/3D, Robot, Tinh linh...)**:
       - `Hand State A (Relaxed Empty Hand)`: Bàn tay mở tự nhiên khi không cầm đồ (đúng 5 ngón/4 ngón chuẩn thiết kế, lòng bàn tay và mu bàn tay).
       - `Hand State B (Active Grip / Holding Pose)`: Tư thế các ngón tay khi nắm/cầm đạo cụ (khóa rõ cách ngón cái và các ngón ôm quanh vật thể).
       - `Hand State C (Pointing / Expressive Gesture)`: Tư thế tay khi ra hiệu hoặc tương tác.
       - `Facial & Mouth Rig`: Khuôn mặt khi khép miệng (`Neutral Closed`), khi phát âm (`Speaking Phoneme`), và khi biểu cảm mạnh (`Emotive`).
     * **Với Sinh vật / Động vật / Khủng long / Máy móc**:
       - `Head & Jaw Rig`: Hộp sọ khi khép hàm tự nhiên vs. khi mở hàm góc 45° (lộ rõ cấu trúc cơ hàm, lưỡi và răng đúng tỷ lệ giải phẫu).
       - `Limb & Foot Rig`: Chi tiết bàn chân chịu lực khi tiếp đất và chi trước khi co/duỗi.

3. **Bản Thiết Kế 3 — `Scale & Anatomy Reference Sheet` (Bản vẽ Khóa Tỷ Lệ Giải Phẫu Thực Tế & Mặt Phẳng Tiếp Đất)**:
   - Đặt nhân vật chính, nhân vật phụ và đạo cụ/vật chuẩn trên cùng một mặt phẳng tham chiếu để **khóa tỷ lệ kích thước chuẩn 1:1 (`Scale Lock`)** (ví dụ: đầu T-Rex dài 1.5m đặt cạnh người 1.8m hoặc con mồi *Edmontosaurus* đúng tỷ lệ thực, tuyệt đối không để AI vẽ khúc xương hay đồ vật to bất thường).

### 2. Hai Tài Nguyên Bổ Trợ Bắt Buộc Trước Khi Dàn Dựng Cảnh (`Clean Plates & Props Library`)

1. **Bối Cảnh Sạch Không Có Nhân Vật (`Environment Clean Plates` trên Nano Banana 2.1)**:
   - Tạo trước ảnh bối cảnh sạch hoàn toàn không có bóng người hay sinh vật (`pristine empty environment plate, no characters, no creatures, clear canopy`).
   - Cung cấp tọa độ ánh sáng, bảng màu và không gian nền thống nhất cho toàn bộ các cảnh trong cùng phân đoạn, chống biến dạng bối cảnh nền.

2. **Thư Viện Đạo Cụ Tách Rời Chuẩn Tỷ Lệ (`Isolated Props Library` trên Nano Banana Pro)**:
   - Bất kỳ đồ vật nào nhân vật sẽ cầm, ném, nhặt hoặc cắn xé (vũ khí, điện thoại, ly nước, công cụ, thức ăn) phải được render độc lập trên nền studio xám trung tính ở 3 góc nhìn (Trước, Nghiêng, 3/4) kèm kích thước vật lý cụ thể (cm/m).
   - Tuyệt đối không để AI tự bịa kích thước đạo cụ khi đang render video.

3. **Cổng Kiểm Định Tài Nguyên Gốc (`audit-assets Gate`)**:
   - Sử dụng lệnh `python scripts/studio_helper.py audit-assets --project "projects/<slug>"` để tự động rà soát toàn bộ Character Rig (5 góc + Articulation + Scale), Bối cảnh sạch và Đạo cụ, xuất lưới ảnh `assets/qa/preprod_assets_qa_grid.jpg`. Chỉ khi đạt `PASS` mới được tiến hành viết kịch bản và ghép Start Keyframe!

### 3. Bộ Lọc Vật Lý Cơ Sinh Học Chống "Cảnh Giả" (`Biomechanical Realism Filter`)
* **Nguyên nhân gây "cảnh giả" (AI Slop / Fake VFX)**:
  - Khi dùng các từ ngữ cường điệu kiểu phim viễn tưởng như `"explosive force"` (lực nổ tung), `"pulverize into dust"` (nghiền thành bụi), `"shockwave"` (sóng xung kích), Veo 3.1 sẽ tạo ra hiệu ứng nổ giả tạo như thuốc nổ TNT hoặc làm vật thể tự vỡ vụn vô lý (như cảnh khúc xương khổng lồ tự nổ tung).
* **Quy tắc Kỹ thuật Bắt buộc**:
  - **CẤM TUYỆT ĐỐI** các từ ngữ gây ảo giác nổ/phép thuật (`explosive`, `explode`, `pulverize`, `shockwave`, `shatter into pieces`, `speed of light`) trong các cảnh đời thực, lịch sử, khoa học, tài liệu.
  - **Thay thế bằng Mô tả Cơ sinh học Thực tế (`Biomechanical & Newtonian Physics`)**:
    * Mô tả rõ **điểm đặt lực, trọng lượng, độ lún, ma sát và quán tính**: Ví dụ thay vì *"cắn nổ tung khúc xương"*, phải viết: *"The adult Tyrannosaurus rex grips the ribcage of a fallen herbivore carcass in its heavy jaws; its thick neck muscles tense as it bites down firmly, bending and cracking the rib bone with a deep crunch while pulling upward with heavy physical weight."*

---

## PHẦN 5: VÒNG LẶP KIỂM DUYỆT PROMPT 3 LẦN (`3-PASS SENIOR AI PROMPT AUDIT LOOP`) & ĐỊNH TUYẾN MODEL THÔNG MINH (`SMART MODEL & CREDIT ROUTER`)

Sau khi Gemini Argon 4 / Pro sinh ra bản nháp Prompt cho Nano Banana và Veo 3.1, **TUYỆT ĐỐI KHÔNG** gửi thẳng vào Google Flow. Mọi prompt bắt buộc phải đi qua **Vòng Lặp Kiểm Duyệt 3 Lần (`3-Pass Audit Loop`)** và **Bộ Định Tuyến Model Theo Độ Khó (`Complexity-Based Model Router`)** bằng lệnh `python scripts/studio_helper.py audit-prompts --project "projects/<slug>"`:

### 1. Quy Trình Kiểm Duyệt & Tinh Chỉnh 3 Vòng (`3-Pass Prompt Audit Loop`)

* **Vòng 1 (`Pass 1 — Semantic Ambiguity & Hallucination Trap Elimination`) — Diệt Bẫy Hiểu Sai & Mơ Hồ Ngữ Nghĩa**:
  - Rà soát từng cụm từ xem Nano Banana hoặc Veo 3.1 có nguy cơ hiểu theo nghĩa đen sai lệch hoặc tự bịa chi tiết không:
    * **Từ khóa phóng đại gây nổ giả**: Tự động phát hiện và viết lại các từ như `explosive force`, `explode`, `pulverize`, `shatter into dust`, `shockwave` thành mô tả cơ sinh học thực tế (`heavy biomechanical jaw pressure`, `visceral muscle tension`, `natural structural fracture`).
    * **Đạo cụ/vật thể chưa khóa tỷ lệ (`Unanchored Scale`)**: Nếu prompt nhắc đến vật thể tương tác (`bone`, `carcass`, `phone`, `cup`, `tool`, `weapon`) mà không ghi rõ kích thước tương đối so với đầu/bàn tay nhân vật, AI rất dễ vẽ vật thể to như tảng đá hoặc nhỏ bất thường. Vòng 1 bắt buộc chèn neo tỷ lệ giải phẫu (`anatomically proportional scale relative to the subject's head/hand, no oversized rock-like props`).
    * **Đại từ nhân xưng mơ hồ (`it`, `they`) trong cảnh nhiều chủ thể**: Thay thế toàn bộ đại từ mơ hồ bằng danh từ định danh rõ chủ thể (`the lead adult T-Rex`, `the prey Edmontosaurus`, `Character A`).

* **Vòng 2 (`Pass 2 — Multi-Angle Model Rig & Hand/Limb Articulation Lock`) — Khóa Bản Thiết Kế Đa Góc Độ & Khớp Cử Động Tay/Hàm**:
  - Kiểm tra toàn bộ `ingredients` và `shots`:
    * Đảm bảo mỗi nhân vật chính có đủ **Bộ 3 Bản Thiết Kế (`Turnaround 5 Góc` + `Articulation Tay Mở/Tay Cầm Đồ/Khẩu Hình` + `Scale Tỷ Lệ Thực`)**.
    * Với mọi cảnh nhân vật dùng tay cầm/buông đồ vật hoặc dùng hàm cắn/nói chuyện, Vòng 2 bắt buộc khóa rõ trạng thái khớp nối (`natural 5-finger anatomical grip wrapping around the object` hoặc `empty relaxed open hands, no duplicate held props`, `consistent 360-degree surface geometry matching the turnaround model sheet`).
    * Kiểm tra tính liên tục tư thế (`start_pose` của Shot $N+1$ phải khớp 100% với `end_pose` của Shot $N$).

* **Vòng 3 (`Pass 3 — Cinematography, Vocal/Audio Timing & Anti-Artifact Guard`) — Tối Ưu Điện Ảnh, Nhịp Thoại & Khóa Chống Sạn Cuối Cùng**:
  - Kiểm tra tiêu cự ống kính (`35mm`, `50mm`, `85mm`), hướng ánh sáng vật lý, âm thanh hiện trường (`Diegetic SFX`), và độ dài câu thoại/thuyết minh (đảm bảo kết thúc trước giây `7.0s`).
  - Đính kèm bộ khóa chất lượng Studio ở cuối mỗi prompt chưa có: `consistent character model geometry across all angles, realistic biomechanical weight, no extra limbs, no morphing, no fake explosions, no subtitles, no on-screen text`.

---

### 2. Bộ Định Tuyến Model Thông Minh Theo Độ Khó & Tối Ưu Ngân Sách 85,000 Credits (`Dynamic Model & Credit Router`)

Hệ thống quản lý ngân sách **85,000 tokens/credits** (cộng thêm `+50 credits` hồi phục mỗi ngày) một cách thông minh, không lãng phí nhưng luôn ưu tiên chất lượng cao nhất cho các cảnh khó:

#### A. Định tuyến Model Tạo Ảnh & Bản Thiết Kế (`Nano Banana 2.1` vs. `Nano Banana Pro`)
| Loại Thực Thể / Khung Hình | Độ Khó Kỹ Thuật | Model Được Chọn Tự Động | Lý Do Kỹ Thuật |
| :--- | :---: | :---: | :--- |
| **Bộ 3 Bản Thiết Kế Nhân Vật Chính** (`Turnaround 5 Góc`, `Articulation Tay Mở/Tay Cầm Đồ`, `Scale Sheet`) & **Composite Keyframe Đa Nhân Vật** | **Cao (`HIGH`)** | **`Nano Banana Pro`** | Cần độ chính xác hình học 5 góc chiếu trực giao tuyệt đối, khớp ngón tay chuẩn giải phẫu và giữ đúng tỷ lệ nhiều nhân vật. |
| **Bối Cảnh Môi Trường Tĩnh (`Environment Plates`)**, Đạo Cụ Đơn Lẻ, Cảnh Thiên Nhiên Không Có Nhân Vật Phức Tạp | **Thấp – Trung Bình (`LOW/MED`)** | **`Nano Banana 2`** *(2.1)* | Tốc độ sinh ảnh cực nhanh, chất lượng ánh sáng và môi trường rất tốt mà không cần tốn tài nguyên Pro. |

#### B. Định tuyến Model Tạo Video (`Veo 3.1 - Fast [10 tokens]` vs. `Veo 3.1 - Quality [100 tokens]`)
Mỗi cảnh `Shot` được chấm **Điểm Phức Tạp (`Complexity Score` từ 1 đến 10)** dựa trên 4 tiêu chí cơ sinh học & điện ảnh:
1. **Tương tác đa chủ thể (`Two-Shot / Group / Predator-Prey Combat`)**: `+4 điểm`
2. **Tương tác vật lý phức tạp của Bàn tay / Cơ hàm / Đạo cụ / Nước & Bùn (`Gripping, Dropping, Biting, Crushing, Fighting, Splash`)**: `+4 điểm`
3. **Chuyển động Camera phức tạp hoặc Chuyển trạng thái `Frames to Video` (`360 Orbit, Fast Tracking, Extreme Macro`)**: `+2 điểm`
4. **Cảnh Mở Đầu Thu Hút (`Hook Shot 01`) hoặc Cảnh Cao Trào (`Climax Shot`)**: `+3 điểm`

* **Quy tắc Chọn Model Tự Động**:
  - **`Complexity Score >= 4` $\rightarrow$ Chọn `Veo 3.1 - Quality` (`100 tokens/clip`)**: Bắt buộc dùng cho mọi cảnh có tương tác vật lý phức tạp (như T-Rex cắn mồi, hai khủng long giao chiến, nhân vật cầm/thả đồ vật, quay cận cảnh bàn tay/cơ hàm, hoặc cảnh Hook mở đầu) để đảm bảo vật lý cơ sinh học chân thực tuyệt đối.
  - **`Complexity Score < 4` $\rightarrow$ Chọn `Veo 3.1 - Fast` (`10 tokens/clip`)**: Dùng cho các cảnh đơn giản mà model nào cũng làm tốt (cảnh toàn môi trường, cảnh đi bộ chậm một mình, cảnh bầu trời/thiên nhiên, cảnh B-roll thuyết minh đơn giản), giúp **tiết kiệm 90% token trên các cảnh đơn giản** (10 token thay vì 100 token) để dồn toàn lực `Quality` cho các cảnh đắt giá!
