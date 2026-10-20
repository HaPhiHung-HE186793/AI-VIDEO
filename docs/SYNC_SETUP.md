# Đồng bộ 2 máy: Windows 11 (nhà) ↔ Ubuntu (công ty)

> **Agent đọc file này khi:** `resume` báo thiếu `STUDIO_MEDIA_DIR` / thiếu media, hoặc máy chưa cài đủ công cụ.
> Làm đúng phần của hệ điều hành đang chạy. Không bao giờ in hay commit nội dung `.env`.

## Cái gì đi đường nào

| Nội dung | Đồng bộ bằng | Ghi chú |
|---|---|---|
| Code, manifest, `PROGRESS.md`, `INDEX.md`, prompt, ảnh frame nhỏ | **git** (GitHub `HaPhiHung-HE186793/AI-VIDEO`) | `git pull` đầu phiên, `git push` cuối phiên |
| Clip `.mp4`, lời dẫn/nhạc `.wav`, video thành phẩm | **rclone → Google Drive** (`gdrive:AI-video-media/<slug>/`) | `media-pull` / `media-push`; git chặn các file này |
| `.env` (API key, tên máy, thư mục media) | **không đồng bộ** — mỗi máy tự tạo | chép `.env.example` |
| Dự án Google Flow (clip gốc, credit) | nằm trên tài khoản Google | Chrome điều khiển phải đăng nhập **cùng tài khoản** |

Google Drive for desktop không có bản Ubuntu → dùng **rclone** (miễn phí, mã nguồn mở) trên cả 2 máy cho giống nhau.

---

## Windows 11 (máy nhà) — ĐÃ CÀI 2026-10-20

- rclone v1.75.2 ở `%LOCALAPPDATA%\Programs\rclone\rclone.exe` (đã thêm vào PATH người dùng, đã đối chiếu SHA256 với bản chính thức).
- Remote `gdrive` (Google Drive) đã cấu hình bằng `rclone config create gdrive drive scope=drive`.
- `.env` có: `STUDIO_MACHINE=may-nha-win11`, `STUDIO_MEDIA_DIR=rclone:gdrive:AI-video-media`.

Cài lại từ đầu trên một máy Windows khác (PowerShell, không cần quyền admin):
```powershell
$dst = "$env:LOCALAPPDATA\Programs\rclone"; New-Item -ItemType Directory -Force $dst | Out-Null
Invoke-WebRequest https://downloads.rclone.org/rclone-current-windows-amd64.zip -OutFile $env:TEMP\rclone.zip
Expand-Archive $env:TEMP\rclone.zip $env:TEMP\rclone_x -Force
Copy-Item (Get-ChildItem $env:TEMP\rclone_x -Recurse -Filter rclone.exe)[0].FullName $dst
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$dst", "User")
& "$dst\rclone.exe" config create gdrive drive scope=drive   # mở trình duyệt → đăng nhập Google → Cho phép
```

---

## Ubuntu (máy công ty) — làm 1 lần

```bash
# 1. Công cụ hệ thống
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ffmpeg fonts-dejavu-core curl
# Chrome (bước Flow cần Chrome thật, không dùng Chromium snap)
curl -fsSLo /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y /tmp/chrome.deb
# rclone bản mới (bản apt của Ubuntu thường cũ nhưng vẫn dùng được: sudo apt install rclone)
sudo -v && curl -fsSL https://rclone.org/install.sh | sudo bash

# 2. Mã nguồn
git clone https://github.com/HaPhiHung-HE186793/AI-VIDEO.git ~/AI-video
cd ~/AI-video
python3 -m venv .venv && source .venv/bin/activate      # mọi phiên sau: source .venv/bin/activate
pip install -r requirements.txt

# 3. Kết nối Google Drive (mở trình duyệt → đăng nhập ĐÚNG tài khoản Google → Cho phép)
rclone config create gdrive drive scope=drive
rclone lsd gdrive:                                        # kiểm tra: thấy thư mục AI-video-media

# 4. .env riêng của máy này
cp .env.example .env
nano .env
#   GEMINI_API_KEY=<dán key — lấy ở aistudio.google.com/apikey, KHÔNG gửi qua chat/git>
#   STUDIO_MACHINE=may-cong-ty-ubuntu
#   STUDIO_MEDIA_DIR=rclone:gdrive:AI-video-media

# 5. Chrome điều khiển cho Google Flow (đăng nhập Google 1 lần, profile ~/chrome_ai_bot được giữ lại)
python scripts/studio_helper.py check-browser --launch

# 6. Kiểm tra
python -m pytest tests -q
python scripts/studio_helper.py resume
```

Máy Ubuntu không có giao diện (SSH): bước 3 dùng `rclone authorize "drive"` trên một máy có trình duyệt rồi dán token,
hoặc chép file `~/.config/rclone/rclone.conf` (Windows: `%APPDATA%\rclone\rclone.conf`) qua kênh an toàn — file này chứa token truy cập Drive, **không commit**.

---

## Mỗi phiên làm việc (cả 2 máy)

**Bắt đầu** (agent tự làm khi người dùng nói "làm tiếp"):
```bash
git pull
python scripts/studio_helper.py resume                          # dự án gần nhất, bước tiếp theo, cảnh báo
python scripts/studio_helper.py media-pull --project <slug>     # chỉ tải file còn thiếu
```

**Kết thúc** (trước khi rời máy):
```bash
python scripts/studio_helper.py note --project <slug> --kind todo "đang dở: ..."
python scripts/studio_helper.py media-push --project <slug>     # chỉ đẩy file mới/đổi
git add -A && git commit -m "<việc đã làm>" && git push
```

`media-push --all` / `media-pull --all`: cả take không được chọn (nặng hơn nhiều — chỉ khi cần QA/chọn lại take).

## Lưu ý

- **Không làm cùng lúc 2 máy trên 1 dự án** — khóa dự án chỉ có tác dụng trong 1 máy. `resume` cảnh báo nếu máy kia vừa hoạt động < 45 phút.
- Quên `media-push` ở máy kia: clip vẫn còn trên Flow (dự án ghi trong PROGRESS.md) — tải lại thủ công, hoặc quay lại máy kia đẩy lên.
- **rclone báo "shared client_id is being retired" (2026):** vẫn chạy được tới khi Google tắt. Khi `media-push` lỗi xác thực:
  tạo OAuth client ID riêng **miễn phí** (Google Cloud Console → APIs & Services → bật Google Drive API → Credentials →
  OAuth client ID loại *Desktop app*; không cần bật thanh toán) rồi `rclone config update gdrive client_id <id> client_secret <secret>`
  và `rclone config reconnect gdrive:` trên **mỗi máy**. Hướng dẫn: https://rclone.org/drive/#making-your-own-client-id
- Phụ đề in cứng dùng font Arial; Ubuntu thiếu thì ffmpeg tự thay font khác (muốn giống hệt: `sudo apt install ttf-mscorefonts-installer`).
- Lệnh trên Ubuntu viết `python` (trong venv); ngoài venv dùng `python3`.
