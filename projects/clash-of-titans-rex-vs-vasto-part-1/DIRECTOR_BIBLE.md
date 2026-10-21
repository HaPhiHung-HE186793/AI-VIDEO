# HỒ SƠ ĐẠO DIỄN & BIÊN ĐẠO CHIẾN ĐẤU (DIRECTOR BIBLE V2 — TOP 0.1% STANDARD)
## Dự án: `Clash of Titans: Rex vs. Vasto` (Bản Làm Lại Hoàn Toàn Từ Đầu — 5 Phút / 300 Giây)

> **Nguyên tắc Sản xuất Bắt buộc:**
> 1. **Làm mới 100% từ Gốc Nội dung (`Fresh Ground-Up Rebuild`):** Xóa bỏ hoàn toàn mọi clip cũ và keyframe cũ. Không tái sử dụng, không lặp lại hay cắt ghép chắp vá bất kỳ đoạn video cũ nào.
> 2. **Định luật 1:1 Ngân sách Shot (`60 Unique Shots = 300s`):** 60 shot kịch bản độc lập (`shot_01` .. `shot_60`), mỗi shot là 1 biến cố cơ sinh học duy nhất (`~5.0s` sau dựng từ clip 8.0s), chia làm **5 Hồi × 12 Shots/Hồi (15 Hiệp giao tranh)**.
> 3. **Bản đồ Địa lý Liền kề (`Contiguous 5-Zone Coastal Ecosystem`):** Toàn bộ trận chiến diễn ra trên một dải địa hình ven biển liền mạch:
>    `Vùng 1: Đất liền Bìa rừng` $\leftrightarrow$ `Vùng 2: Đầm lầy bùn ven bờ` $\leftrightarrow$ `Vùng 3: Bãi cát & Ghềnh đá sát sóng` $\leftrightarrow$ `Vùng 4: Vùng nước biển ngập ngực sóng vỗ` $\leftrightarrow$ `Vùng 5: Mỏm đá gành biển sâu`.
> 4. **Cầu nối Dịch chuyển Vật lý 3 Shot (`Mandatory 3-Shot Physical Transition Bridge`):** Mọi sự dịch chuyển giữa các vùng đều do lực tác động vật lý thật (đánh lùi, vừa chạy vừa đánh, quăng xuống biển rồi con trên bờ nhảy xuống biển ngay chỗ con kia đứng để đánh tiếp).
> 5. **Giao thức Máy Trạng thái Hữu hạn (`FSM Continuity`):** $\text{ExitState}(\text{Shot}_{k-1}) \equiv \text{EntryState}(\text{Shot}_{k})$.

---

## 1. BẢN ĐỒ ĐỊA LÝ LIỀN KỀ & CƠ SINH HỌC THEO ĐỊA HÌNH (`CONTIGUOUS MAP & TERRAIN BIOMECHANICS`)

```mermaid
flowchart LR
    Z1["VÙNG 1 (0:00-1:00)<br/>Đất Liền Bìa Rừng<br/>(Thăm dò, vật ngã, đánh lùi)"] -->|Shots 10-12: Vừa chạy vừa đánh<br/>trượt xuống dốc bùn| Z2["VÙNG 2 (1:00-2:00)<br/>Đầm Lầy Bùn Ven Bờ<br/>(Chân lún bùn 40cm, Vasto lách sườn)"]
    Z2 -->|Shots 22-24: Khóa hàm đẩy lùi<br/>văng ra bãi đá ven biển| Z3["VÙNG 3 (2:00-3:00)<br/>Bờ Cát & Ghềnh Đá Sát Biển<br/>(Va đập đá tảng, quật ngã)"]
    Z3 -->|Shots 34-36: Quăng xuống biển -> Đứng dậy<br/>-> Nhảy từ bờ xuống biển đấu tiếp| Z4["VÙNG 4 (3:00-4:00)<br/>Nước Biển Ngập Ngực Sóng Vỗ<br/>(Sức cản nước, dìm nước & húc ngược)"]
    Z4 -->|Shots 46-48: Vừa vật nhau<br/>vừa dạt lên gành đá| Z5["VÙNG 5 (4:00-5:00)<br/>Mỏm Đá Gành Biển Sâu<br/>(Đòn bẩy quật rơi xuống biển sâu)"]
```

