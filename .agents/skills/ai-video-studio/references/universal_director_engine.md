# Tư duy Đạo diễn & Biên đạo Chuẩn Top 0.1% Thế giới — Áp dụng cho mọi chủ đề

Tài liệu này là phần "nghề làm phim" mà công cụ không tự làm thay được. Veo 3.1 chỉ là máy quay; **100% sự liền mạch, kịch tính và thời lượng thực chất của bộ phim nằm ở Kịch bản Phân cảnh (`Director Bible`), Biên đạo Trạng thái (`FSM Continuity`), Dựng phim và Âm thanh.**

Chi tiết toàn bộ hệ quy chiếu Top 0.1% (Spielberg / ILM, Peter Jackson / Weta, George Miller, Yuen Woo-ping, Chad Stahelski, Vince Gilligan): xem [`docs/WORLD_CLASS_0_1_PERCENT_DIRECTOR_STANDARD.md`](../../../docs/WORLD_CLASS_0_1_PERCENT_DIRECTOR_STANDARD.md).

---

## 1. Quy luật Tối thượng: Nội dung sinh ra Thời lượng (Cấm kéo giãn hậu kỳ)

- **1 Shot trong Kịch bản = 1 Biến cố Vi mô Duy nhất (`3.5s – 5.0s` sau dựng) = 1 Clip Tạo Mới.**
- **Cấm tuyệt đối:** Không bao giờ lấy 14–22 clip gốc rồi cắt vụn hoặc ghép Take 1 nối tiếp Take 2 của cùng một prompt để "chày cối" kéo dài thành 5 phút. Nếu video bị lặp hoặc đứt mạch, nguyên nhân gốc là **kịch bản thiếu số lượng biến cố hành động và thiếu trạng thái chuyển tiếp**.
- **2 Chế độ Định cỡ Thời lượng của Đạo diễn:**
  1. **Chế độ Thời lượng Cố định (`Fixed Target Duration` — khi User giao mốc cụ thể, vd: 5 phút = `300s`):**
     - Tính ngay ngân sách shot duy nhất: $N_{\text{shots}} = \lceil T / \text{ASL} \rceil$ (với $\text{ASL} \approx 3.8\text{s}-4.2\text{s}$ cho hành động $\Rightarrow$ 5 phút cần **70–78 shots độc lập**).
     - Phân rã từ trên xuống (`Top-Down Time-Boxing`):
       - **Tầng Hồi (`Acts`):** Cứ mỗi `60s` là 1 Hồi gắn với **1 Tiểu Đấu trường / Bối cảnh mới (`arena_stage`)** và **1 Bước ngoặt Lật kèo (`Major Reversal`)**. (5 phút = 5 Hồi × 60s).
       - **Tầng Hiệp (`Exchanges`):** Mỗi Hồi 60s chia thành **3 Hiệp giao tranh / Nhịp cảnh (`20s/hiệp`)**.
       - **Tầng Tế bào 4–5 Shot (`Action-Reaction Cell`):** Mỗi Hiệp 20s gồm 4–5 shot nối tiếp nhân quả: `[1] Telegraph/Lấy đà` $\rightarrow$ `[2] Strike/Va chạm toàn thân` $\rightarrow$ `[3] 85mm Macro Điểm tiếp xúc/Vết thương` $\rightarrow$ `[4] Knockdown/Văng ngã đổi tư thế` $\rightarrow$ `[5] Recovery/Phản kích thoát hiểm`.
  2. **Chế độ Đạo diễn Tự Định cỡ (`Director-Evaluated Optimal Duration` — khi User giao ý tưởng và cho phép dài tùy ý từ 1 phút đến 60+ phút):**
     - Đánh giá **Chỉ số Độ Phức Tạp Tự Sự (`NCI`)** trên 5 trục: Quy mô nhân vật, Chiều sâu xung đột, Độ rộng bản đồ/đấu trường, Kho chiến thuật/bước ngoặt, và Nhịp thở/bối cảnh khoa học.
     - Đề xuất rõ **4 Gói Thời lượng** để User chọn hoặc ủy quyền:
       - `Short / Teaser (60s–120s | 18–30 shots)`: 1 cao trào duy nhất.
       - `Theatrical Set-Piece (5 Phút / 300s | 70–78 shots)`: 5 Hồi – 5 Đấu trường liên hoàn.
       - `Extended Short Film (12–15 Phút | 180–220 shots)`: 3 Chương lớn (Rình mò mở màn $\rightarrow$ Đụng độ & Rút lui trong đêm bão $\rightarrow$ Quyết chiến sinh tử tại hẻm núi/vực thác).
       - `Feature / Anthology Episode (30–60 Phút | 450–900 shots)`: Cấu trúc 8 Sequences điện ảnh có A-Plot, B-Plot, phát triển nhân vật và thế giới hoàn chỉnh.

