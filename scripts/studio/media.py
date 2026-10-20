"""Tiện ích ffmpeg / OpenCV: tìm ffmpeg, probe, đọc frame, đọc PCM, chạy lệnh có báo lỗi rõ ràng."""

import hashlib
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


class MediaError(Exception):
    pass


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as e:
        raise MediaError("Không tìm thấy ffmpeg. Cài ffmpeg vào PATH hoặc `pip install -r requirements.txt`.") from e


def run_ffmpeg(args: list, cwd: Path = None) -> None:
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *args]
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        tail = res.stderr.decode("utf-8", "replace").strip().splitlines()[-15:]
        raise MediaError("ffmpeg lỗi:\n" + "\n".join(tail))


@lru_cache(maxsize=1)
def has_nvenc() -> bool:
    try:
        res = subprocess.run(
            [ffmpeg_exe(), "-hide_banner", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.1",
             "-c:v", "h264_nvenc", "-f", "null", "-"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
        )
        return res.returncode == 0
    except Exception:
        return False


def probe(path: Path) -> dict:
    """Thông tin cơ bản của file media (parse output `ffmpeg -i`)."""
    path = Path(path)
    if not path.exists():
        raise MediaError(f"Không tồn tại: {path}")
    res = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = res.stderr.decode("utf-8", "replace")
    info = {"path": str(path), "duration": 0.0, "width": 0, "height": 0, "fps": 0.0, "has_audio": False, "has_video": False}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if m:
        info["duration"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    for line in text.splitlines():
        if "Video:" in line and not info["has_video"]:
            info["has_video"] = True
            sm = re.search(r"\b(\d{2,5})x(\d{2,5})\b", line)
            if sm:
                info["width"], info["height"] = int(sm.group(1)), int(sm.group(2))
            fm = re.search(r"(\d+(?:\.\d+)?)\s*fps", line)
            if fm:
                info["fps"] = float(fm.group(1))
        if "Audio:" in line:
            info["has_audio"] = True
    return info


def cv2_module():
    try:
        import cv2

        return cv2
    except ImportError as e:
        raise MediaError("Thiếu opencv-python. Chạy `pip install -r requirements.txt`.") from e


def read_gray_frames(path: Path, size=(320, 180)):
    """Trả về (fps, list frame xám đã resize)."""
    cv2 = cv2_module()
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(cv2.resize(f, size), cv2.COLOR_BGR2GRAY))
    cap.release()
    return fps, frames


def read_frame_at(path: Path, t_sec: float = None, last: bool = False):
    """Đọc 1 frame màu (BGR) tại thời điểm t hoặc frame cuối."""
    cv2 = cv2_module()
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    idx = n - 1 if last or t_sec is None else int(round(t_sec * fps))
    idx = max(0, min(n - 1, idx))
    frame = None
    # Một số container báo thừa frame cuối: lùi dần đến khi đọc được.
    for back in range(0, 6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, idx - back))
        ok, f = cap.read()
        if ok:
            frame, idx = f, max(0, idx - back)
            break
    cap.release()
    if frame is None:
        raise MediaError(f"Không đọc được frame từ {path}")
    return frame, idx / fps


def read_pcm(path: Path, sr: int = 16000):
    """Đọc audio mono float32 [-1, 1]. Trả về mảng rỗng nếu không có audio."""
    import numpy as np

    res = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    return np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