| Mã Vùng (`arena_stage`) | Địa hình & Quang học | Cơ sinh học & Tương tác Vật lý đặc trưng | Trạng thái Cơ thể (`character_states`) |
| :--- | :--- | :--- | :--- |
| **`ZONE_1_DRY_CLEARING`** (`shot_01`..`shot_12`) | Đất liền bìa rừng ven biển; nền đất cứng phủ đá cuội; phía xa bên phải thấy rõ đầm lầy và biển. | Bước chạy nhanh, bụi đất bốc lên; lượn vòng thăm dò, khóa cổ vật ngã đầu tiên, dùng vai đánh lùi nhau ra để đo sức. | `state_1_dry_probing`: Da khô ráo phủ bụi đất rừng, thể lực sung mãn 100%. |
| **`ZONE_2_MUDDY_MARSH`** (`shot_13`..`shot_24`) | Đầm lầy bùn đen ven bờ nằm sát chân dốc bìa rừng; bùn đặc sâu 40cm, gốc cây ngập mặn. | Chân 9 tấn của Rex lún sâu vào bùn làm giảm tốc độ xoay hông; Vasto nhẹ hơn lách sườn cào vai Rex; bùn đen bắn đặc quánh. | `state_2_mud_splattered`: Chân ngập bùn đen, bùn bắn lên sườn và hàm, vết cào mới trên vai. |
| **`ZONE_3_ROCKY_SHORELINE`** (`shot_25`..`shot_36`) | Bãi cát ướt và ghềnh đá bazan sát mép sóng biển; gờ bờ đá cao 2m nhìn xuống vùng nước biển sâu. | Bàn chân trượt trên đá ướt và cát; dùng sức nặng húc vỡ đá风 hóa; quăng đối thủ qua gờ đá rơi xuống biển và nhảy theo. | `state_3_shoreline_battered`: Bùn bị sóng liếm loang lổ, cát ướt bám sườn, vết cắn rỉ máu ở cổ. |
| **`ZONE_4_BREAKING_SEA_SURF`** (`shot_37`..`shot_48`) | Vùng nước biển ven bờ ngập ngang đùi/ngực; sóng bạc đầu đánh mạnh vào sườn hai titan. | Lực cản nước biển (`hydrodynamic drag`) làm bước di chuyển nặng nề; sóng xô lệch trụ; đè dìm đầu xuống nước biển sủi bọt khí. | `state_4_sea_drenched_bleeding`: Toàn thân ướt sũng nước biển bóng loáng, bọt sóng trắng xóa trộn máu loang. |
| **`ZONE_5_COASTAL_REEF_SPIT`** (`shot_49`..`shot_60`) | Mỏm đá gành biển nhô ra vùng biển sâu; mặt đá trơn trượt, sóng biển đập tung hai bên. | Cả hai kiệt sức, chân run trên đá trơn; dùng khóa hàm làm đòn bẩy + đà lao + độ dốc mỏm đá để quật đối thủ rơi xuống biển sâu. | `state_5_exhausted_apex`: Kiệt sức, ngực phập phồng thở khói nhiệt, vết thương chiến đấu in hằn. |

---

## 2. PHÂN RÃ CHI TIẾT 5 HỒI — 15 HIỆP GIAO TRANH — 60 SHOTS DUY NHẤT

### HỒI I: ĐẤT LIỀN BÌA RỪNG VEN BIỂN — CHẠM MẶT, THĂM DÒ, VẬT NGÃ & CHẠY XUỐNG ĐẦM LẦY (`0:00 – 1:00` | `shot_01` .. `shot_12`)
- **Hiệp 1 (`beat_01` | `shot_01`..`shot_04` | `0:00–0:20`): Chạm mặt trên đất liền & Lượn vòng thăm dò**
  - `shot_01`: Rex bước đi trên nền đất cứng bìa rừng ven biển (hậu cảnh xa thấy đầm lầy và sóng biển), khựng lại khi nghe tiếng bước chân nặng nề từ phía phải.
  - `shot_02`: Vasto bước ra từ rặng cây phía phải trên nền đất khô, cúi thấp đầu gầm thăm dò, móng chân cào tung bụi đất khô.
  - `shot_03`: Cả hai chưa lao vào ngay mà bước lượn vòng giữ khoảng cách 8m trên nền đất cứng (`circling & probing`), gầm gừ đo phản xạ và tìm sơ hở của nhau.
  - `shot_04`: Vasto tung đòn nhử đầu tiên: lao nhanh táp vào khoảng không trước mặt làm Rex nghiêng đầu né, hai bộ hàm sượt qua nhau cách vài phân.
