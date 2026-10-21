# TIÊU CHUẨN ĐẠO DIỄN & BIÊN ĐẠO ĐIỆN ẢNH TOP 0.1% THẾ GIỚI (WORLD-CLASS 0.1% DIRECTOR & CHOREOGRAPHY STANDARD)

> **Tuyên ngôn Cốt lõi (The Iron Law of Pre-Production):**
> **Mọi giây thời lượng trên màn ảnh phải được sinh ra từ NỘI DUNG KỊCH BẢN & BIÊN ĐẠO TIỀN KỲ, tuyệt đối không sinh ra từ việc cắt nhỏ, lặp lại hay kéo giãn clip cũ ở hậu kỳ.**
> Khi một bộ phim AI bị đứt mạch, nhảy vị trí, lặp cảnh hoặc AI hiểu sai ý đồ tạo ra video lỗi, **95% nguyên nhân gốc rễ nằm ở Tài liệu Đạo diễn & Kịch bản Phân cảnh (`Director Bible & Shot Choreography`) chưa đạt độ chi tiết Cơ học Nhân quả (Causal Finite-State Machine)** — khiến bộ biên dịch Prompt và mô hình Video (Veo 3.1) phải "tự đoán" trạng thái đầu/cuối của từng cảnh.

Tài liệu này đúc kết bộ quy chuẩn của **Top 0.1% Đạo diễn, Chỉ đạo Võ thuật/Hành động, Giám sát Pre-vis & Showrunner xuất sắc nhất thế giới**:
- **Chỉ đạo Hành động & Võ thuật (0.1% Action Choreography):** Yuen Woo-ping (*The Matrix*, *Ngọa Hổ Tàng Long*), Chad Stahelski & 87Eleven (*John Wick 1–4*), Gareth Evans (*The Raid 1 & 2*).
- **Đạo diễn Đại cảnh Sinh vật & Pre-vis Khối lượng lớn (0.1% Creature & Blockbuster Pre-vis):** Steven Spielberg & Phil Tippett / ILM (*Jurassic Park*, *Jurassic World*), Peter Jackson & Weta Digital (*King Kong 2005* — trận Kong đấu 3 V-Rex dài 7 phút liên tục), George Miller (*Mad Max: Fury Road*), Genndy Tartakovsky (*Primal*).
- **Kiến trúc sư Kịch bản & Nhịp độ Điện ảnh (0.1% Showrunners & Dramaturgs):** Christopher Nolan, Denis Villeneuve, Vince Gilligan (*Breaking Bad*), Craig Mazin (*Chernobyl*, *The Last of Us*), Robert McKee (*Story*).

---

## PHẦN 1: CHẨN ĐOÁN GỐC RỄ — VÌ SAO NỘI DUNG SƠ SÀI KHIẾN AI ĐỌC NHẦM VÀ TẠO VIDEO SAI?

### 1.1. Chuỗi Domino Lỗi từ Nội dung đến Video (`The Garbage-In Hallucination Chain`)
Mô hình tạo video AI (như Veo 3.1) **không có bộ nhớ dài hạn giữa các lần bấm tạo clip**. Mỗi Shot 8 giây là một vũ trụ độc lập đối với AI.

```mermaid
flowchart LR
    A["1. Kịch bản viết chung chung<br/>(Chỉ ghi hành động, thiếu Trạng thái Đầu/Cuối)"] --> B["2. Prompt sinh ra bị hổng<br/>(Không khóa tư thế xuất phát từ kết quả cảnh trước)"]
    B --> C["3. AI tự suy diễn tư thế mặc định<br/>(Đang nằm bẹp ở Shot 8 -> Tự đứng dậy lành lặn ở Shot 9)"]
    C --> D["4. Video đứt gãy & Thiếu nguyên liệu<br/>(14-22 clip không đủ lấp 5 phút)"]
    D --> E["5. Hậu kỳ chắp vá<br/>(Kéo giãn/xài lại Take 1 + Take 2 -> Lặp hành động)"]
```

### 1.2. 4 Căn bệnh Kinh điển của Kịch bản khiến AI "Đọc Nhầm"
1. **Hội chứng "Mất Trí Nhớ Trạng Thái" (`State Amnesia between Shots`):**
   - *Ví dụ lỗi:* Shot 08 mô tả *"Rex quật ngã Vasto xuống bùn"*. Shot 09 viết *"Vasto tung cú quất đuôi vào mặt Rex"*.
   - *Vì sao AI làm sai:* Khi đọc Shot 09, AI không hề biết ở cuối Shot 08 Vasto đang **nằm nghiêng dưới bùn**. AI lập tức vẽ Vasto đang đứng thẳng hai chân bình thường để quất đuôi -> Khi ghép Shot 08 với Shot 09, khán giả thấy Vasto "dịch chuyển tức thời" từ nằm bẹp sang đứng thẳng!
   - *Cách 0.1% Đạo diễn viết:* Shot 09 bắt buộc phải mở đầu bằng `entry_state`: *"Vẫn đang nằm nghiêng bên sườn phải dưới lớp bùn sâu sau cú quật của Rex, Vasto lấy điểm tựa từ bả vai, bất ngờ xoay hông quất ngược khúc đuôi vảy sừng từ dưới thấp văng ngược lên trúng hàm Rex (`low-to-high sweeping tail counter-strike from prone position`)"*, giúp Vasto vừa đánh lùi Rex vừa có thời gian chống chân đứng dậy ở cuối Shot 09 (`exit_state: cả hai lùi ra 4m, đứng gầm gừ`).
