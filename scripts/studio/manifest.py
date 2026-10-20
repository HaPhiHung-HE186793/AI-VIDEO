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
    """ID duy nhất cho Keyframe đầu/giữa/cuối của shot (vd: KF_PGMT_S01_START, KF_PGMT_S03A_END)."""
    import re

    pcode = project_code(manifest)
    m = re.search(r"(\d+)([a-zA-Z]*)$", str(shot_id))
    if m:
        scode = f"S{int(m.group(1)):02d}{m.group(2).upper()}"
    else:
        scode = re.sub(r"[^A-Z0-9]", "", str(shot_id).upper())[:6]
    s_lower = str(slot).lower()
    if s_lower in ("start", "first"):
        tag = "START"
    elif s_lower in ("end", "last"):
        tag = "END"
    else:
        tag = re.sub(r"[^A-Z0-9_]", "", str(slot).upper()) or "MID"
    return f"KF_{pcode}_{scode}_{tag}"


def keyframe_rel_path(manifest: dict, shot_id: str, slot: str = "start", ext: str = ".png") -> str:
    """Đường dẫn tương đối chuẩn có gắn Unique ID cho Keyframe của shot."""
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"assets/frames/{keyframe_uid(manifest, shot_id, slot)}{ext}"


def expand_shot_waypoints(manifest: dict) -> list:
    """Mở rộng các shot có khai báo `mid_action` / `mid_actions` (1 hoặc N frame trung gian) thành chuỗi Sub-Shots.

    - Một shot có `start_action`, `mid_actions: [M1, M2, ..., Mn]` và `end_action` sẽ có N+2 trạng thái Keyframe
      (F0 -> F1 -> F2 -> ... -> Fn+1) và được tách thành N+1 sub-shots (`shot_XXa`, `shot_XXb`, ...) nối Daisy-Chain.
    - Tất cả sub-shots đều đặt `anchor_frame_shot` trỏ về sub-shot đầu tiên (`shot_XXa`), giúp toàn bộ frame
      trung gian F1..Fn và frame cuối Fn+1 đều neo trực tiếp vào F0 (Star-Anchored) và tạo song song trong 1 đợt.
    """
    import copy

    shots = ordered_shots(manifest)
    if not any(s.get("mid_actions") or s.get("mid_action") for s in shots):
        return []

    expanded_log = []
    new_shots = []
    for s in shots:
        raw_mids = s.get("mid_actions")
        if not raw_mids and s.get("mid_action"):
            raw_mids = [s["mid_action"]]
        if not isinstance(raw_mids, list) or not raw_mids:
            new_shots.append(s)
            continue

        mids = []
        for item in raw_mids:
            if isinstance(item, dict) and (item.get("pose") or item.get("end_action") or item.get("action")):
                mids.append({
                    "pose": (item.get("pose") or item.get("end_action") or item.get("action")).strip(),
                    "action": (item.get("action") or "").strip(),
                    "props": item.get("props"),
                })
            elif isinstance(item, str) and item.strip():
                mids.append({"pose": item.strip(), "action": "", "props": None})
        if not mids:
            new_shots.append(s)
            continue

        base_id = s["shot_id"]
        start_pose = (s.get("start_action") or s.get("action") or "").strip()
        end_pose = (s.get("end_action") or s.get("action") or "").strip()
        states = [start_pose] + [m["pose"] for m in mids] + [end_pose]
        n_bridges = len(states) - 1
        root_sub_id = f"{base_id}a"
        sub_ids = []

        for idx in range(n_bridges):
            suffix = chr(ord("a") + idx) if idx < 26 else f"_{idx + 1}"
            sub_id = f"{base_id}{suffix}"
            sub_ids.append(sub_id)
            sub = copy.deepcopy(s)
            sub.pop("mid_actions", None)
            sub.pop("mid_action", None)
            sub.pop("takes", None)
            sub.pop("selected_take", None)
            sub.pop("auto_selection", None)
            sub.pop("edit_in", None)
            sub.pop("edit_out", None)
            sub.pop("qa", None)

            pose_a, pose_b = states[idx], states[idx + 1]
            custom_act = mids[idx]["action"] if idx < len(mids) and mids[idx]["action"] else ""
            bridge_action = custom_act or f"{pose_a.rstrip('.')} then smoothly transitions to: {pose_b.rstrip('.')}"

            sub["shot_id"] = sub_id
            sub["generation_mode"] = "first_last"
            sub["start_action"] = pose_a
            sub["end_action"] = pose_b
            sub["action"] = bridge_action
            sub["waypoint_parent"] = base_id
            sub["waypoint_index"] = idx + 1
            sub["waypoint_total"] = n_bridges
            sub["waypoint_subshot"] = True
            sub["anchor_frame_shot"] = root_sub_id
            sub["clip_output_path"] = f"assets/clips/{sub_id}.mp4"
            sub["status"] = STATUS_PENDING

            if idx < len(mids) and mids[idx].get("props"):
                sub["props"] = list(dict.fromkeys((sub.get("props") or []) + list(mids[idx]["props"])))

            if idx == 0:
                sub["chain_from_prev"] = bool(s.get("chain_from_prev"))
                sub["first_frame_path"] = s.get("first_frame_path") or keyframe_rel_path(manifest, sub_id, "start")
            else:
                sub["chain_from_prev"] = True
                prev_sub_id = sub_ids[idx - 1]
                sub["first_frame_path"] = keyframe_rel_path(manifest, prev_sub_id, "end")

            sub["last_frame_path"] = keyframe_rel_path(manifest, sub_id, "end")

            if idx < n_bridges - 1:
                sub["transition_to_next"] = "INTRA_SCENE_CONTINUE"
                sub["transition_out"] = "cut"
            else:
                if s.get("transition_to_next"):
                    sub["transition_to_next"] = s["transition_to_next"]
                else:
                    sub.pop("transition_to_next", None)
                sub["transition_out"] = s.get("transition_out", "cut")

            new_shots.append(sub)

        expanded_log.append({"parent": base_id, "waypoints": len(mids), "sub_shots": sub_ids})

    for order_idx, sh in enumerate(new_shots, start=1):
        sh["order"] = order_idx
    manifest["shots"] = new_shots
    return expanded_log