- **Hiệp 2 (`beat_02` | `shot_05`..`shot_08` | `0:20–0:40`): Va chạm trực diện, vật ngã lần 1 & Đánh lùi tách ra**
  - `shot_05`: Rex phản công đâm sầm ngực và vai vào sườn Vasto trên nền đất cứng, làm bụi đất bốc mù mịt.
  - `shot_06`: Cận cảnh 85mm: Rex dùng hàm tì vào bả vai Vasto và quật mạnh làm Vasto mất trụ ngã khuỵu một bên gối xuống nền đất đá cuội (`first takedown`).
  - `shot_07`: Đang khuỵu gối trên đất, Vasto lập tức xoay hông quất đuôi vào đùi Rex và dùng đầu húc ngược vào ngực Rex để đẩy lùi Rex ra xa 4m (`push-back to create space`).
  - `shot_08`: Vasto bật dậy trên nền đất cứng; cả hai lùi lại vài bước thở mạnh, rũ bụi đất, quan sát đánh giá sức mạnh thật sự của đối phương.
- **Hiệp 3 (`beat_03` | `shot_09`..`shot_12` | `0:40–1:00`): Cầu nối Dịch chuyển Vật lý từ Đất liền xuống Đầm lầy ven bờ**
  - `shot_09`: Rex dồn toàn bộ khối lượng 9 tấn lao tới ép sát, dùng hộp sọ rộng húc liên tiếp làm Vasto trượt chân lùi dần về phía triền dốc dẫn xuống đầm lầy.
  - `shot_10 (Bridge 1/3)`: Vasto nhận thấy trên nền đất cứng mình bất lợi về sức nặng nên vừa táp trả vừa chủ động xoay người chạy rút dọc theo triền dốc xuống Đầm lầy bùn ven bờ ngay bên cạnh.
  - `shot_11 (Bridge 2/3)`: Vasto lao xuống Đầm lầy bùn sâu 35cm làm bùn đen bắn tung tóe, lập tức xoay người lại thủ thế giữa đầm lầy chờ sẵn.
  - `shot_12 (Bridge 3/3)`: Rex không kịp hãm đà, phóng thẳng từ triền đất liền xuống Đầm lầy bùn ngay trước mặt Vasto, hai chân sau lún sâu 40cm vào lớp bùn đặc!

---

### HỒI II: ĐẦM LẦY BÙN VEN BỜ — MẤT ĐỘ BÁM, ĐÒN LÁCH SƯỜN & ĐẨY VĂNG RA BỜ BIỂN (`1:00 – 2:00` | `shot_13` .. `shot_24`)
- **Hiệp 4 (`beat_04` | `shot_13`..`shot_16` | `1:00–1:20`): Chân Rex lún bùn sâu & Vasto lách sườn phản kích**
  - `shot_13`: Cận cảnh 50mm dưới thấp: Bàn chân 9 tấn của Rex bị lún sâu 40cm trong lớp bùn đen đặc quánh của đầm lầy, mỗi nhịp rút chân đều nặng nề.
  - `shot_14`: Lợi dụng lúc Rex rút chân chậm trong bùn, Vasto lướt nhanh qua bên sườn phải của Rex, tung cú đớp sắc lẹm.
  - `shot_15`: Cận cảnh 85mm Macro: Hàm răng dẹp như lưỡi dao của Vasto cắn sượt qua bả vai phải của Rex, để lại vết rách rỉ máu trộn lẫn bùn đen.
  - `shot_16`: Rex gầm lên đau đớn, xoay cổ táp trả nhưng chân phải trượt trong bùn làm Rex chao đảo suýt ngã.
- **Hiệp 5 (`beat_05` | `shot_17`..`shot_20` | `1:20–1:40`): Quần thảo trong bùn lầy & Bước ngoặt 1 (Vasto ép thế)**
  - `shot_17`: Vasto thừa thắng xông lên trong đầm lầy, dùng vai húc ngang vào hông Rex khi chân Rex đang lún bùn.
  - `shot_18`: Rex bị húc ngã nghiêng sườn trái xuống đầm lầy bùn đen, tạo một làn sóng bùn đặc văng cao 3m.
  - `shot_19`: Đang nằm nghiêng trong bùn, Rex ngẩng đầu há hàm đớp chặn ngay vào cẳng chân trước/ức của Vasto khi Vasto định lao vào giẫm bồi.
  - `shot_20`: Từ tư thế nằm nghiêng trong bùn, Rex dùng lực cổ quật ngang làm Vasto trượt chân ngã sập xuống bùn cạnh đó, giúp Rex có khoảng trống chống hai chân sau đứng dậy.
