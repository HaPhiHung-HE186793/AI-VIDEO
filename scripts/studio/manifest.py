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


def props_by_id(manifest: dict) -> dict:
    return {p["id"]: p for p in manifest.get("props", []) if p.get("id")}


def project_code(manifest: dict) -> str:
    """Mã viết tắt 4–6 ký tự chữ-số in hoa của dự án để đóng dấu Unique ID cho mọi frame/asset trên Flow."""
    import re

    if manifest.get("project_code"):
        return re.sub(r"[^A-Z0-9]", "", str(manifest["project_code"]).upper())[:6] or "PROJ"
    slug = manifest.get("project_slug") or manifest.get("project_name") or "proj"
    parts = [p for p in re.split(r"[^a-zA-Z0-9]+", slug) if p]
    if not parts:
        return "PROJ"
    if len(parts) == 1:
        return parts[0][:5].upper()
    code = "".join(p[0] for p in parts[:6]).upper()
    if len(code) < 4:
        code = (code + parts[0][1:].upper())[:4]
    return code[:6]


def keyframe_uid(manifest: dict, shot_id: str, slot: str = "start") -> str:
    """ID duy nhất cho Keyframe đầu/cuối của shot (vd: KF_PGMT_S01_START, KF_PGMT_S01_END)."""
    import re

    pcode = project_code(manifest)
    m = re.search(r"(\d+)$", shot_id)
    scode = f"S{int(m.group(1)):02d}" if m else re.sub(r"[^A-Z0-9]", "", shot_id.upper())[:6]
    tag = "END" if str(slot).lower() in ("end", "last") else "START"
    return f"KF_{pcode}_{scode}_{tag}"


def keyframe_rel_path(manifest: dict, shot_id: str, slot: str = "start", ext: str = ".png") -> str:
    """Đường dẫn tương đối chuẩn có gắn Unique ID cho Keyframe của shot."""
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"assets/frames/{keyframe_uid(manifest, shot_id, slot)}{ext}"


def asset_uid(manifest: dict, asset_id: str, view: str = "") -> str:
    """ID duy nhất cho ảnh tham chiếu nhân vật/bối cảnh/đạo cụ khi tìm kiếm trên Flow."""
    import re

    pcode = project_code(manifest)
    clean_id = re.sub(r"[^A-Z0-9_]", "_", str(asset_id).upper()).strip("_")
    suffix = f"_{re.sub(r'[^A-Z0-9]', '', view.upper())}" if view else ""
    return f"REF_{pcode}_{clean_id}{suffix}"


def resolve_chained_keyframes(manifest: dict, proj_dir: Path = None) -> list:
    """Tự động nối Keyframe giữa các shot liên tiếp cùng cảnh (Daisy-Chain Keyframing).

    - Nếu shot N có `transition_to_next == "INTRA_SCENE_CONTINUE"` hoặc shot N+1 đặt `chain_from_prev=True`:
      + Nếu shot N có `last_frame_path`, tự gán làm `first_frame_path` của shot N+1 (nối liền mạch tuyệt đối).
      + Ngược lại, nếu shot N ở chế độ `first_last` nhưng chưa có `last_frame_path`, còn shot N+1 đã có
        `first_frame_path`, tự dùng `first_frame_path` của shot N+1 làm `last_frame_path` của shot N.
    """
    shots = ordered_shots(manifest)
    linked = []

    def exists_ok(rel_path: str) -> bool:
        if not rel_path:
            return False
        return True if proj_dir is None else (Path(proj_dir) / rel_path).exists()

    for i in range(len(shots) - 1):
        prev, cur = shots[i], shots[i + 1]
        if prev.get("exclude_from_edit") or cur.get("exclude_from_edit"):
            continue
        is_chained = bool(cur.get("chain_from_prev") or prev.get("transition_to_next") == "INTRA_SCENE_CONTINUE")
        if not is_chained:
            continue
        prev_last = prev.get("last_frame_path") or ""
        cur_first = cur.get("first_frame_path") or ""
        if exists_ok(prev_last) and (cur.get("chain_from_prev") or not exists_ok(cur_first)):
            if cur.get("first_frame_path") != prev_last:
                cur["first_frame_path"] = prev_last
                linked.append({"from": f"{prev['shot_id']}.last_frame_path",
                               "to": f"{cur['shot_id']}.first_frame_path", "path": prev_last})
        elif prev.get("generation_mode") == "first_last" and not exists_ok(prev_last) and exists_ok(cur_first):
            prev["last_frame_path"] = cur_first
            linked.append({"from": f"{cur['shot_id']}.first_frame_path",
                           "to": f"{prev['shot_id']}.last_frame_path", "path": cur_first})
    return linked


def shot_reference_paths(manifest: dict, shot: dict, proj_dir: Path = None, limit: int = 3,
                         include_env: bool = True) -> list:
    """Chọn danh sách ảnh tham chiếu tối ưu (Round-Robin) cho shot trong giới hạn slot của Flow/Veo.

    Thứ tự ưu tiên để không làm rớt nhân vật thứ 2 hoặc đạo cụ/bối cảnh:
    1. `shot.reference_images` (đạo diễn chỉ định cứng).
    2. Ảnh chính diện (`refs[0]`) của TỪNG nhân vật trong `shot.subjects` (khóa danh tính mọi người trong khung).
    3. Ảnh đạo cụ (`shot.props` hoặc đạo cụ khớp tên trong `action`).
    4. Ảnh góc thứ hai (`refs[1]`, thường là 3/4) của từng nhân vật theo vòng tròn.
    5. Ảnh bối cảnh sạch (`environment.path`) nếu `include_env=True`.
    6. Các ảnh nhân vật còn lại (`refs[2:]`).
    """
    chars = characters_by_id(manifest)
    envs = environments_by_id(manifest)
    props = props_by_id(manifest)

    def ok(rel_path: str) -> bool:
        if not rel_path:
            return False
        return True if proj_dir is None else (Path(proj_dir) / rel_path).exists()

    ordered = []

    def push(rel_path: str) -> None:
        if ok(rel_path) and rel_path not in ordered:
            ordered.append(rel_path)

    for p in shot.get("reference_images", []):
        push(p)

    subj_refs = []
    for cid in shot.get("subjects", []):
        c = chars.get(cid, {})
        valid = [p for p in c.get("reference_images", []) if ok(p)]
        if valid:
            subj_refs.append(valid)

    # Vòng 1: mỗi nhân vật xuất hiện trong cảnh đều có ít nhất 1 ảnh nhận dạng chính
    for refs in subj_refs:
        push(refs[0])

    # Vòng 2: đạo cụ khai báo trong shot.props hoặc khớp tên trong action
    shot_props = list(shot.get("props", []))
    action_lower = (shot.get("action") or "").lower()
    for pid, p_obj in props.items():
        pname = (p_obj.get("name") or "").lower()
        if pid in shot_props or (pname and pname in action_lower):
            push(p_obj.get("path", ""))

    # Vòng 3: góc thứ hai (three_quarter) của từng nhân vật
    for refs in subj_refs:
        if len(refs) > 1:
            push(refs[1])

    # Vòng 4: ảnh bối cảnh sạch (clean plate) để giữ liên tục không gian giữa các shot
    if include_env and shot.get("environment") in envs:
        push(envs[shot["environment"]].get("path", ""))

    # Vòng 5: các ảnh nhân vật còn lại (vd. expressions / profile)
    max_len = max((len(r) for r in subj_refs), default=0)
    for idx in range(2, max_len):
        for refs in subj_refs:
            if len(refs) > idx:
                push(refs[idx])

    return ordered[:limit] if limit else ordered


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
