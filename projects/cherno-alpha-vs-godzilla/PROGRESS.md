# Tiến độ: Cherno Alpha vs Godzilla

> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng `python scripts/studio_helper.py note --project cherno-alpha-vs-godzilla "..."`.

## Bắt đầu phiên trên máy khác

```powershell
git pull
python scripts/studio_helper.py media-pull --project cherno-alpha-vs-godzilla   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)
python scripts/studio_helper.py resume --project cherno-alpha-vs-godzilla       # kiểm tra máy + in bước tiếp theo
```

Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).

Máy mới (Windows / Ubuntu) hoặc thiếu rclone / `.env`: làm theo [docs/SYNC_SETUP.md](../../docs/SYNC_SETUP.md).

Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).

## Trạng thái

- **Slug:** `cherno-alpha-vs-godzilla` — thư mục `projects/cherno-alpha-vs-godzilla/` (KHÔNG `init` dự án mới)
- **Flow:** https://flow.google.com/project/eba75017-1af5-48e6-b95b-1b0d6294c221
- **Ngôn ngữ / khung:** en / 16:9; giọng dẫn `-`
- **Cập nhật lần cuối:** 2026-10-22T23:12:16 trên máy **DESKTOP-HUP72C4** (lệnh `qa-vision`)
- **Storyboard:** chưa duyệt

## ▶ Bước tiếp theo: 4. 🧑 Chờ người dùng duyệt storyboard

60 shot chưa có video. Storyboard chưa duyệt.

```powershell
python scripts/studio_helper.py storyboard --project cherno-alpha-vs-godzilla
(người dùng xem output/storyboard.html)
python scripts/studio_helper.py storyboard-approve --project cherno-alpha-vs-godzilla --by "<tên>"
```

## Shot

| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |
|---|---|---|---|---|---|---|
| 1 | shot_01 | beat_01 | pending | - / 0 |  |  |
| 2 | shot_02 | beat_01 | pending | - / 0 |  |  |
| 3 | shot_03 | beat_01 | pending | - / 0 |  |  |
| 4 | shot_04 | beat_01 | pending | - / 0 |  |  |
| 5 | shot_05 | beat_02 | pending | - / 0 |  |  |
| 6 | shot_06 | beat_02 | pending | - / 0 |  |  |
| 7 | shot_07 | beat_02 | pending | - / 0 |  |  |
| 8 | shot_08 | beat_02 | pending | - / 0 |  |  |
| 9 | shot_09 | beat_03 | pending | - / 0 |  |  |
| 10 | shot_10 | beat_03 | pending | - / 0 |  |  |
| 11 | shot_11 | beat_03 | pending | - / 0 |  |  |
| 12 | shot_12 | beat_03 | pending | - / 0 |  |  |
| 13 | shot_13 | beat_04 | pending | - / 0 |  |  |
| 14 | shot_14 | beat_04 | pending | - / 0 |  |  |
| 15 | shot_15 | beat_04 | pending | - / 0 |  |  |
| 16 | shot_16 | beat_04 | pending | - / 0 |  |  |
| 17 | shot_17 | beat_05 | pending | - / 0 |  |  |
| 18 | shot_18 | beat_05 | pending | - / 0 |  |  |
| 19 | shot_19 | beat_05 | pending | - / 0 |  |  |
| 20 | shot_20 | beat_05 | pending | - / 0 |  |  |
| 21 | shot_21 | beat_06 | pending | - / 0 |  |  |
| 22 | shot_22 | beat_06 | pending | - / 0 |  |  |
| 23 | shot_23 | beat_06 | pending | - / 0 |  |  |
| 24 | shot_24 | beat_06 | pending | - / 0 |  |  |
| 25 | shot_25 | beat_07 | pending | - / 0 |  |  |
| 26 | shot_26 | beat_07 | pending | - / 0 |  |  |
| 27 | shot_27 | beat_07 | pending | - / 0 |  |  |
| 28 | shot_28 | beat_07 | pending | - / 0 |  |  |
| 29 | shot_29 | beat_08 | pending | - / 0 |  |  |
| 30 | shot_30 | beat_08 | pending | - / 0 |  |  |
| 31 | shot_31 | beat_08 | pending | - / 0 |  |  |
| 32 | shot_32 | beat_08 | pending | - / 0 |  |  |
| 33 | shot_33 | beat_09 | pending | - / 0 |  |  |
| 34 | shot_34 | beat_09 | pending | - / 0 |  |  |
| 35 | shot_35 | beat_09 | pending | - / 0 |  |  |
| 36 | shot_36 | beat_09 | pending | - / 0 |  |  |
| 37 | shot_37 | beat_10 | pending | - / 0 |  |  |
| 38 | shot_38 | beat_10 | pending | - / 0 |  |  |
| 39 | shot_39 | beat_10 | pending | - / 0 |  |  |
| 40 | shot_40 | beat_10 | pending | - / 0 |  |  |
| 41 | shot_41 | beat_11 | pending | - / 0 |  |  |
| 42 | shot_42 | beat_11 | pending | - / 0 |  |  |
| 43 | shot_43 | beat_11 | pending | - / 0 |  |  |
| 44 | shot_44 | beat_11 | pending | - / 0 |  |  |
| 45 | shot_45 | beat_12 | pending | - / 0 |  |  |
| 46 | shot_46 | beat_12 | pending | - / 0 |  |  |
| 47 | shot_47 | beat_12 | pending | - / 0 |  |  |
| 48 | shot_48 | beat_12 | pending | - / 0 |  |  |
| 49 | shot_49 | beat_13 | pending | - / 0 |  |  |
| 50 | shot_50 | beat_13 | pending | - / 0 |  |  |
| 51 | shot_51 | beat_13 | pending | - / 0 |  |  |
| 52 | shot_52 | beat_13 | pending | - / 0 |  |  |
| 53 | shot_53 | beat_14 | pending | - / 0 |  |  |
| 54 | shot_54 | beat_14 | pending | - / 0 |  |  |
| 55 | shot_55 | beat_14 | pending | - / 0 |  |  |
| 56 | shot_56 | beat_14 | pending | - / 0 |  |  |
| 57 | shot_57 | beat_15 | pending | - / 0 |  |  |
| 58 | shot_58 | beat_15 | pending | - / 0 |  |  |
| 59 | shot_59 | beat_15 | pending | - / 0 |  |  |
| 60 | shot_60 | beat_15 | pending | - / 0 |  |  |

## Beat & lời dẫn

- **beat_01** (hook_godzilla_ocean_emergence) — 
- **beat_02** (cherno_airdrop_and_faceoff) — 
- **beat_03** (bridge_harbor_to_boulevard_charge) — 
- **beat_04** (act2_first_piston_punch_collision) — 
- **beat_05** (shoulder_ram_and_kaiju_claw_counter) — 
- **beat_06** (bridge_boulevard_to_burning_plaza) — 
- **beat_07** (act3_shoulder_flame_turbines_assault) — 
- **beat_08** (reversal_180_tail_whip_skyscraper_crash) — 
- **beat_09** (bridge_plaza_to_trenched_avenue) — 
- **beat_10** (act4_dorsal_fins_atomic_charge) — 
- **beat_11** (atomic_breath_clash_and_trench_block) — 
- **beat_12** (piston_thruster_charge_through_smoke_bridge) — 
- **beat_13** (act5_tesla_fist_overcharge_and_final_impact) — 
- **beat_14** (shockwave_cloud_parting_and_kaiju_fall) — 
- **beat_15** (resolution_smoke_clearing_and_victor_stand) — 

## Media trên máy này

⚠ Máy **DESKTOP-HUP72C4** thiếu 60/126 file — chạy `media-pull` (hoặc tải lại take từ Flow).