- **Hiệp 6 (`beat_06` | `shot_21`..`shot_24` | `1:40–2:00`): Cầu nối Dịch chuyển Vật lý từ Đầm lầy ra Bãi đá Bờ biển**
  - `shot_21`: Cả hai cùng đứng dậy giữa đầm lầy trong bộ dạng bê bết bùn đen; Rex hạ thấp trọng tâm khóa chặt hàm vào gốc cổ Vasto.
  - `shot_22 (Bridge 1/3)`: Khóa chặt cổ Vasto làm đòn bẩy, Rex gồng cơ đùi đẩy lùi Vasto trượt băng qua rặng rễ cây ngập mặn ở rìa đầm lầy hướng thẳng ra phía bờ biển.
  - `shot_23 (Bridge 2/3)`: Vasto bị đẩy bật qua ranh giới đầm lầy, trượt chân văng ra Bãi cát ướt và Ghềnh đá bazan sát mép sóng biển (sóng biển tràn vào bàn chân rửa trôi một phần bùn).
  - `shot_24 (Bridge 3/3)`: Rex bước hùng hổ từ rìa đầm lầy ra Bãi đá bờ biển ngay trước mặt Vasto, gió biển thổi bọt sóng bay qua hai cơ thể lấm lem bùn máu.

---

### HỒI III: BỜ CÁT & GHỀNH ĐÁ SÁT MÉP BIỂN — VA ĐẬP ĐÁ TẢNG, QUĂNG XUỐNG BIỂN & NHẢY THEO (`2:00 – 3:00` | `shot_25` .. `shot_36`)
- **Hiệp 7 (`beat_07` | `shot_25`..`shot_28` | `2:00–2:20`): Giao chiến trên Ghềnh đá ven biển & Đập vỡ đá tảng**
  - `shot_25`: Trên bãi cát và ghềnh đá sát mép biển (sóng đánh tung bọt ngay bên phải khung hình), hai titan lao vào đọ sức trực diện.
  - `shot_26`: Vasto quất đuôi làm vỡ tung một mỏm đá phong hóa ven bờ, mảnh đá và cát ướt văng rào rạt vào mặt Rex.
  - `shot_27`: Rex che mắt chịu đòn rồi lao tới dùng đỉnh hộp sọ húc thẳng vào ngực Vasto (`Cranial Battering Ram`).
  - `shot_28`: Cú húc làm Vasto lùi sát ra gờ đá bờ biển cao 2m nhìn xuống vùng nước biển sóng vỗ bên dưới, những viên đá ở mép bờ lăn rơi xuống biển.
- **Hiệp 8 (`beat_08` | `shot_29`..`shot_32` | `2:20–2:40`): Giằng co sát mép bờ biển & Đòn khóa hàm đòn bẩy**
  - `shot_29`: Không muốn bị đẩy xuống biển, Vasto liều mạng lao ngược vào trong bờ, dùng hàm cắn vào bên má trái của Rex.
  - `shot_30`: Cận cảnh 85mm: Hai bộ hàm khóa chặt vào nhau trên gờ đá ven biển, nước bọt và máu nhỏ xuống mặt đá ướt sóng biển.
  - `shot_31`: Rex dùng cổ vặn mạnh phá khóa hàm, rồi nhân lúc Vasto đang lao theo đà về phía trước, Rex luồn đầu ngoạm chặt vào bả vai và gốc cổ Vasto.
  - `shot_32`: Bàn chân trái của Rex đạp cứng vào một tảng đá bazan làm điểm tựa đòn bẩy, cơ cổ và cơ lưng 9 tấn gồng cứng chuẩn bị quăng đối thủ theo đà dốc bờ biển.
