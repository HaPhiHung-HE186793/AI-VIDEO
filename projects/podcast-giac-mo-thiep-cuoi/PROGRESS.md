# Tiến độ: podcast-giac-mo-thiep-cuoi

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project podcast-giac-mo-thiep-cuoi "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project podcast-giac-mo-thiep-cuoi   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project podcast-giac-mo-thiep-cuoi       # kiểm tra máy + in bước tiếp theo
```

Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).

Máy mới (Windows / Ubuntu) hoặc thiếu rclone / `.env`: làm theo [docs/SYNC_SETUP.md](../../docs/SYNC_SETUP.md).

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `podcast-giac-mo-thiep-cuoi` — thư mục `projects/podcast-giac-mo-thiep-cuoi/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/69dec2a7-c3f5-4f28-b83b-5327bb8e2d5f
- **Ngôn ngữ / khung:** vi / 16:9; giọng dẫn `Charon`
- **Cập nhật lần cuối:** 2026-10-20T18:32:44 trên máy **user** (lệnh `storyboard`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 4. 🧑 Chờ người dùng duyệt storyboard

46 shot chưa có video. Storyboard chưa duyệt.

```powershell
python scripts/studio_helper.py storyboard --project podcast-giac-mo-thiep-cuoi
(người dùng xem output/storyboard.html)
python scripts/studio_helper.py storyboard-approve --project podcast-giac-mo-thiep-cuoi --by "<tên>"
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01a | b01_noon_break_hook | pending | - / 0 |  |  |
| 2 | shot_01b | b01_noon_break_hook | pending | - / 0 |  |  |
| 3 | shot_02a | b02_post_grad_busy_life | pending | - / 0 |  |  |
| 4 | shot_02b | b02_post_grad_busy_life | pending | - / 0 |  |  |
| 5 | shot_02c | b02_post_grad_busy_life | pending | - / 0 |  |  |
| 6 | shot_03a | b03_rooftop_arrival_full_table | pending | - / 0 |  |  |
| 7 | shot_03b | b03_rooftop_arrival_full_table | pending | - / 0 |  |  |
| 8 | shot_04a | b03_rooftop_arrival_full_table | pending | - / 0 |  |  |
| 9 | shot_04b | b03_rooftop_arrival_full_table | pending | - / 0 |  |  |
| 10 | shot_05a | b04_tan_and_gentle_girl | pending | - / 0 |  |  |
| 11 | shot_05b | b04_tan_and_gentle_girl | pending | - / 0 |  |  |
| 12 | shot_06a | b04_tan_and_gentle_girl | pending | - / 0 |  |  |
| 13 | shot_06b | b04_tan_and_gentle_girl | pending | - / 0 |  |  |
| 14 | shot_07a | b05_teasing_the_pioneers | pending | - / 0 |  |  |
| 15 | shot_07b | b05_teasing_the_pioneers | pending | - / 0 |  |  |
| 16 | shot_07c | b05_teasing_the_pioneers | pending | - / 0 |  |  |
| 17 | shot_08a | b06_dead_silence_alien_stare | pending | - / 0 |  |  |
| 18 | shot_08b | b06_dead_silence_alien_stare | pending | - / 0 |  |  |
| 19 | shot_08c | b06_dead_silence_alien_stare | pending | - / 0 |  |  |
| 20 | shot_09a | b07_hoang_anh_viet_duong_bombshell | pending | - / 0 |  |  |
| 21 | shot_09b | b07_hoang_anh_viet_duong_bombshell | pending | - / 0 |  |  |
| 22 | shot_09c | b07_hoang_anh_viet_duong_bombshell | pending | - / 0 |  |  |
| 23 | shot_10a | b08_tan_nods_bride_smiles | pending | - / 0 |  |  |
| 24 | shot_10b | b08_tan_nods_bride_smiles | pending | - / 0 |  |  |
| 25 | shot_10c | b08_tan_nods_bride_smiles | pending | - / 0 |  |  |
| 26 | shot_11a | b09_secret_wedding_album_reveal | pending | - / 0 |  |  |
| 27 | shot_11b | b09_secret_wedding_album_reveal | pending | - / 0 |  |  |
| 28 | shot_11c | b09_secret_wedding_album_reveal | pending | - / 0 |  |  |
| 29 | shot_12a | b10_where_is_my_invitation | pending | - / 0 |  |  |
| 30 | shot_12b | b10_where_is_my_invitation | pending | - / 0 |  |  |
| 31 | shot_12c | b10_where_is_my_invitation | pending | - / 0 |  |  |
| 32 | shot_13a | b11_tantrum_and_paparazzi | pending | - / 0 |  |  |
| 33 | shot_13b | b11_tantrum_and_paparazzi | pending | - / 0 |  |  |
| 34 | shot_13c | b11_tantrum_and_paparazzi | pending | - / 0 |  |  |
| 35 | shot_14a | b12_alarm_635_ceiling_shock | pending | - / 0 |  |  |
| 36 | shot_14b | b12_alarm_635_ceiling_shock | pending | - / 0 |  |  |
| 37 | shot_14c | b12_alarm_635_ceiling_shock | pending | - / 0 |  |  |
| 38 | shot_15a | b13_morning_wash_bitter_tears | pending | - / 0 |  |  |
| 39 | shot_15b | b13_morning_wash_bitter_tears | pending | - / 0 |  |  |
| 40 | shot_16a | b14_blurry_dream_bride_memory | pending | - / 0 |  |  |
| 41 | shot_16b | b14_blurry_dream_bride_memory | pending | - / 0 |  |  |
| 42 | shot_16c | b14_blurry_dream_bride_memory | pending | - / 0 |  |  |
| 43 | shot_17a | b15_psa_to_all_brothers | pending | - / 0 |  |  |
| 44 | shot_17b | b15_psa_to_all_brothers | pending | - / 0 |  |  |
| 45 | shot_18a | b16_final_warning_and_accuracy_check | pending | - / 0 |  |  |
| 46 | shot_18b | b16_final_warning_and_accuracy_check | pending | - / 0 |  |  |

## Beat & lời dẫn

- **b01_noon_break_hook** (hook) 🔊 Uhm, sắp trưa đang nghỉ ngơi rảnh rỗi, tự nhiên nhớ ra chuyện này nên phải lên mic kể ngay cho bọn mày nghe mấy cái vô tri. Thề luôn, đêm qua tao nằm mơ một quả giấc mơ vô tri đến mức sáng dậy tao ngồi lú mất đúng năm phút đồng hồ, cảm giác vừa cay vừa buồn cười không tài nào chịu nổi!
- **b02_post_grad_busy_life** (need) 🔊 Chuyện là đêm qua tao mơ thấy cả hội anh em mình gặp lại nhau sau một thời gian dài ra trường. Bình thường đứa nào đứa nấy đều bận tối mắt tối mũi với công việc riêng, lâu lắm rồi cả lũ chưa có dịp tụ tập đông đủ. Trong mơ tao nhớ mang máng có thằng nào đấy đứng ra hú cả hội đi cà phê, mà chẳng hiểu sao địa điểm lại là một cái quán rooftop nhìn quen cực kỳ, đúng kiểu giấc mơ đan xen lẫn lộn thật giả.
- **b03_rooftop_arrival_full_table** (senses) 🔊 Tao hí hửng đẩy cửa kính bước vào quán, giữa không gian quán xá đông đúc náo nhiệt thì thấy ngay nguyên một bàn dài toàn mặt chúng mày đang ngồi ăn uống cười nói rôm rả. Có đủ cả Hoàng Anh, Việt Đường, Lưu Văn Việt Đức, Nguyễn Phong, Quang Bình, Hà Phi Hùng, Nhật Anh với Duy Khiêm, cảm giác nhộn nhịp y hệt như chưa hề có cuộc chia ly nào sau ngày tốt nghiệp. Tao phi lại gần, đang định giơ tay vỗ vai chào từng thằng một thì cảnh tượng trước mắt làm tao khựng lại.
- **b04_tan_and_gentle_girl** (senses) 🔊 Đập ngay vào mắt tao là cu Vũ Tấn đang ngồi chễm chệ ngay chính giữa bàn, mà ngồi sát bên cạnh nó lại là một em gái nhìn dịu dàng, ngoan hiền cực kỳ, gọi tạm là Linh nhé. Cảm giác trong mơ lúc đấy nó ảo ma thật sự, giờ tỉnh dậy tao quên gần hết chi tiết rồi, chỉ còn đọng lại đúng cái cảm giác mái tóc đen dài mượt mà và nụ cười hiền lành ngồi sát bên cạnh thằng Vũ Tấn giữa bàn tiệc.
- **b05_teasing_the_pioneers** (target) 🔊 Thấy thế tao mới cười nham nhở trêu nó: Uầy, Vũ Tấn dạo này khá nhỉ! Thấy mấy anh em Lưu Văn Việt Đức, Nguyễn Phong, Quang Bình tiên phong dẫn đầu rồi, tiếp đến Hoàng Anh, Việt Đường, Hà Phi Hùng với Nhật Anh cũng đang khởi sắc rực rỡ với mấy mối tình, nên nay chú em cũng chính thức gia nhập đường đua đấy à? Giấu kỹ thế, hôm nay mới chịu dắt người yêu ra mắt anh em cơ đấy!
- **b06_dead_silence_alien_stare** (escalation) 🔊 Và thề luôn, ngay sau khi tao vừa dứt câu trêu đấy thì nguyên cả bàn dài đang ồn ào bỗng nhiên im phăng phắc. Từng thằng một từ Lưu Văn Việt Đức, Nguyễn Phong, Quang Bình, Hoàng Anh, Việt Đường, Hà Phi Hùng cho tới Nhật Anh, Duy Khiêm đều quay phắt lại nhìn tao bằng ánh mắt hết sức khó hiểu. Cái ánh mắt kiểu như đang nhìn một sinh vật lạ vừa từ hành tinh khác rơi xuống, từ trong rừng rậm bước ra, hay mới từ bản xa xuống phố vậy!
- **b07_hoang_anh_viet_duong_bombshell** (escalation) 🔊 Đúng lúc tao còn đang ngơ ngác thì Hoàng Anh với Việt Đường ngồi ngay bên cạnh mới phì cười, hai thằng vừa đấm thùm thụp vừa xoa vai tao mà bảo: Người yêu cái đầu mày ấy! Vợ hợp pháp của thằng Vũ Tấn đấy ông tướng ạ! Hai đứa nó vừa mới dắt nhau đi hưởng tuần trăng mật về hồi tuần trước xong, đúng là ngơ vãi cả Đạt đụt, tối cổ hết phần thiên hạ!
- **b08_tan_nods_bride_smiles** (escalation) 🔊 Nghe xong câu đấy tao đứng hình mất năm giây, trong bụng vẫn đinh ninh là lũ quỷ này đang hợp sức bày trò trêu tao nên mới lắp bắp hỏi lại như thằng ngốc. Thế mà nhìn sang giữa bàn, cu Vũ Tấn mặt cứ phởn phơ tự đắc, gật đầu cái rụp xác nhận luôn, còn cô vợ Linh bên cạnh thì ngồi che miệng cười ngại ngùng như thể chuyện cưới xin này đã bình thường từ tám đời nào rồi! Bình thường cái đầu chúng mày ấy, sao lúc đấy tao không sốc quá mà tỉnh dậy luôn cho rồi!
- **b09_secret_wedding_album_reveal** (escalation) 🔊 Chưa dừng lại ở đấy đâu, cả lũ bắt đầu rút điện thoại ra dí sát vào tận mắt kính của tao cho xem bằng chứng. Hóa ra thằng Vũ Tấn lập hẳn một cái tài khoản mạng xã hội phụ khác, đăng không biết bao nhiêu là ảnh cưới với kỷ niệm ngọt ngào như một bộ sưu tập khổng lồ mà một mình tao hoàn toàn mù tịt. Cả bàn từ Hoàng Anh, Việt Đường tới Nguyễn Phong, Quang Bình cứ thay nhau vuốt màn hình dí vào mặt tao khoe từng bức ảnh một!
- **b10_where_is_my_invitation** (climax) 🔊 Tức nước vỡ bờ, tao mới quay phắt ra giữa bàn đập tay hỏi lớn: Ủa thế thiệp cưới của tao đâu? Sao đám cưới bạn thân mà tao không biết một chữ bẻ đôi nào? Nghe tao hỏi xong, cả lũ ngồi quanh bàn từ Vũ Tấn, Lưu Văn Việt Đức, Hà Phi Hùng tới Nhật Anh, Duy Khiêm đồng loạt nở nụ cười khẩy đầy đểu cáng kiểu: Ơ thế hóa ra em không được mời à, hẹ hẹ! Ai nấy đều đi ăn cưới chụp choẹt check-in ầm ầm, chỉ có mỗi mình tao bị bỏ rơi ở thời kỳ đồ đá!
- **b11_tantrum_and_paparazzi** (climax) 🔊 Lúc đấy tao giãy nảy lên ăn vạ ngay tại bàn, cảm giác vừa bất lực vừa tủi thân không để đâu cho hết. Thấy tao dỗi, vợ chồng Vũ Tấn với Linh mới bắt đầu quay sang bàn luận rối rít giải thích rồi dỗ dành tao, đã đang bực mình mà nhìn hai đứa nó cuống quýt bên nhau vẫn thấy đáng yêu cực kỳ. Trong khi hai vợ chồng ra sức an ủi tao thì cả lũ xung quanh ngồi xem kịch hay đập bàn đập ghế cười hô hố, đặc biệt là thằng Nguyễn Phong với Duy Khiêm còn rút máy điện thoại giơ lên quay cận cảnh tao đang ngồi dỗi hờn ăn vạ nữa chứ!
- **b12_alarm_635_ceiling_shock** (resolution) 🔊 Đang tới đúng cái đoạn gay cấn nhất là hội anh em chuẩn bị chốt phương án đền bù kèo nhậu cho tao, chưa kịp nghe rõ trong mơ thỏa thuận được cái gì thì bỗng nhiên: tíng tình tình tính ting! Tiếng chuông báo thức sáu giờ ba mươi lăm phút sáng réo vang inh ỏi! Tao giật bắn mình mở choàng mắt ra thì trước mặt chỉ là cái trần nhà quen thuộc, cảm giác hụt hẫng rơi từ trên mây xuống đất, thật giả lẫn lộn đến mức phải vớ lấy điện thoại ngồi lướt Tóp Tóp một lúc lâu não mới chịu thông lại!
- **b13_morning_wash_bitter_tears** (resolution) 🔊 Bước xuống giường đi vào góc gương rửa mặt và tắm rửa buổi sáng mà khóe mắt tao vẫn còn cay xè, nỗi đau bị bỏ quên tấm thiệp hồng trong mơ nó cứ thấm thía tận tâm can. Tao thực sự không hiểu thằng Vũ Tấn nó làm cái trò trống gì trong tiềm thức của tao mà tự nhiên lại nằm mơ ra quả kịch bản éo le đến thế, không biết là điềm báo mộng cái gì đây!
- **b14_blurry_dream_bride_memory** (resolution) 🔊 Mà nghĩ lại mới thấy buồn cười, lúc ở trong mơ tao còn đang bận sốc nặng vụ không được mời cưới nên chẳng kịp lưu kỹ khuôn mặt cô dâu Linh vào bộ nhớ não. Giờ cố vắt óc nhớ lại cũng chỉ thấy mang máng một bóng hình tóc đen dài thẳng mượt, làn da trắng trẻo, đôi mắt trong veo có hồn và nụ cười nhẹ nhàng dịu dàng chứ không phải nét sắc sảo. Nhưng khuôn mặt trong mơ cứ mờ mờ ảo ảo dưới ánh đèn vàng, giờ mà bắt tao cầm bút vẽ lại chắc tao vẽ ra người ngoài hành tinh mất!
- **b15_psa_to_all_brothers** (resolution) 🔊 Qua giấc mơ vô tri đêm qua, tao xin phát thông báo cảnh báo khẩn cấp tới toàn thể anh em trong nhóm: từ Vũ Tấn, Hoàng Anh, Việt Đường, Lưu Văn Việt Đức, Nguyễn Phong, Quang Bình cho tới Hà Phi Hùng, Nhật Anh, Duy Khiêm! Anh em mình ra trường có thể ít gặp nhau, mỗi đứa một guồng quay cuộc sống riêng, nhưng sau này đứa nào cưới vợ thì nhớ gửi thiệp mời tao cho đầy đủ! Tao không cần phong bì hoàn lại đâu, tao chỉ cần đúng một tấm thiệp hồng trao tay để xác nhận tình anh em mình vẫn còn tồn tại, đừng để tao phải biết tin qua tài khoản phụ hay báo mạng nhé!
- **b16_final_warning_and_accuracy_check** (resolution) 🔊 Các anh em nghe rõ rồi thì nhớ xác nhận giúp tao một tiếng nhé, đừng có mà bỏ rơi thằng bạn này đấy! Còn bạn gái hay vợ tương lai của đứa nào tình cờ nghe được quả podcast giấc mơ vô tri này của tao thì cũng nhớ nhắc chồng gửi thiệp cho tao nha! Phần còn lại thì để tao ghim sẵn ở đây, đợi hôm nào thằng Vũ Tấn cưới vợ thật, tao sẽ mang đúng cái video này ra đối chiếu với cô dâu Linh ngoài đời xem giấc mơ báo mộng của tao có độ chính xác bao nhiêu phần trăm!

## Media trên máy này

⚠ Máy **user** thiếu 46/152 file — chạy `media-pull` (hoặc tải lại take từ Flow).

- `assets/clips/shot_01a.mp4` — shot_01a clip dựng
- `assets/clips/shot_01b.mp4` — shot_01b clip dựng
- `assets/clips/shot_02a.mp4` — shot_02a clip dựng
- `assets/clips/shot_02b.mp4` — shot_02b clip dựng
- `assets/clips/shot_02c.mp4` — shot_02c clip dựng
- `assets/clips/shot_03a.mp4` — shot_03a clip dựng
- `assets/clips/shot_03b.mp4` — shot_03b clip dựng
- `assets/clips/shot_04a.mp4` — shot_04a clip dựng
- `assets/clips/shot_04b.mp4` — shot_04b clip dựng
- `assets/clips/shot_05a.mp4` — shot_05a clip dựng
- `assets/clips/shot_05b.mp4` — shot_05b clip dựng
- `assets/clips/shot_06a.mp4` — shot_06a clip dựng
- `assets/clips/shot_06b.mp4` — shot_06b clip dựng
- `assets/clips/shot_07a.mp4` — shot_07a clip dựng
- `assets/clips/shot_07b.mp4` — shot_07b clip dựng
- `assets/clips/shot_07c.mp4` — shot_07c clip dựng
- `assets/clips/shot_08a.mp4` — shot_08a clip dựng
- `assets/clips/shot_08b.mp4` — shot_08b clip dựng
- `assets/clips/shot_08c.mp4` — shot_08c clip dựng
- `assets/clips/shot_09a.mp4` — shot_09a clip dựng
- `assets/clips/shot_09b.mp4` — shot_09b clip dựng
- `assets/clips/shot_09c.mp4` — shot_09c clip dựng
- `assets/clips/shot_10a.mp4` — shot_10a clip dựng
- `assets/clips/shot_10b.mp4` — shot_10b clip dựng
- `assets/clips/shot_10c.mp4` — shot_10c clip dựng
- … và 21 file khác

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-20 18:32 | user | `storyboard ` | ok |
| 10-20 18:32 | user | `voiceover ` | ok |
| 10-20 18:31 | user | `voiceover ` | ok |
| 10-20 18:21 | user | `voiceover ` | ok |
| 10-20 18:21 | user | `storyboard ` | ok |
| 10-20 18:20 | user | `flow-harvest --kind image --wait --wait-timeout 180 --shots shot_10c,shot_11b,shot_11c,shot_12b,shot_12c,shot_13b,shot_13c,shot_14b,shot_14c,shot_15b,shot_16b,shot_16c,shot_` | ok |
| 10-20 18:20 | user | `flow-harvest --kind image --wait --wait-timeout 600 --shots shot_10c,shot_11b,shot_11c,shot_12b,shot_12c,shot_13b,shot_13c,shot_14b,shot_14c,shot_15b,shot_16b,shot_16c,shot_` | ok |
| 10-20 18:19 | user | `flow-generate --kind frames --count 2 --new-project --shots shot_10c,shot_11b,shot_11c,shot_12b,shot_12c,shot_13b,shot_13c,shot_14b,shot_14c,shot_15b,shot_16b,shot_16c,shot_1` | ok |
| 10-20 18:15 | user | `flow-harvest --kind image --wait --wait-timeout 180 --shots shot_01b,shot_02a,shot_02b,shot_02c,shot_03b,shot_04b,shot_05b,shot_06b,shot_07b,shot_07c,shot_08b,shot_08c,shot_` | ok |
| 10-20 18:15 | user | `flow-harvest --kind image --wait --wait-timeout 600 --shots shot_01b,shot_02a,shot_02b,shot_02c,shot_03b,shot_04b,shot_05b,shot_06b,shot_07b,shot_07c,shot_08b,shot_08c,shot_` | ok |
| 10-20 18:14 | user | `flow-generate --kind frames --count 2 --new-project --shots shot_01b,shot_02a,shot_02b,shot_02c,shot_03b,shot_04b,shot_05b,shot_06b,shot_07b,shot_07c,shot_08b,shot_08c,shot_0` | ok |
| 10-20 18:11 | user | `flow-harvest --kind image --wait --wait-timeout 180 --shots shot_02a` | ok |
| 10-20 18:10 | user | `flow-generate --kind frames --count 2 --new-project --shots shot_02a` | ok |
| 10-20 18:06 | user | `storyboard ` | ok |
| 10-20 18:05 | user | `qa-frames ` | ❌ [ERROR] Không có clip nào để QA. |