2. **Hội chứng "Văn Kể Chuyện Trừu Tượng" (`Abstract Narrative Prose vs. Kinematic Verbs`):**
   - *Ví dụ lỗi:* *"Vasto nhận ra không thể đọ sức mạnh trực diện nên quyết định dùng sự linh hoạt để phản công."*
   - *Vì sao AI làm sai:* Máy quay không chụp được chữ *"nhận ra"* hay *"quyết định"*. AI sẽ tạo ra một con khủng long đứng đơ tại chỗ há miệng vô nghĩa.
   - *Cách 0.1% Đạo diễn viết:* Mọi ý đồ tâm lý phải dịch 100% sang **Động từ Cơ sinh học (`Biomechanical Verbs`)**: *"Đôi đồng tử vàng của Vasto co rút lại; nó hạ thấp trọng tâm sát mặt nước, lách qua dưới cổ Rex với tốc độ cực nhanh rồi bấu móng vuốt chân sau vào bắp đùi đối thủ."*
3. **Hội chứng "Thiếu Ngân sách Hành động cho Thời lượng" (`Action Starvation`):**
   - *Ví dụ lỗi:* Muốn làm phim 5 phút (`300 giây`) nhưng kịch bản chỉ có 14 hoặc 22 ý hành động.
   - *Hệ quả:* Dù có chia đôi mỗi clip hay lấy cả Take 1 lẫn Take 2 ghép vào, người xem vẫn nhận ra chỉ có bấy nhiêu đòn đánh lặp đi lặp lại trong cùng một vũng nước suốt 5 phút.
4. **Hội chứng "Đấu Trường Đóng Băng & Máu Tự Lành" (`Static Arena & Resetting Damage`):**
   - Đánh nhau 5 phút nhưng bối cảnh từ phút thứ 1 đến phút thứ 5 vẫn y hệt một góc rừng; vết thương, bùn đất bám trên da ở cảnh trước sang cảnh sau biến mất sạch sẽ.

---

## PHẦN 2: KIẾN TRÚC THỜI LƯỢNG KÉP (DUAL-MODE RUNTIME ARCHITECTURE)

Đạo diễn Top 0.1% luôn làm việc theo **2 Chế độ Thời lượng** tùy theo yêu cầu của Nhà sản xuất (User):

```mermaid
flowchart TD
    U["Yêu cầu từ Nhà sản xuất (User)"] --> M1["CHẾ ĐỘ 1: THỜI LƯỢNG CỐ ĐỊNH<br/>(User giao mốc cụ thể: vd 1 phút, 3 phút, 5 phút)"]
    U --> M2["CHẾ ĐỘ 2: ĐẠO DIỄN TỰ ĐỊNH CỠ THỜI LƯỢNG<br/>(User giao ý tưởng/câu chuyện, cho phép dài tùy ý: 1 phút -> 60+ phút)"]
    M1 --> B1["Phân rã Từ Trên Xuống (Top-Down Time-Boxing):<br/>Thời lượng T -> Số Hồi (Acts) -> Số Hiệp (Exchanges) -> N Shot Duy Nhất"]
    M2 --> B2["Đánh giá Từ Dưới Lên (Bottom-Up Dramaturgy):<br/>Chấm chỉ số Độ phức tạp NCI -> Đề xuất 3-4 Gói Thời lượng Chuẩn"]
```

### 2.1. Định luật Bất biến về Mật độ Shot (`The 1:1 Unique Shot Density Law`)
Trong điện ảnh chuyên nghiệp (Hollywood / Weta / ILM / Netflix):
- **1 Cú cắt trên phim (`Edited Cut`) = 1 Biến cố Vi mô Mới (`1 Unique Micro-Event`) = 1 Shot Độc lập trong Kịch bản.**
- **Cấm tuyệt đối:** Không bao giờ lấy Take 1 ghép nối tiếp Take 2 của cùng một câu lệnh (`veo_prompt`) để kéo dài thời gian.
- **Công thức tính Số Shot Duy Nhất Bắt Buộc ($N_{\text{shots}}$):**
  $$N_{\text{shots}} = \left\lceil \frac{T_{\text{target}}}{\text{ASL}_{\text{genre}}} \right\rceil$$
  Trong đó $\text{ASL}_{\text{genre}}$ (*Average Shot Length* — độ dài trung bình 1 shot sau khi cắt bỏ đầu/đuôi thừa từ clip Veo 8s):
  - **Hành động / Đại chiến / Võ thuật (`action_blockbuster`, `wuxia_xianxia`):** $\text{ASL} = 3.5\text{s} - 4.2\text{s}$ (tối ưu `4.0s/shot`).
  - **Kinh dị / Khoa học viễn tưởng / Anime (`horror_thriller`, `cyberpunk_scifi`, `anime_2d_3d`):** $\text{ASL} = 4.0\text{s} - 4.5\text{s}$.
  - **Tài liệu Thiên nhiên / Sử thi / Tâm lý (`nature_documentary`, `historical_epic`, `romance_kdrama`):** $\text{ASL} = 4.5\text{s} - 5.5\text{s}$.

#### Bảng Định mức Biên đạo theo Thời lượng (Chuẩn Hành động / Đại chiến $\text{ASL} \approx 4.0\text{s}$):

