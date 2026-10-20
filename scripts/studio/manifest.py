"""Đọc/ghi project_manifest.json an toàn (ghi nguyên tử + bản sao lưu)."""

import json
import os
import shutil
import sys
from pathlib import Path

SCHEMA_VERSION = 2

# Trạng thái vòng đời của một shot
STATUS_PENDING = "pending"
STATUS_RENDERED = "rendered"
STATUS_QA_PASS = "qa_pass"
STATUS_QA_WARN = "qa_warn"
STATUS_QA_FAIL = "qa_fail"
STATUS_APPROVED = "approved"


class ManifestError(Exception):
    pass


def manifest_path(proj_dir: Path) -> Path:
    return Path(proj_dir) / "project_manifest.json"


def load(proj_dir: Path) -> dict:
    path = manifest_path(proj_dir)
    if not path.exists():
        raise ManifestError(f"Không tìm thấy {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save(proj_dir: Path, manifest: dict) -> None:
    path = manifest_path(proj_dir)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def ordered_shots(manifest: dict) -> list:
    shots = manifest.get("shots", [])
    return sorted(shots, key=lambda s: (s.get("order", 0), s.get("shot_id", "")))


def find_shot(manifest: dict, shot_id: str) -> dict:
    for s in manifest.get("shots", []):
        if s.get("shot_id") == shot_id:
            return s
    raise ManifestError(f"Không có shot '{shot_id}' trong manifest")


def clip_path(proj_dir: Path, shot: dict) -> Path:
    rel = shot.get("clip_output_path") or f"assets/clips/{shot['shot_id']}.mp4"
    return Path(proj_dir) / rel


def characters_by_id(manifest: dict) -> dict:
    return {c["id"]: c for c in manifest.get("characters", []) if c.get("id")}


def environments_by_id(manifest: dict) -> dict:
    return {e["id"]: e for e in manifest.get("environments", []) if e.get("id")}


def shot_audio(shot: dict) -> dict:
    """Chuẩn hóa khối audio của shot (hỗ trợ cả trường cũ `dialogue_text`)."""
    audio = dict(shot.get("audio") or {})
    audio.setdefault("mode", "sfx_only")
    if not audio.get("line") and shot.get("dialogue_text"):
        audio["line"] = shot["dialogue_text"]
    return audio


class ProjectLock:
    """Khóa độc quyền theo dự án cho các lệnh sửa manifest (khóa của hệ điều hành: tự nhả khi tiến trình kết thúc).

    Ngăn lỗi ghi đè: lệnh A (vd. flow-harvest chạy lâu) đọc manifest, lệnh B lưu thay đổi, rồi A lưu đè làm mất của B.
    """

    def __init__(self, proj_dir: Path, timeout: float = 1800, poll: float = 2.0):
        self.path = Path(proj_dir) / ".studio.lock"
        self.timeout, self.poll, self.fh = timeout, poll, None

    def _try(self) -> bool:
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def __enter__(self):
        import time

        self.fh = open(self.path, "a+")
        t0, warned = time.time(), False
        while not self._try():
            if time.time() - t0 > self.timeout:
                self.fh.close()
                raise ManifestError(f"Dự án đang bị lệnh khác giữ khóa quá {self.timeout:.0f}s ({self.path}).")
            if not warned:
                print("[INFO] Dự án đang bị lệnh khác sử dụng — chờ lệnh đó xong...", file=sys.stderr, flush=True)
                warned = True
            time.sleep(self.poll)
        return self

    def __exit__(self, *exc):
        try:
            if os.name == "nt":
                import msvcrt

                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        self.fh.close()