- `assets/clips/shot_01.mp4` — shot_01 clip dựng
- `assets/clips/shot_02.mp4` — shot_02 clip dựng
- `assets/clips/shot_03.mp4` — shot_03 clip dựng
- `assets/clips/shot_04.mp4` — shot_04 clip dựng
- `assets/clips/shot_05.mp4` — shot_05 clip dựng
- `assets/clips/shot_06.mp4` — shot_06 clip dựng
- `assets/clips/shot_07.mp4` — shot_07 clip dựng
- `assets/clips/shot_08.mp4` — shot_08 clip dựng
- `assets/clips/shot_09.mp4` — shot_09 clip dựng
- `assets/clips/shot_10.mp4` — shot_10 clip dựng
- `assets/clips/shot_11.mp4` — shot_11 clip dựng
- `assets/clips/shot_12.mp4` — shot_12 clip dựng
- `assets/clips/shot_13.mp4` — shot_13 clip dựng
- `assets/clips/shot_14.mp4` — shot_14 clip dựng
- `assets/clips/shot_15.mp4` — shot_15 clip dựng
- `assets/clips/shot_16.mp4` — shot_16 clip dựng
- `assets/clips/shot_17.mp4` — shot_17 clip dựng
- `assets/clips/shot_18.mp4` — shot_18 clip dựng
- `assets/clips/shot_19.mp4` — shot_19 clip dựng
- `assets/clips/shot_20.mp4` — shot_20 clip dựng
- `assets/clips/shot_21.mp4` — shot_21 clip dựng
- `assets/clips/shot_22.mp4` — shot_22 clip dựng
- `assets/clips/shot_23.mp4` — shot_23 clip dựng
- `assets/clips/shot_24.mp4` — shot_24 clip dựng
- `assets/clips/shot_25.mp4` — shot_25 clip dựng
- … và 35 file khác

## Nhật ký lệnh (mới nhất trước)

| Lúc | Máy | Lệnh | Kết quả |
|---|---|---|---|
| 10-22 23:12 | DESKTOP-HUP72C4 | `qa-vision ` | ok |
| 10-22 23:12 | DESKTOP-HUP72C4 | `qa-frames ` | ❌ [ERROR] Không có clip nào để QA. |
| 10-22 23:11 | DESKTOP-HUP72C4 | `lint-prompts ` | ok |
| 10-22 23:11 | DESKTOP-HUP72C4 | `lint-prompts ` | ❌ AttributeError: 'str' object has no attribute 'get' |
| 10-22 23:10 | DESKTOP-HUP72C4 | `storyboard ` | ok |
| 10-22 23:10 | DESKTOP-HUP72C4 | `lint-prompts ` | ❌ AttributeError: 'str' object has no attribute 'get' |
| 10-22 23:10 | DESKTOP-HUP72C4 | `build-prompts ` | ok |
| 10-22 23:09 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_57,shot_58,shot_59,shot_60 --wait` | ok |
| 10-22 23:06 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_49,shot_50,shot_51,shot_52,shot_53,shot_54,shot_55,shot_56,shot_57,shot_58,shot_59,shot_60 --wait` | ok |
| 10-22 23:03 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_55,shot_56,shot_57,shot_58,shot_59,shot_60 --count 2` | ok |
| 10-22 23:01 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_49,shot_50,shot_51,shot_52,shot_53,shot_54 --count 2` | ok |
| 10-22 22:58 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_49,shot_50,shot_51,shot_52,shot_53,shot_54 --count 2` | ok |
| 10-22 22:54 | DESKTOP-HUP72C4 | `flow-harvest --kind image --shots shot_43,shot_44,shot_45,shot_46,shot_47,shot_48 --wait` | ok |
| 10-22 22:53 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_46,shot_47,shot_48 --count 2` | ok |
| 10-22 22:51 | DESKTOP-HUP72C4 | `flow-generate --kind frames --shots shot_43,shot_44,shot_45 --count 2` | ok |