---

## 2. Giao thức Máy Trạng thái Hữu hạn (`FSM Continuity`) — Chống AI đọc nhầm kịch bản

AI tạo video không có trí nhớ giữa các shot. Nếu Shot $k$ kết thúc khi nhân vật đang nằm bẹp dưới bùn mà Shot $k+1$ chỉ viết *"Nhân vật quất đuôi tấn công"*, AI sẽ tự vẽ nhân vật đứng thẳng lành lặn, gây nhảy hình phi vật lý.

- **Phương trình Liên tục Bắt buộc giữa 2 Shot cùng cảnh:**
  $$\text{ExitState}(\text{Shot}_{k-1}) \equiv \text{EntryState}(\text{Shot}_{k})$$
- **6 Trường Đạo diễn có cấu trúc trên mỗi Shot:**
  1. `entry_state`: Tư thế vật lý (`standing`, `crouched`, `pinned_on_right_flank`), vị trí Trái/Phải, khoảng cách ở `t = 0.0s` (khớp 100% với `exit_state` của shot trước).
  2. `causal_link`: Bắt đầu bằng `"THEREFORE:"` (*Vì vậy*) hoặc `"BUT:"` (*Nhưng*). Cấm nối cảnh bằng kiểu liệt kê *"Và rồi"*.
  3. `action` + `timeline_phases`: Quỹ đạo động học 3 pha (`0.0-2.5s` Phát lực $\rightarrow$ `2.5-5.5s` Va chạm $\rightarrow$ `5.5-8.0s` Hệ quả). Chỉ dùng động từ cơ sinh học nhìn thấy được, không viết câu tâm lý trừu tượng.
  4. `exit_state`: Tư thế và vị trí kết thúc ở `t = 8.0s` (khóa `last_frame_prompt` và truyền cho shot kế tiếp).
  5. `arena_stage`: Tiểu đấu trường / vùng địa hình liền kề hiện tại (vd: `ZONE_1_DRY_COASTAL_CLEARING` $\rightarrow$ `ZONE_2_MUDDY_MARSH` $\rightarrow$ `ZONE_3_ROCKY_SHORELINE` $\rightarrow$ `ZONE_4_BREAKING_SEA_SURF` $\rightarrow$ `ZONE_5_COASTAL_REEF_SPIT`).
  6. `character_states`: Trạng thái thương tích, bùn đất, nước biển, mồ hôi/hơi thở tích lũy tăng dần (`L0_fresh` $\rightarrow$ `L1_dusty_scratched` $\rightarrow$ `L2_mud_coated` $\rightarrow$ `L3_sea_soaked_bleeding` $\rightarrow$ `L4_exhausted_heavy_panting`), không bao giờ tự nhiên sạch lại ở cảnh sau.