| Thời lượng Mục tiêu ($T$) | Số Hồi (`Acts`) | Số Đấu trường / Bối cảnh (`Arenas`) | Số Hiệp Giao tranh (`Exchanges`) | Số Bước ngoặt Lật kèo (`Reversals`) | **Số Shot Duy nhất Bắt buộc ($N_{\text{shots}}$)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1 Phút (`60s` — Short/Reels)** | 3 hồi ngắn (20s/hồi) | 1 đấu trường (2 tầng địa hình) | 3 hiệp | 1–2 lần lật kèo | **15 – 18 shots** |
| **3 Phút (`180s` — Set-Piece Chuẩn)** | 3 hồi (60s/hồi) | 3 đấu trường liên hoàn | 9 hiệp | 3 lần lật kèo | **42 – 48 shots** |
| **5 Phút (`300s` — Đại chiến IMAX)** | **5 hồi (60s/hồi)** | **5 đấu trường liên hoàn** | **15 hiệp** | **5 lần lật kèo** | **70 – 78 shots** |
| **10 Phút (`600s` — Phim Ngắn/Tập)** | 5 hồi (120s/hồi) | 6–8 bối cảnh + rượt đuổi | 28–30 hiệp/cảnh | 7–8 lần lật kèo | **140 – 160 shots** |
| **30 Phút (`1800s` — Tập Đặc biệt)** | 4 chương lớn | 12–15 bối cảnh đa sinh cảnh | 80+ phân đoạn | 15+ bước ngoặt | **420 – 480 shots** |
| **60 Phút (`3600s` — Phim Điện ảnh)** | 3 Hồi / 8 Sequences | 25+ bối cảnh (Thế giới hoàn chỉnh) | 160+ phân đoạn | Chuỗi nhân quả đa tuyến | **800 – 950 shots** |

---

### 2.2. CHẾ ĐỘ 1: Khi User giao Thời lượng Cố định (Ví dụ: *"Làm trận đánh nhau 5 phút / 300 giây"*)

Khi có khung thời gian cố định $T = 300\text{s}$, Đạo diễn Top 0.1% (như Peter Jackson biên đạo trận *Kong vs. 3 V-Rexes* hay Gareth Evans biên đạo *The Raid*) không bao giờ viết tràn lan mà chia theo **Cấu trúc Đồng hồ Thụy Sĩ 3 Tầng (`Macro Act -> Meso Exchange -> Micro Cell`)**:

#### Tầng 1 — Bản đồ Địa lý Liền kề 5 Vùng & Cầu nối Dịch chuyển Vật lý (`5 Contiguous Terrain Zones × 60s = 300s`):
> **Nguyên tắc Thực tế Vật lý (`Contiguous Geography Law`):**
> **5 Đấu trường KHÔNG PHẢI là 5 nơi xa lạ tự nhiên cắt cảnh nhảy tới, càng không phải mặt đất tự nhiên nổ vỡ vô lý!**
> Toàn bộ trận chiến phải diễn ra trên **1 Bản đồ Sinh thái Liền kề nhau** (Ví dụ: `Đất liền Bìa rừng` nằm sát cạnh `Đầm lầy ven bờ`, và ngay bên cạnh đầm lầy là `Bãi biển & Vùng nước biển sóng vỗ`). Ngay từ các góc máy rộng (Wide Shot) ở Vùng 1, khán giả đã thấy đầm lầy và biển nằm ở hậu cảnh/bên sườn. Khi chuyển từ vùng này sang vùng kia, **bắt buộc phải do lực tác động vật lý của trận đánh**: vừa đánh vừa lùi, vừa chạy vừa truy kích, hoặc bị quăng/húc văng xuống biển rồi con kia nhảy xuống biển theo để đánh tiếp!

- **HỒI I (`0:00 – 1:00` | 15 Shots | `Vùng 1: Đất Liền Bìa Rừng Ven Biển — Dry Coastal Clearing`):**
  - *Logic Chiến thuật & Vật lý:* Hai con chạm mặt trên nền đất cứng (phía xa bên phải đã thấy đầm lầy và sóng biển). Chúng không lao vào tự sát ngay mà **gầm thăm dò, lượn vòng đo sức (`probing & circling`)** $\rightarrow$ lao vào khóa cổ vật ngã lần 1 $\rightarrow$ dùng vai và đầu **đánh lùi nhau ra (`push-back & spacing`)** để thăm dò phản xạ của đối thủ.
  - *Cầu nối Dịch chuyển Vật lý sang Vùng 2 (`Shots 13–15` — Vừa chạy vừa đánh / Đẩy lùi):* Vasto bị Rex ép lùi bằng sức nặng, vừa táp trả vừa lùi/chạy dọc theo triền dốc dẫn xuống **Đầm lầy bùn ven bờ** để lợi dụng địa hình lầy lội làm chậm bước chạy của Rex; Rex gầm lên lao theo truy kích sát nút.
- **HỒI II (`1:00 – 2:00` | 15 Shots | `Vùng 2: Đầm Lầy Bùn Ven Bờ — Coastal Muddy Marsh`):**
  - *Logic Chiến thuật & Vật lý:* Dưới lớp bùn lầy ngập cổ chân 30–40cm, bàn chân 9 tấn của Rex bị lún sâu làm giảm tốc độ xoay trở. Vasto nhẹ và linh hoạt hơn, liên tục lách qua sườn dùng móng vuốt cào và đớp vào bả vai Rex, làm bùn đen bắn tung tóe lên khắp cơ thể cả hai (**Bước ngoặt 1**: Vasto chiếm ưu thế 70/30 nhờ địa hình bùn).
  - *Cầu nối Dịch chuyển Vật lý sang Vùng 3 (`Shots 28–30` — Vật ngã & Đẩy trượt ra Bãi bờ biển):* Rex chịu đau, chờ lúc Vasto lao vào cắn sườn liền khóa chặt hàm vào cổ Vasto rồi dùng toàn bộ lực chân sau đẩy lùi Vasto trượt băng qua rặng cây ngập mặn, văng thẳng ra **Dải bờ cát & Ghềnh đá sát mép sóng biển**.