- **Hiệp 9 (`beat_09` | `shot_33`..`shot_36` | `2:40–3:00`): Cầu nối 3 Shot Kinh điển — Quăng Vasto xuống Biển & Rex Nhảy xuống Biển Đấu Tiếp**
  - `shot_33`: Rex xoay hông 90 độ trên gờ đá bờ biển, mượn chính đà lao của Vasto kết hợp độ dốc bờ đá để quật Vasto bay qua mép bờ đá hướng ra biển.
  - `shot_34 (Bridge 1/3 — Quăng xuống biển)`: Vasto bị quăng văng khỏi gờ đá bờ biển, rơi ầm xuống vùng nước biển sâu ngang ngực cách bờ 6m, làm bùng lên một cột nước biển trắng xóa cao 8m!
  - `shot_35 (Bridge 2/3 — Đứng dậy dưới biển)`: Giữa vùng nước biển sủi bọt trắng xóa, Vasto đạp mạnh hai chân sau xuống đáy biển tìm lại thăng bằng, đứng bật dậy ngay tại chỗ vừa bị ném xuống, rũ nước biển mặn khỏi mặt và gầm vang thách thức lên bờ.
  - `shot_36 (Bridge 3/3 — Nhảy xuống biển đấu tiếp)`: Từ trên gờ đá bờ biển cao 2m, Rex không hề chần chừ, lấy đà hai bước rồi **phóng nhảy thẳng xuống vùng nước biển ngay trước mặt nơi Vasto đang đứng**, tạo làn sóng xung kích khổng lồ xô vào ngực Vasto!

---

### HỒI IV: THỦY CHIẾN GIỮA SÓNG BIỂN NGẬP NGỰC — SỨC CẢN NƯỚC, DÌM NƯỚC & LẬT KÈO (`3:00 – 4:00` | `shot_37` .. `shot_48`)
- **Hiệp 10 (`beat_10` | `shot_37`..`shot_40` | `3:00–3:20`): Thủy chiến giữa Sóng biển & Lực cản Thủy động lực học**
  - `shot_37`: Cả hai titan đứng đối diện nhau trong vùng nước biển ngập ngang đùi và ngực; một con sóng bạc đầu đánh ầm vào sườn cả hai làm bọt biển tung mù mịt.
  - `shot_38`: Hai con lao vào nhau giữa biển; sức cản của khối nước biển (`hydrodynamic drag`) làm bước chân nặng nề và tạo ra hai luồng sóng cuộn ngược dữ dội.
  - `shot_39`: Rex và Vasto vật nhau giữa sóng biển, hai cơ thể ướt sũng bóng loáng va đập làm nước biển đỏ ngầu vết máu loang quanh ngực.
  - `shot_40`: Một con sóng lớn ập tới từ phía ngoài khơi kết hợp cú húc vai của Vasto làm chân trụ của Rex trượt trên nền cát đáy biển.
- **Hiệp 11 (`beat_11` | `shot_41`..`shot_44` | `3:20–3:40`): Bước ngoặt 3 — Vasto đè dìm đầu Rex dưới sóng biển & Cú húc ngược sinh tử**
  - `shot_41`: Rex khuỵu hai gối xuống vùng nước biển sâu; Vasto lập tức chồm lên từ phía phải, dùng hàm và ức đè chặt cổ Rex dìm xuống mặt nước biển đang sủi bọt!
  - `shot_42`: Cận cảnh 85mm kịch tính: Nửa đầu và lỗ mũi của Rex bị ép ngập dưới mặt nước biển sủi bọt trắng xóa, bong bóng khí phun ra dữ dội khi Rex bị ngạt thở dưới sức nặng của Vasto.
  - `shot_43`: Khoảnh khắc sinh tử dưới nước: Đôi mắt vàng của Rex mở trừng dưới làn nước biển; hai bàn chân sau của Rex đạp ngập xuống nền đá ngầm đáy biển lấy điểm tựa phản lực.
  - `shot_44`: Từ dưới mặt nước biển, Rex bùng nổ sức mạnh đạp thẳng hai chân sau, dùng đỉnh hộp sọ húc ngược từ dưới nước lên trúng hàm dưới của Vasto, phá tung mặt nước biển và hất Vasto ngửa cổ ra sau!
- **Hiệp 12 (`beat_12` | `shot_45`..`shot_48` | `3:40–4:00`): Cầu nối Dịch chuyển Vật lý từ Dưới biển lên Mỏm đá Gành biển**
  - `shot_45`: Vasto loạng choạng lùi lại giữa sóng biển vì cú húc ngược vào hàm; Rex ngoi lên thở hổn hển, phun nước biển mặn từ miệng và mũi.
  - `shot_46 (Bridge 1/3)`: Cả hai vừa khóa cổ vừa đẩy nhau băng qua vùng nước nông sát chân **Mỏm đá gành biển (`Coastal Reef Spit`)** nhô ra vùng biển sâu ngay kế bên.
  - `shot_47 (Bridge 2/3)`: Vasto đạp bọt sóng bước trèo lên mặt Mỏm đá gành biển ướt trơn để tìm lại địa hình cứng, quay lại gầm xuống mép nước.
  - `shot_48 (Bridge 3/3)`: Rex bước từ dưới sóng biển lên mặt Mỏm đá gành biển ngay đối diện Vasto; sóng biển lớn đập vào hai bên vách đá gành bắn bọt trắng xóa lên trời.