### 2b. Định luật Bản đồ Địa lý Liền kề & Hợp thức hóa Vật lý (`Contiguous Map & Grounded Plausibility`)
- **5 Đấu trường là 5 Vùng Địa hình Liền kề trên cùng 1 Bản đồ Sinh thái (`Đất liền` $\leftrightarrow$ `Đầm lầy` $\leftrightarrow$ `Bờ biển` $\leftrightarrow$ `Dưới biển`):** Tuyệt đối không cắt cảnh nhảy cóc sang nơi xa lạ, cũng không làm mặt đất tự nhiên nổ vỡ vô lý. Ngay ở góc rộng Vùng 1 (đất liền), hậu cảnh đã thấy đầm lầy và biển nằm kế bên.
- **Cầu nối Dịch chuyển Vật lý 3 Shot (`3-Shot Zone-Transition Bridge`):** Mỗi khi chuyển từ vùng A sang vùng B (vd: từ bờ đất xuống biển), bắt buộc phải có chuỗi nhân quả vật lý:
  1. `Shot Cầu nối 1 (Đẩy lùi / Quăng xuống nước / Vừa chạy vừa đánh)`: Một con bị húc lùi, bị quăng qua mép bờ rơi xuống biển, hoặc chủ động vừa đánh trả vừa chạy xuống biển/đầm lầy để mượn địa hình cản tốc độ đối thủ.
  2. `Shot Cầu nối 2 (Tiếp đất & Đứng dậy tại địa hình mới)`: Con bị quăng xuống biển rơi tung bọt sóng, lập tức đạp chân xuống đáy cát đứng dậy ngay tại chỗ vừa rơi xuống.
  3. `Shot Cầu nối 3 (Nhảy theo Truy kích)`: Con trên bờ lao tới phóng/nhảy thẳng xuống vùng nước biển ngay trước mặt nơi đối thủ vừa đứng dậy để tiếp tục giao chiến (`lint-prompts` kiểm tra `UNBRIDGED_ARENA_TELEPORT`).
- **Hợp thức hóa Vật lý & Yếu tố Siêu nhiên/Sci-Fi (`Grounded Plausibility`):**
  - *Địa hình nào — Cơ sinh học đó:* Trên đất liền (lượn vòng thăm dò, khóa hàm vật ngã, đánh lùi giữ khoảng cách); trong đầm lầy (chân lún bùn sâu, trượt ma sát); dưới biển (sức cản nước biển làm bước chạy nặng nề, sóng đánh lệch trọng tâm, vật ngã dưới nước có nguy cơ sặc nước/ngạt thở).
  - *Hợp lý hóa Siêu nhiên/Khoa học viễn tưởng:* Nếu có năng lượng, tia nhiệt, điện sinh học hay phép thuật, cấm "thích làm gì thì làm". Phải có: (1) Dấu hiệu nạp/tích tụ sinh học trước khi phát chiêu, (2) Phản lực Newton đẩy lùi chân trụ + tương tác nhiệt/vật lý thật với môi trường (tia nhiệt chạm nước biển bốc hơi thành sương mù trắng xóa), và (3) Tiêu hao thể lực/thở dốc sau chiêu lớn.

---

## 3. Kể chuyện & Cấu trúc Kịch tính

- **Hook 3 giây đầu** là hình ảnh mạnh nhất hoặc một câu hỏi gây tò mò cụ thể. Tránh câu mở sáo rỗng ("Hàng triệu năm trước...", "Bạn có biết...").
- **Cấu trúc**: vấn đề / câu hỏi → 2–3 nhịp leo thang (mỗi nhịp có bước ngoặt `BUT / THEREFORE`) → payoff (câu trả lời, đòn tất sát, twist, cảm xúc) → kết.
- **Cho xem, đừng kể**: mỗi câu lời dẫn phải có hình minh họa đúng nội dung câu đó. Nếu lời dẫn nói "khứu giác siêu nhạy", hình phải cho thấy hành vi đánh hơi/lần theo dấu vết.
- **Chính xác nội dung**: kiểm tra sự thật khoa học/lịch sử với Gemini kèm nguồn; hình ảnh phải khớp (ví dụ: đã nói T-Rex có môi che răng thì hình không được lộ răng khi ngậm miệng).

---

## 4. Chọn chế độ Veo theo shot

| Nhu cầu | Chế độ | Ghi chú |
|---|---|---|
| Cảnh không nhân vật cố định | `text` | B-roll, thiên nhiên, hiện tượng. |
| Nhân vật/sản phẩm nhất quán | `ingredients` | 1–3 ảnh tham chiếu sạch. |
| Bố cục/góc máy chính xác | `first_frame` | Frame từ Nano Banana Pro dựng trên ảnh tham chiếu, đúng tỷ lệ khung. |
| Chuyển động có điểm đến | `first_last` | Hai frame cùng cỡ cảnh, góc máy, ánh sáng; khóa `entry_state` (START) và `exit_state` (END). |
| Hành động kéo dài cùng cảnh | `extend` | Giữ quán tính; chất lượng giảm sau vài lần extend. |