- **HỒI III (`2:00 – 3:00` | 15 Shots | `Vùng 3: Bờ Cát & Ghềnh Đá Sát Mép Biển — Rocky Shoreline & Surf Edge`):**
  - *Logic Chiến thuật & Vật lý:* Trên bãi cát ướt và đá tảng ven biển, sóng biển bắt đầu tràn vào mắt cá chân. Cả hai quần thảo dữ dội: quật đuôi, húc đầu làm vỡ các tảng đá风 hóa ven bờ (**Bước ngoặt 2**: Rex dùng sức nặng quật Vasto ngã nghiêng trên bờ cát).
  - *Cầu nối Dịch chuyển Vật lý sang Vùng 4 (`Shots 42–45` — Quăng xuống Biển & Nhảy theo Truy kích):*
    - `Shot 43 (Quăng/Húc xuống biển):` Rex ngoạm bả vai Vasto, dồn lực hông quăng mạnh Vasto văng qua gờ đá bờ biển rơi ầm xuống **vùng nước biển ngập ngang đùi/ngực** cách bờ 6m, cột nước biển tung trắng xóa.
    - `Shot 44 (Đứng dậy dưới biển):` Vasto chới với giữa sóng biển nhưng lập tức đạp chân xuống đáy cát ngầm, đứng bật dậy ngay tại chỗ vừa bị ném xuống, rũ nước mặn khỏi đầu và gầm ngược lên bờ.
    - `Shot 45 (Nhảy xuống biển đấu tiếp):` Không cho đối thủ kịp hồi sức, Rex từ trên gờ bờ đất liền lấy đà **phóng nhảy thẳng xuống vùng nước biển ngay trước mặt nơi Vasto đang đứng**, tạo làn sóng xung kích xô dạt cả hai vào cuộc thủy chiến!
- **HỒI IV (`3:00 – 4:00` | 15 Shots | `Vùng 4: Thủy Chiến Giữa Sóng Biển Ngập Ngực — Chest-Deep Breaking Sea Surf`):**
  - *Logic Chiến thuật & Vật lý (`Hydrodynamic Drag`):* Đánh nhau trong nước biển sâu ngang đùi/bụng khác hẳn trên cạn: sức cản của nước biển làm mọi cú bước chân nặng nề, sóng lớn liên tục đánh vào sườn làm chao đảo trọng tâm, bọt biển trắng xóa trộn lẫn máu từ vết thương.
  - *Diễn biến (**Bước ngoặt 3 — Nguy cơ Chết đuối Sinh học**):* Trong lúc giằng co giữa sóng lớn, Vasto lợi dụng một con sóng ngầm húc lệch chân trụ của Rex làm Rex khuỵu gối xuống nước biển; Vasto chồm lên đè đầu Rex xuống sát mặt nước biển sủi bọt để dìm ngạt thở $\rightarrow$ Khoảnh khắc sinh tử: Đầu Rex bị ép sát mặt nước biển, lỗ mũi ph่น bong bóng nước dữ dội, Rex đạp mạnh hai chân sau vào đáy biển và húc ngược đỉnh sọ từ dưới nước lên trúng hàm dưới của Vasto, hất tung Vasto ngửa ra sau giữa sóng biển.
- **HỒI V (`4:00 – 5:00` | 15 Shots | `Vùng 5: Mỏm Đá Gành Biển & Đòn Kết Liễu — Coastal Reef Spit Climax`):**
  - *Logic Chiến thuật & Vật lý:* Cả hai ướt sũng nước biển, cơ bắp run lên vì kiệt sức, vừa vật lộn vừa dạt lên **Mỏm đá gành nhô ra biển sâu** ngay kế bên.
  - *Diễn biến (**Bước ngoặt 4 — Đòn Tất Sát Hợp Lý Vật Lý**):* Cả hai lấy chút sức lực cuối cùng lao vào nhau. Thay vì những đòn ảo phi vật lý, Rex chủ động chịu một vết cào vào bả vai để luồn hàm xuống dưới cổ Vasto, khóa chặt khí quản rồi lợi dụng chính đà lao của Vasto + độ dốc trơn của mỏm đá ướt, **xoay trụ quật Vasto trượt khỏi mỏm đá gành rơi xuống vùng nước biển sâu sóng dữ bên dưới** (Vasto chìm xuống rồi phải bơi/lội tháo chạy dọc bờ biển) $\rightarrow$ Rex đứng thở dốc trên mỏm đá gành giữa sóng biển đập tung bọt trắng xóa, ngửa cổ gầm vang khẳng định chủ quyền.

#### Tầng 2 — Cầu nối Dịch chuyển Địa hình 3 Shot Bắt buộc (`The 3-Shot Zone-Transition Bridge`):
Mỗi khi cuộc chiến dịch chuyển từ Địa hình $A$ sang Địa hình liền kề $B$ (vd: từ Đất liền $\rightarrow$ Đầm lầy, hoặc từ Bờ biển $\rightarrow$ Dưới biển), Đạo diễn **cấm cắt cảnh nhảy cóc** mà phải viết đủ **Chuỗi 3 Shot Cầu nối Vật lý**:
1. **Shot Cầu nối 1 — Tác động Dịch chuyển (`Displacement / Running Pursuit`):** Một bên bị đánh bật lùi, bị quăng qua ranh giới địa hình, hoặc chủ động vừa chạy vừa đánh sang địa hình kế bên. Khung hình phải thấy rõ **cả địa hình cũ lẫn địa hình mới** nằm cạnh nhau.
2. **Shot Cầu nối 2 — Tiếp đất & Thích nghi Địa hình (`Landing & Terrain Recovery`):** Kẻ bị quăng xuống biển/đầm lầy rơi xuống tạo tương tác vật lý thật (sóng biển tung bọt, bùn văng), sau đó đạp chân tìm điểm tựa đứng dậy ngay tại vị trí vừa rơi xuống.
3. **Shot Cầu nối 3 — Truy kích Nhập cuộc (`Pursuit Entry`):** Kẻ tấn công trên bờ chạy lao xuống hoặc nhảy bổ xuống đúng vị trí dưới biển/đầm lầy nơi đối thủ vừa đứng dậy để tiếp tục giao chiến.