def root_anchor_frame_path(manifest: dict, shot: dict, proj_dir: Path = None) -> Path:
    """Tìm đường dẫn file ảnh Keyframe gốc (F0 - Star-Anchor) của một shot hoặc chuỗi Daisy-Chain / Waypoints.

    Giúp toàn bộ các frame trung gian (MID_01..MID_N) và frame END trong chuỗi nhiều shot đều lấy trực tiếp F0
    làm ảnh tham chiếu mỏ neo (tạo song song trong 1 đợt và không bị trôi nhân vật/bối cảnh).
    """
    shots = ordered_shots(manifest)
    by_id = {s["shot_id"]: s for s in shots}
    anchor_sid = shot.get("anchor_frame_shot")
    if anchor_sid and anchor_sid in by_id:
        rel = by_id[anchor_sid].get("first_frame_path") or ""
        if rel:
            return (Path(proj_dir) / rel) if proj_dir else Path(rel)

    # Nếu shot nối tiếp từ shot trước (chain_from_prev), lùi về đầu chuỗi để lấy F0 nếu first_frame_path chưa có.
    if shot.get("first_frame_path"):
        p = (Path(proj_dir) / shot["first_frame_path"]) if proj_dir else Path(shot["first_frame_path"])
        if proj_dir is None or p.exists():
            return p

    idx = next((i for i, x in enumerate(shots) if x["shot_id"] == shot.get("shot_id")), None)
    while idx is not None and idx > 0 and (shots[idx].get("chain_from_prev") or shots[idx - 1].get("transition_to_next") == "INTRA_SCENE_CONTINUE"):
        idx -= 1
        cand = shots[idx].get("first_frame_path") or ""
        if cand:
            cp = (Path(proj_dir) / cand) if proj_dir else Path(cand)
            if proj_dir is None or cp.exists():
                return cp
    if shot.get("first_frame_path"):
        return (Path(proj_dir) / shot["first_frame_path"]) if proj_dir else Path(shot["first_frame_path"])
    return None


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


def shot_all_cast_ids(shot: dict) -> list:
    """Trả về toàn bộ danh sách ID nhân vật có tên xuất hiện trong shot (không giới hạn số lượng 1..N).

    Gộp theo thứ tự ưu tiên:
    1. `shot.subjects` (nhân vật tiêu điểm / hành động chính).
    2. `shot.ensemble_cast` / `shot.table_group` / `shot.background_cast` (các nhân vật phụ có tên cùng ngồi bàn / cùng cảnh).
    """
    seen = []
    for key in ("subjects", "ensemble_cast", "table_group", "background_cast"):
        for cid in shot.get(key) or []:
            if cid and cid not in seen:
                seen.append(cid)
    return seen