Độ khó cao (Quality): tương tác tay/đạo cụ, nhiều chủ thể chạm nhau, cận chi tiết giải phẫu, nhép miệng, hook/kết. Cảnh dễ (Fast): phong cảnh, 1 chủ thể chuyển động đơn giản. `build-prompts` tự chấm điểm và định tuyến.

---

## 5. Ngôn ngữ máy quay & Định luật Tương tác Vật lý

- **Chọn ống kính theo lực va chạm (`Lens-to-Impact Matching`):**
  - Cảnh lao vào nhau, quật ngã, di chuyển địa hình: dùng `24mm–35mm Anamorphic Wide`, đặt máy thấp ngang tầm mắt người (`1.2m Ground-Level`) có tiền cảnh mờ (`foreground occlusion`) để tôn quy mô khổng lồ.
  - Cảnh răng cắn ngập vào cổ, móng vuốt cào rách da, lưỡi kiếm chạm giáp: **bắt buộc cắt vào `85mm–100mm Macro Close-Up`** để vùng tiếp xúc chiếm `>35%` khung hình (dùng góc rộng 24mm sẽ bị cảm giác trượt bề mặt).
- **Quy tắc 180° & Tâm điểm Ánh nhìn (`Crosshair Eye-Trace`):** Giữ hướng nhìn/vị trí Trái-Phải nhất quán giữa các shot liên tiếp; đặt điểm va chạm gần trung tâm khung hình để mắt người xem không phải tìm kiếm qua cú cắt nhanh.
- **Định luật Chậm Trễ Cơ Học 3 Nhịp:** Dồn trọng lượng lún đất $\rightarrow$ Va chạm truyền sóng cơ bắp (trễ 0.15s) $\rightarrow$ Dư chấn môi trường (bùn/nước bắn, cây gãy, rung máy tự nhiên).

---

## 6. Dựng phim

- **Clip 8s ≠ shot 8s.** Shot sau dựng thường 2–5s (video ngắn 1.5–3s). Tạo nguyên liệu dư, chọn đoạn đẹp nhất (`edit_in`/`edit_out`).
- **Mỗi cú cắt là 1 shot mới:** Không lặp lại đoạn clip đã chiếu.
- **Hard cut là mặc định.** Dissolve = thời gian trôi / đổi chương. Không dùng hiệu ứng chuyển cảnh để che lỗi.
- **Dựng theo lời dẫn và nhạc**: hình cắt theo nhịp câu và phách nhạc; để khoảng thở (0.5–1.5s không lời) sau ý quan trọng.
- **Màu đồng bộ**: clip AI lệch màu nhau → áp 1 LUT chung (`assemble --lut`), chọn take có tông gần nhau.

---

## 7. Âm thanh (một nửa trải nghiệm xem)

- 3 lớp: **lời** (lời dẫn TTS/thu âm 1 giọng, hoặc thoại Veo ngắn) + **SFX/không khí** (Veo làm rất tốt) + **nhạc** (tự hạ khi có lời).
- Chuẩn hóa −14 LUFS (YouTube/TikTok), đỉnh ≤ −1.5 dBTP — `assemble` tự làm.
- Lời dẫn nhiều shot không để Veo đọc: mỗi lần tạo là một giọng khác.

---

## 8. Phát hành & Bảo đảm chất lượng

- **9:16** cho TikTok/Shorts/Reels — tạo ở 9:16 từ đầu; crop từ 16:9 chỉ là phương án dự phòng (`crop_focus_x`).
- **Phụ đề**: in cứng cho video ngắn (`--burn-subs`); file `.srt` đăng kèm cho YouTube.
- **1080p** tối thiểu: tải bản 1080p/upscale từ Flow.
- **6 Cổng Kiểm Duyệt Tiền Kỳ (`lint-prompts --strict`)**: Đủ ngân sách shot duy nhất (`UNDERBUDGETED_SHOT_COUNT`), khớp trạng thái đầu/cuối (`FSM_POSTURE_DISCONTINUITY`), liên kết nhân quả (`THEREFORE/BUT`), biến đổi đấu trường (`STATIC_ARENA_FATIGUE`), góc máy đa chiều và QA thị giác từng take (`qa-takes` $\rightarrow$ `auto-select`).