#### Tầng 3 — 15 Hiệp Giao tranh (`15 Tactical Exchanges × 20s`) & Tế bào 5 Shot (`Action-Reaction Cell`):
Trong mỗi Hiệp 20 giây, Đạo diễn viết đúng **4 đến 5 Shot Duy Nhất (`~4.0s/shot`)** theo chu kỳ cơ sinh học thực tế:
1. **Shot 1 — Thăm dò / Lấy đà (`Probe / Telegraph` — `4.0s`):** Lượn vòng giữ khoảng cách, bước chân dồn lực lên đất/bùn/nước biển, ánh mắt khóa mục tiêu.
2. **Shot 2 — Phát lực & Va chạm (`Strike / Clinch` — `4.0s`):** Lao vào khóa hàm, húc vai, quật đuôi theo đúng quán tính khối lượng 8–9 tấn.
3. **Shot 3 — Đặc tả Điểm Tiếp Xúc (`Visceral Macro Insert` — `3.0s`):** Ống kính 85mm–100mm cận cảnh răng/móng vuốt/vũ khí cắm vào da thịt hoặc bàn chân trượt trên đá ướt.
4. **Shot 4 — Hệ quả Vật lý & Vật ngã/Đánh lùi (`Takedown / Push-Back` — `4.5s`):** Bị vật ngã xuống đất/nước hoặc bị đánh bật lùi ra xa để thở dốc (`standing` $\rightarrow$ `prone/staggered_back`).
5. **Shot 5 — Đứng dậy / Chuyển thế Chiến thuật (`Recovery / Tactical Shift` — `4.5s`):** Chống chân đứng dậy, lợi dụng địa hình (bùn, sóng biển, đá ngầm) để đổi thế đánh cho hiệp sau.

---

### 2.2b. ĐỊNH LUẬT HỢP THỨC HÓA VẬT LÝ & SIÊU NHIÊN (`GROUNDED PLAUSIBILITY & RATIONALIZED SCI-FI/SUPERNATURAL LAW`)

Dù phim thuộc thể loại **Hiện thực Tiền sử (`Realistic Prehistoric`)**, **Quái vật Khổng lồ / Khoa học Viễn tưởng (`MonsterVerse / Sci-Fi Mecha`)** hay **Tiên hiệp / Siêu nhiên (`Xianxia / Fantasy`)**, tiêu chuẩn Top 0.1% áp dụng quy tắc sắt: **"Không bao giờ thích làm gì thì làm — Mọi hành động đều phải hợp lý hóa bằng Quy luật Vật lý & Sinh học Nội tại"**:

1. **Định luật Bảo toàn Khối lượng, Đòn bẩy & Sức cản Địa hình (`Mass, Leverage & Terrain Drag`):**
   - Một sinh vật nặng 8–9 tấn không thể tự nhiên bay lơ lửng hay ném đối thủ 8 tấn bay xa 50 mét như quả bóng nhựa. Muốn quăng đối thủ xuống biển, nó phải **khóa hàm vào cổ làm đòn bẩy + lợi dụng đà lao của đối thủ + độ dốc của bờ đất/vách đá** để hất đối thủ mất trụ lăn/rơi xuống biển.
   - **Địa hình nào — Cơ sinh học đó:**
     - *Trên đất liền:* Bước chạy nhanh, dứt khoát, bụi mù, dễ giữ thăng bằng.
     - *Trong đầm lầy:* Bàn chân lún sâu, bước rút chân nặng, dễ trượt ngã khi xoay hông gấp.
     - *Dưới biển / Sóng vỗ:* Nước biển ngập ngang đùi/ngực tạo lực cản thủy động lực học (`hydrodynamic drag`), mỗi bước lao tạo sóng cuộn; khi bị vật ngã dưới nước sẽ bị sặc nước/ngạt thở, buộc nhân vật phải giãy giụa tìm cách ngoi đầu lên khỏi mặt nước.
2. **Định luật Tâm lý Chiến đấu Thực tế (`Realistic Combat Psychology`):**
   - Sinh vật thông minh hoặc võ sĩ thực chiến luôn có nhịp: **Thăm dò (`Probe`) $\rightarrow$ Va chạm & Vật ngã (`Clinch & Takedown`) $\rightarrow$ Đánh lùi tách ra để thở & Quan sát (`Disengage & Assess`) $\rightarrow$ Vừa di chuyển/chạy vừa đánh (`Mobile Skirmish`)**, tuyệt đối không đứng yên một chỗ vung đòn vô hồn.
3. **Định luật Hợp thức hóa Yếu tố Siêu nhiên / Khoa học Viễn tưởng (`Rationalized Supernatural & Sci-Fi`):**
   - Nếu dự án có yếu tố siêu nhiên hoặc khoa học viễn tưởng (hơi thở nguyên tử/nhiệt năng, phóng điện sinh học, trọng lực, kiếm khí), **bắt buộc phải hợp thức hóa bằng 3 cơ chế vật lý**:
     - *Cơ chế Nạp & Dấu hiệu Sinh học (`Biomechanical Telegraph`):* Trước khi phát năng lượng phải có quá trình tích tụ hợp lý (lồng ngực phồng lớn hút khí, các gai lưng/mạch năng lượng sáng dần từ đuôi lên cổ, không khí xung quanh bị nung nóng biến dạng quang học).
     - *Phản lực Newton & Tương tác Môi trường (`Newtonian Recoil & Element Coupling`):* Phóng một luồng xung kích về phía trước thì hai chân sau phải bị đẩy trượt lùi trên mặt đất/đáy biển; luồng nhiệt bắn xuống biển phải làm nước biển sôi sục và bốc hơi thành sương mù dày đặc tức thì.
     - *Tiêu hao Sinh lực (`Metabolic Cost & Cooldown`):* Sau khi tung đòn đặc biệt, cơ thể phải chịu tải (thở dốc, bốc khói nhiệt từ miệng/khe giáp, giảm tốc độ trong nhịp kế tiếp), không bao giờ tung chiêu vô hạn.