def build_group_reference_sheet(manifest: dict, char_ids: list, proj_dir: Path) -> str:
    """Ghép ảnh chính diện của N nhân vật (4..20+ người) thành 1 bảng tham chiếu nhóm có nhãn tên & vị trí.

    Giúp vượt giới hạn 3–4 slot đính kèm ảnh của Google Flow: chỉ tốn 1 slot đính kèm nhưng Nano Banana / Veo
    nhìn thấy tạo hình chính xác của toàn bộ 10–20 nhân vật có tên trong bàn tiệc/cảnh nhóm.
    Trả về đường dẫn tương đối (`assets/characters/_composites/group_cast_<hash>.jpg`) hoặc chuỗi rỗng nếu thiếu ảnh.
    """
    if not proj_dir or len(char_ids) < 2:
        return ""
    chars = characters_by_id(manifest)
    entries = []
    for idx, cid in enumerate(char_ids, start=1):
        c = chars.get(cid, {})
        refs = [p for p in c.get("reference_images", []) if p and (Path(proj_dir) / p).exists()]
        if refs:
            label = c.get("short_name") or c.get("name") or cid
            entries.append((cid, f"#{idx} {label}", Path(proj_dir) / refs[0], refs[0]))
    if len(entries) < 2:
        return ""

    import hashlib
    import math

    sig = "|".join(f"{cid}:{rel}" for cid, _, _, rel in entries)
    digest = hashlib.sha1(sig.encode("utf-8")).hexdigest()[:10]
    rel_out = f"assets/characters/_composites/group_cast_{len(entries)}p_{digest}.jpg"
    out_path = Path(proj_dir) / rel_out
    if out_path.exists():
        return rel_out

    try:
        import cv2
        import numpy as np
    except Exception:  # noqa: BLE001
        return ""

    n = len(entries)
    cols = min(5, max(2, math.ceil(math.sqrt(n))))
    rows = math.ceil(n / cols)
    cell_w = max(240, min(480, 1920 // cols))
    cell_h = max(270, min(540, 1080 // rows))

    cells = []
    for _, _, img_path, _ in entries:
        im = cv2.imread(str(img_path))
        if im is None:
            continue
        h, w = im.shape[:2]
        scale = min(cell_w / max(w, 1), cell_h / max(h, 1))
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA)
        border_color = [int(x) for x in im[0, 0]] if h > 0 and w > 0 else [165, 165, 165]
        canvas = np.full((cell_h, cell_w, 3), border_color, dtype=np.uint8)
        y0 = (cell_h - nh) // 2
        x0 = (cell_w - nw) // 2
        canvas[y0:y0 + nh, x0:x0 + nw] = resized
        cells.append(canvas)

    if len(cells) < 2:
        return ""
    while len(cells) % cols != 0:
        cells.append(np.full((cell_h, cell_w, 3), 165, dtype=np.uint8))

    grid = np.vstack([np.hstack(cells[r * cols:(r + 1) * cols]) for r in range(rows)])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    return rel_out if out_path.exists() else ""


def shot_reference_paths(manifest: dict, shot: dict, proj_dir: Path = None, limit: int = 3,
                         include_env: bool = True) -> list:
    """Chọn danh sách ảnh tham chiếu tối ưu (Round-Robin + Auto Group Composite) cho shot.

    Thứ tự ưu tiên để không làm rớt bất kỳ nhân vật nào dù cảnh có 2 hay 20 nhân vật:
    1. `shot.reference_images` (đạo diễn chỉ định cứng).
    2. Nếu cảnh có nhiều nhân vật (>= 3 người có ảnh trên đĩa) khiến tổng số ảnh vượt `limit`:
       - Giữ ảnh riêng cho nhân vật tiêu điểm đầu tiên (`subjects[0]`).
       - Tự động ghép toàn bộ các nhân vật còn lại (hoặc cả nhóm 4..20+ người) thành 1 bảng `group_cast_<hash>.jpg`
         để chỉ tốn 1 slot nhưng AI thấy đủ mặt tất cả mọi người.
    3. Ảnh chính diện (`refs[0]`) của từng nhân vật trong `shot_all_cast_ids(shot)`.
    4. Ảnh đạo cụ (`shot.props` hoặc đạo cụ khớp tên trong `action`).
    5. Ảnh bối cảnh sạch (`environment.path`) nếu `include_env=True`.
    6. Ảnh góc thứ hai (`refs[1]`, thường là 3/4) và các góc còn lại của từng nhân vật.
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

    all_cast = shot_all_cast_ids(shot)
    subj_refs = []
    valid_cast_ids = []
    for cid in all_cast:
        c = chars.get(cid, {})
        valid = [p for p in c.get("reference_images", []) if ok(p)]
        if valid:
            subj_refs.append(valid)
            valid_cast_ids.append(cid)

    # Nếu số nhân vật có ảnh vượt quá slot cho phép (vd. cảnh nhóm 3..20 người), tự động ghép bảng Group Cast Sheet
    env_slot = 1 if (include_env and shot.get("environment") in envs and ok(envs[shot["environment"]].get("path", ""))) else 0
    if proj_dir is not None and limit and len(valid_cast_ids) + env_slot > limit and len(valid_cast_ids) >= 3:
        # Giữ slot 1 cho nhân vật chính đầu tiên, ghép toàn bộ nhóm vào bảng tổng hợp ở slot 2
        push(subj_refs[0][0])
        sheet_rel = build_group_reference_sheet(manifest, valid_cast_ids, Path(proj_dir))
        if sheet_rel:
            push(sheet_rel)

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