---

### HỒI V: MỎM ĐÁ GÀNH BIỂN SÂU — KIỆT SỨC, ĐÒN BẨY TẤT SÁT & BÁ CHỦ ĐỈNH CAO (`4:00 – 5:00` | `shot_49` .. `shot_60`)
- **Hiệp 13 (`beat_13` | `shot_49`..`shot_52` | `4:00–4:20`): Cuộc chiến Kiệt sức trên Mỏm đá Gành biển trơn trượt**
  - `shot_49`: Góc rộng IMAX trên Mỏm đá gành nhô ra biển sâu: Cả hai titan ướt đẫm nước biển, đầy vết thương, ngực phập phồng thở ra khói nhiệt đặc quánh giữa gió bão biển.
  - `shot_50`: Cả hai bước những bước nặng nề tiến vào nhau trên mặt đá gành trơn trượt, quật đuôi và tì vai trong trạng thái thể lực đã chạm đáy.
  - `shot_51`: Vasto tung đòn cào và táp cuối cùng vào bả vai trái của Rex; Rex không lùi mà nghiến răng chịu đòn để giữ vững hai chân trụ trên nền đá gành.
  - `shot_52`: Ngay khi đầu Vasto vừa chúi về phía trước sau cú táp, Rex hạ thấp cổ luồn xuống dưới hàm Vasto rồi ngoạm ngược lên khóa chặt lấy cổ họng và gáy của Vasto (`Apex Death-Clamp`).
- **Hiệp 14 (`beat_14` | `shot_53`..`shot_56` | `4:20–4:40`): Đòn Tất Sát Hợp Lý Vật Lý — Quật ngã khỏi Gành đá xuống Biển sâu**
  - `shot_53`: Cận cảnh 85mm Macro: Bộ hàm 9 tấn của Rex khóa chặt vào cổ Vasto, cơ hàm phồng căng, chân Vasto cào trượt trên mặt đá gành ướt nước biển.
  - `shot_54`: Rex dùng chân trái làm trục xoay, lợi dụng độ dốc nghiêng và trơn của mỏm đá gành biển để đẩy và xoay ngang toàn bộ cơ thể Vasto ra sát mép vực biển sâu.
  - `shot_55`: Đá vụn ở mép gành vỡ lở; Rex gồng hết sức bình sinh quật mạnh đầu sang phải, hất Vasto mất hoàn toàn điểm tựa trượt khỏi mép Mỏm đá gành biển!
  - `shot_56`: Khung hình rộng từ mép gành nhìn xuống: Cơ thể khổng lồ của Vasto rơi xuống vùng nước biển sâu sẫm màu bên dưới chân gành đá, tạo ra một vùng xoáy bọt biển khổng lồ.
- **Hiệp 15 (`beat_15` | `shot_57`..`shot_60` | `4:40–5:00`): Kẻ thua rút lui dưới biển & Tiếng gầm Bá chủ trên Gành đá**
  - `shot_57`: Dưới vùng nước biển sâu dưới chân gành đá, Vasto ngoi đầu lên giữa sóng dữ, kiệt sức và đau đớn, đành quay đầu lội/bơi rút lui dọc theo bờ biển mờ sương.
  - `shot_58`: Trên đỉnh Mỏm đá gành biển, Rex đứng thở dốc, nước biển và máu nhỏ giọt từ cằm xuống mặt đá, đôi mắt hổ phách nhìn theo kẻ bại trận đang rút lui dưới biển.
  - `shot_59`: Góc máy thấp 1.2m ngước lên: Rex bước một bước nặng nề lên điểm cao nhất của Mỏm đá gành biển, sóng biển đập vào vách đá phía sau tung bọt trắng xóa dưới ánh nắng bình minh xuyên qua mây bão.
  - `shot_60`: Đại cảnh IMAX Kết thúc: Rex vươn cao cổ, há rộng hàm tung tiếng gầm bá chủ vang dội khắp vùng bờ biển và đại dương, khép lại trận đại chiến 5 phút hoàn chỉnh.