---

### 2.3. CHẾ ĐỘ 2: Khi User giao Chủ đề và cho phép Đạo diễn Tự Đánh giá Thời lượng Hợp lý (`1 phút -> 60+ phút`)

Khi Nhà sản xuất nói: *"Tôi có ý tưởng này, bạn tự phân tích và đưa ra thời lượng hợp lý nhất — nếu ý tưởng hay và chi tiết thì dài chục phút hay cả tiếng đều được"*, Đạo diễn Top 0.1% không chọn bừa một con số mà chấm **Chỉ số Độ Phức Tạp Tự Sự (`Narrative Complexity Index — NCI`, thang 5–25 điểm)** trên 5 trục:

1. **Trục 1 — Quy mô Nhân vật & Hệ sinh thái (`Cast & Ecosystem Scale` | 1–5 điểm):**
   - 1đ: 1–2 nhân vật đơn lẻ.
   - 3đ: 2 nhân vật chính + bầy đàn/quần chúng hoặc con non cần bảo vệ.
   - 5đ: Hệ sinh thái đa phe phái (3–5 loài/nhóm nhân vật có mục tiêu chồng chéo).
2. **Trục 2 — Chiều sâu Xung đột & Động cơ (`Conflict & Emotional Stakes` | 1–5 điểm):**
   - 1đ: Đụng độ tình cờ.
   - 3đ: Sinh tồn (bảo vệ ổ trứng/con non, tranh giành nguồn sống cuối cùng trong mùa hạn/núi lửa).
   - 5đ: Bi kịch/Sử thi nhiều giai đoạn (mối thù truyền kiếp, mất mát đầu phim -> rèn luyện/thích nghi -> phục thù).
3. **Trục 3 — Độ rộng Bản đồ & Biến đổi Môi trường (`World & Biome Progression` | 1–5 điểm):**
   - 1đ: 1 căn phòng / 1 vũng nước.
   - 3đ: 3–5 tiểu địa hình liên thông (Suối -> Rừng -> Đầm lầy -> Vách đá -> Vực thác).
   - 5đ: Hành trình xuyên nhiều vùng khí hậu/thời gian (Ngày -> Hoàng hôn -> Bão đêm -> Bình minh lửa núi lửa).
4. **Trục 4 — Kho vũ khí Chiến thuật & Bước ngoặt (`Tactical Arsenal & Reversals` | 1–5 điểm):**
   - Số lượng đòn đánh, bẫy địa hình và bước ngoặt "NHƯNG / VÌ VẬY" không trùng lặp.
5. **Trục 5 — Nhịp thở Điện ảnh & Chiều sâu Khoa học/Tâm lý (`Atmospheric Pacing & Lore` | 1–5 điểm):**
   - Có cần phần mở đầu rình mò căng thẳng (như 10 phút đầu cảnh T-Rex phá rào trong *Jurassic Park*), khoảng lặng băng bó vết thương giữa 2 hiệp đấu, và phần kết lắng đọng không?

#### Khung Đề xuất 4 Cấp độ Thời lượng của Đạo diễn (`Director's 4 Runtime Tiers`):
Sau khi phân tích, Đạo diễn luôn trình bày cho User bảng lựa chọn chiến lược:
- **Gói 1 — `Short / Teaser (60s – 120s | 18–30 Shots)`:** Trích xuất đúng 1 cao trào duy nhất (Climax Clash). Nhịp dồn dập, phù hợp TikTok/Shorts/Reels.
- **Gói 2 — `Theatrical Set-Piece (5 Phút / 300s | 72–80 Shots)`:** Trận đại chiến 5 Hồi – 5 Đấu trường hoàn chỉnh từ lúc phát hiện nhau đến đòn kết liễu. Chuẩn trích đoạn đỉnh cao YouTube (*King Kong vs V-Rexes*, *Rexy vs Indominus*).
- **Gói 3 — `Extended Short Film / Mini-Movie (12 – 15 Phút / 720s–900s | 180–220 Shots)`:** Mở rộng thành câu chuyện 3 Chương hoàn chỉnh:
  - *Chương 1 (3 phút):* Thế giới quan, cuộc săn mồi thường nhật, dấu hiệu kẻ xâm lược bí ẩn (xác con mồi lớn, dấu chân khổng lồ), sự căng thẳng tích tụ trước cơn bão.
  - *Chương 2 (4 phút):* Cuộc chạm trán lần 1 lúc hoàng hôn -> Một bên bị thương nặng phải rút lui vào rừng sâu trong đêm mưa -> Sự rình rập tâm lý trong bóng tối.
  - *Chương 3 (6–8 phút):* Trận quyết chiến sinh tử tại Hẻm núi Lửa / Vực Thác với sự tham gia của hiểm họa tự nhiên (cháy rừng, sạt lở đá) và kết cục bi tráng.
- **Gói 4 — `Feature / Anthology Episode (30 – 60 Phút / 1800s–3600s | 450–900 Shots)`:** Cấu trúc Phim Điện ảnh 8 Sequences (Chuẩn Pixar / Hollywood Feature):
  - Có tuyến truyện chính (A-Plot: Hành trình sinh tồn và bảo vệ lãnh thổ/con non của nhân vật chính) + tuyến truyện đối trọng (B-Plot: Sự trỗi dậy và tàn phá của kẻ săn mồi ngoại lai) + 3 trận giao tranh lớn ở Hồi 1, Midpoint và Hồi 3, mỗi trận mang một ý nghĩa tâm lý và chiến thuật hoàn toàn khác nhau.

---

## PHẦN 3: GIAO THỨC MÁY TRẠNG THÁI HỮU HẠN (FSM CONTINUITY PROTOCOL) — CHỐNG AI ĐỌC NHẦM 100%

Để AI (cả trình biên dịch Prompt lẫn mô hình Veo 3.1 / Nano Banana Pro) **không bao giờ hiểu sai cảnh hoặc vẽ nhảy tư thế**, mỗi Shot trong `project_manifest.json` bắt buộc phải tuân thủ **Phương trình Trạng thái Liên tục (`FSM State Continuity Equation`)**:

$$\boxed{\text{ExitState}(\text{Shot}_{k-1}) \equiv \text{EntryState}(\text{Shot}_{k})}$$

### 3.1. 6 Trường Dữ liệu Đạo diễn Bắt buộc trên mỗi Shot (`Mandatory Director Fields`)

| Trường trong `shot` | Ý nghĩa Điện ảnh & Vật lý | Ví dụ Chuẩn 0.1% |
| :--- | :--- | :--- |
| **`entry_state`** | **Trạng thái Vật lý Đầu Shot (`t = 0.0s`):** Tư thế cơ thể (`standing`, `crouched`, `pinned_on_flank`), vị trí Trái/Phải, khoảng cách, bùn/máu trên người. **Phải khớp 100% với `exit_state` của shot ngay trước đó.** | `"Rex (trái) đang ghì chặt hàm vào cổ Vasto; Vasto (phải) nằm nghiêng sườn phải dưới lớp bùn sâu 40cm, hai chân sau co đạp."` |
| **`causal_link`** | **Liên từ Nhân - Quả (`THEREFORE` / `BUT`):** Cấm dùng *"Và rồi"*. Giải thích vì sao hành động này tất yếu xảy ra từ `entry_state`. | `"BUT: Vasto dùng móng vuốt chân sau móc ngược vào bụng Rex để phá thế khóa hàm."` |
| **`action` + `timeline_phases`** | **Quỹ đạo Cơ sinh học (`t = 0.0s -> 8.0s`):** Chia 3 pha rõ ràng (`0.0-2.5s` Phát lực -> `2.5-5.5s` Va chạm/Tác động -> `5.5-8.0s` Hệ quả). Mỗi chủ thể trong khung hình đều phải có động từ chủ động/phản ứng riêng. | Pha 1: Vasto co chân đạp -> Pha 2: Móng vuốt rạch bụng khiến Rex nhả hàm lùi lại -> Pha 3: Vasto lăn vòng chống chân đứng dậy. |
| **`exit_state`** | **Trạng thái Vật lý Cuối Shot (`t = 8.0s`):** Kết quả vị trí và tư thế sau khi hành động hoàn tất. Dùng để khóa `last_frame_prompt` và truyền thẳng sang `entry_state` của shot kế tiếp. | `"Rex lùi về bên trái 3m, cúi thấp đầu gầm nhẹ; Vasto bên phải vừa chống hai chân đứng dậy, bùn đặc phủ kín sườn phải."` |
| **`arena_stage`** | **Tiểu Đấu trường & Hiểm họa Địa hình:** Đảm bảo bối cảnh biến đổi theo tiến trình trận đánh. | `"ARENA_3_BASALT_MUD_PIT"` |
| **`character_states`** | **Sổ cái Thương tích & Thể lực Lũy tiến (`Progressive Damage Ledger`):** Bùn, nước, vết cào, máu, hơi thở khói phải **tích lũy tăng dần** từ Hồi 1 đến Hồi 5, không bao giờ tự sạch đi. | `{"CHAR_REX": "soaked hide, mud-splattered legs, fresh claw scratch on left shoulder, heavy steam breath"}` |

### 3.2. Quy tắc "Không Nhảy Cóc Tư Thế" (`Zero Posture Teleportation Rule`)
Nếu ở cuối Shot $k$, Nhân vật X đang ở tư thế **Ngã / Nằm / Quỳ / Bị đè (`prone`, `pinned`, `collapsed`, `on its flank`, `on the ground`, `hanging`)**:
- Thì ở đầu Shot $k+1$ (nếu cùng cảnh và có mặt Nhân vật X), `entry_state` / `start_action` **BẮT BUỘC** phải giữ Nhân vật X ở đúng tư thế đang nằm/bị đè đó!
- Muốn Nhân vật X đứng dậy tấn công ở Shot $k+2$, thì chính nội dung của Shot $k+1$ phải là **Cảnh Phá vây / Chống chân đứng dậy (`Recovery / Kip-up / Counter-Push`)**.
- Bộ công cụ `lint-prompts` tự động quét lỗi này qua mã cảnh báo `FSM_POSTURE_DISCONTINUITY`.

---

## PHẦN 4: NGỮ PHÁP MÁY QUAY & DỰNG PHIM HÀNH ĐỘNG TOP 0.1%

### 4.1. Định luật Chọn Ống kính theo Lực Va Chạm (`Lens-to-Impact Matching`)
Tại sao nhiều cảnh cắn/đâm trong video AI trông như "lướt qua người nhau"?
- **Lỗi:** Dùng ống kính góc rộng (`24mm–28mm Wide Shot`) cho cảnh răng cắn ngập vào cổ hoặc lưỡi kiếm đâm qua giáp. Trong khung hình rộng, chiếc răng chỉ chiếm `< 3%` diện tích ảnh -> AI không đủ độ phân giải pixel để vẽ biến dạng da thịt!
- **Chuẩn 0.1% (Spielberg / Gareth Evans):**
  - **Pha Lao vào & Quật ngã (`Full-Body Trajectory & Knockdown`):** Dùng ống kính `24mm–35mm Anamorphic Wide / Medium-Wide`, đặt máy thấp ngang tầm mắt con người (`1.2m Ground-Level`) có tiền cảnh mờ (`Dirty Frame: cành dương xỉ, tảng đá, tia nước bắn`) để tôn kích thước khổng lồ và quỹ đạo văng.
  - **Pha Cắn ngập răng / Vuốt cào / Đòn chí mạng (`Visceral Flesh Compression`):** Bắt buộc cắt vào ống kính **`85mm–100mm Macro Close-Up`** trong `2.5s–3.5s` sao cho bộ hàm/móng vuốt và vùng da thịt bị ép lún chiếm **`> 40%` diện tích khung hình**.

### 4.2. Định luật Tâm điểm Ánh nhìn của George Miller (`Crosshair Framing & Eye-Trace`)
Trong *Mad Max: Fury Road* (giành giải Oscar Dựng phim xuất sắc nhất), George Miller đặt **điểm va chạm chính xác tại giao điểm trung tâm khung hình (hoặc trục 1/3 cố định)** giữa 2 cú cắt liên tiếp:
- Khi cắt từ `Shot A (Wide: Rex lao tới từ trái sang phải)` sang `Shot B (85mm Close-Up: Hàm Rex ngoạm cổ Vasto)`, vị trí cổ Vasto trên màn hình ở cuối Shot A phải nằm cùng tọa độ màn hình với vị trí cú ngoạm ở đầu Shot B -> Mắt khán giả không mất 0.2 giây đi tìm chủ thể, tạo cảm giác cú đớp liền mạch 100%.

### 4.3. Định luật Chậm Trễ Cơ Học 3 Nhịp (`3-Beat Mass Delay Physics`)
Sinh vật nặng 8–10 tấn (hoặc chiến binh mặc giáp nặng) không bao giờ di chuyển như bóng bay:
1. **Nhịp 1 — Dồn trọng lượng (`Weight Shift`):** Bàn chân đạp lún bùn/đá, cơ đùi căng phồng trước khi thân mình nhúc nhích.
2. **Nhịp 2 — Va chạm & Trễ Sóng Xung Kích (`Impact + 0.15s Shockwave Delay`):** Đầu/hàm chạm mục tiêu tại $t_0$ -> $0.15\text{s}$ sau làn sóng chấn động mới truyền qua lớp mỡ/cơ bắp làm văng nước mưa và bùn khỏi lưng đối thủ.
3. **Nhịp 3 — Dư chấn Môi trường (`Environmental Aftermath`):** Cây gãy, đá lở, sóng nước dội vào ống kính máy quay, rung giật máy tự nhiên (`organic handheld camera rattle on impact`).

---

## PHẦN 5: QUY TRÌNH KIỂM DUYỆT KỊCH BẢN TRƯỚC KHI BẤM RENDER (`THE 0.1% PRE-FLIGHT GATE`)

Trước khi chạy `flow-generate` tốn bất kỳ credit nào, Kịch bản Đạo diễn (`project_manifest.json`) phải vượt qua **6 Cổng Kiểm Duyệt Bắt Buộc**:

1. **Cổng 1 — Đủ Số lượng Shot Duy nhất (`Shot Budget Gate`):**
   - Kiểm tra: `len(shots) >= ceil(target_duration_sec / avg_shot_sec)`.
   - Nếu mục tiêu là 5 phút (`300s`), phải có đủ `70–78` shots có nội dung độc lập (hoặc nếu đạo diễn chọn nhịp cắt 4.5s thì tối thiểu `65` shots). Tuyệt đối không dùng 14–22 shots rồi ép hậu kỳ lặp/chia nhỏ để đủ 5 phút.
2. **Cổng 2 — Liên kết Nhân Quả `THEREFORE / BUT` (`Causality Gate`):**
   - Đọc nối tiếp toàn bộ `shot_01` -> `shot_N`: mỗi shot phải có `causal_link` bắt đầu bằng `THEREFORE` hoặc `BUT`.
3. **Cổng 3 — Khớp Khóa Trạng thái Đầu/Cuối (`FSM Continuity Gate`):**
   - Mọi cặp shot cùng cảnh phải thỏa mãn `shot[k-1].exit_state == shot[k].entry_state`. Không có nhân vật nào tự nhiên đổi từ nằm sang đứng hoặc nhảy từ trái sang phải mà không có shot chuyển tiếp.
4. **Cổng 4 — Tiến hóa Đấu trường & Thương tích Lũy tiến (`Arena & Damage Progression Gate`):**
   - Cứ mỗi `60–75 giây` (`12–16 shots`) phải chuyển sang `arena_stage` mới và cập nhật `character_states` (tăng mức độ ướt, bùn, vết xước, nhịp thở).
5. **Cổng 5 — Cân bằng Góc máy Đa chiều (`Camera Coverage Gate`):**
   - Không quá 2 shot liên tiếp dùng cùng một cỡ cảnh phẳng (`flat medium/wide two-shot`). Phải đan xen: `Wide Geography` -> `OTS Depth` -> `85mm Macro Impact` -> `1.2m Ground-Level POV` -> `Reaction ECU`.
6. **Cổng 6 — Kiểm định Tự động bằng Lệnh (`Automated Linter Gate`):**
   - Chạy `python scripts/studio_helper.py lint-prompts --project <slug> --strict` đạt **0 Error, 0 FSM Discontinuity, 0 Underbudgeted Shot Warning**.

