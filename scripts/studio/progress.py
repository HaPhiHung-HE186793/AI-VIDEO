"""Bàn giao giữa các máy / phiên chat: `projects/<slug>/PROGRESS.md` + `projects/INDEX.md`.

Tự cập nhật sau MỌI lệnh sửa dự án. Phiên mới (máy khác) chỉ cần chạy `resume` hoặc đọc PROGRESS.md là biết:
đang ở bước nào, lệnh tiếp theo chính xác, job Flow đang tạo dở, file media nào máy này còn thiếu, quyết định đã chốt.

Đồng bộ: code + manifest + PROGRESS.md qua git; media (clip/âm thanh, nặng) qua thư mục chung `STUDIO_MEDIA_DIR`
(vd. Google Drive for desktop) bằng `media-push` / `media-pull`.
"""

import datetime as dt
import os
import socket
from pathlib import Path

from . import manifest as mf

LOG_KEEP = 40
ACTIVE_WARN_MIN = 45  # máy khác chạy lệnh trong vòng 45 phút → cảnh báo trùng phiên


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def machine(cfg: dict = None) -> str:
    host = socket.gethostname()
    names = (cfg or {}).get("machines", {})
    return os.environ.get("STUDIO_MACHINE") or names.get(host) or host


# ---------------------------------------------------------------- media mà manifest tham chiếu
def media_refs(proj: Path, m: dict) -> list:
    """[(đường dẫn tương đối, vai trò)] — mọi file nặng dự án cần để làm tiếp / dựng lại."""
    refs = []
    add = lambda p, role: p and refs.append((str(p).replace("\\", "/"), role))  # noqa: E731
    for s in mf.ordered_shots(m):
        if s.get("exclude_from_edit"):
            continue
        sid = s["shot_id"]
        add(s.get("first_frame_path"), f"{sid} frame đầu")
        add(s.get("last_frame_path"), f"{sid} frame cuối")
        sel = s.get("selected_take")
        for t in s.get("takes", []):
            if t.get("take") == sel:
                add(t.get("path"), f"{sid} take {sel} (720p)")
                add(t.get("path_1080"), f"{sid} take {sel} (1080p)")
        if s.get("clip_output_path"):
            add(s["clip_output_path"], f"{sid} clip dựng")
        add(s.get("voiceover_path"), f"{sid} lời dẫn")
    for b in m.get("beats", []):
        add(b.get("voiceover_path"), f"beat {b['beat_id']} lời dẫn")
    for c in m.get("characters", []):
        for r in c.get("reference_images", []):
            add(r if isinstance(r, str) else r.get("path"), f"ảnh tham chiếu {c.get('id')}")
    add(m.get("music_path"), "nhạc nền")
    add(m.get("lut_path"), "LUT màu")
    seen, out = set(), []
    for p, role in refs:
        if p not in seen:
            seen.add(p)
            out.append((p, role))
    return out


def missing_media(proj: Path, m: dict) -> list:
    return [(p, r) for p, r in media_refs(proj, m) if not (Path(proj) / p).exists()]


# ---------------------------------------------------------------- xác định bước hiện tại
def stage(proj: Path, m: dict) -> dict:
    """Bước tiếp theo của quy trình + lệnh chính xác. Trả {step, title, detail, commands, needs_user}."""
    slug = m.get("project_slug") or Path(proj).name
    cmd = lambda c, extra="": f"python scripts/studio_helper.py {c} --project {slug}{extra}"  # noqa: E731
    shots = [s for s in mf.ordered_shots(m) if not s.get("exclude_from_edit")]
    if not shots:
        return {"step": 1, "title": "Viết kịch bản & shot list", "needs_user": False,
                "detail": "Manifest chưa có shot.", "commands": ["(agent) viết beats + shots vào manifest", cmd("build-prompts")]}
    no_prompt = [s["shot_id"] for s in shots if not s.get("veo_prompt")]
    if no_prompt:
        return {"step": 2, "title": "Dựng prompt", "needs_user": False, "detail": f"Thiếu prompt: {', '.join(no_prompt)}",
                "commands": [cmd("build-prompts"), cmd("lint-prompts", " --strict")]}
    pending_jobs = [j for j in m.get("flow_jobs", []) if not j.get("harvested")]
    if pending_jobs:
        kinds = sorted({j["kind"] for j in pending_jobs})
        shots_s = ", ".join(sorted({j["shot"] for j in pending_jobs}))
        return {"step": 5, "title": "Tải kết quả Flow đang tạo dở", "needs_user": False,
                "detail": f"Đã gửi tạo nhưng CHƯA tải về: {shots_s} ({', '.join(kinds)}). Kết quả nằm sẵn trên Flow "
                          f"(cùng tài khoản Google) — KHÔNG gửi tạo lại (mất credit).",
                "commands": [cmd("flow-harvest", f" --kind {k} --wait") for k in kinds]}
    need_frame = [s["shot_id"] for s in shots if s.get("generation_mode") in ("first_frame", "first_last")
                  and not s.get("takes") and not s.get("first_frame_path")]
    if need_frame:
        return {"step": 4, "title": "Tạo frame mở đầu (Nano Banana, 0 credit)", "needs_user": False,
                "detail": f"Shot chưa có frame: {', '.join(need_frame)}",
                "commands": [cmd("flow-generate", " --kind frames --count 2"), cmd("flow-harvest", " --kind image --wait")]}
    no_takes = [s["shot_id"] for s in shots if not s.get("takes")]
    approval = (m.get("storyboard") or {}).get("approved_hash")
    if no_takes:
        from . import storyboard

        st = storyboard.approval_state(m)
        if not st.get("valid"):
            return {"step": 4, "title": "🧑 Chờ người dùng duyệt storyboard", "needs_user": True,
                    "detail": f"{len(no_takes)} shot chưa có video. Storyboard {'chưa duyệt' if not approval else 'đã sửa sau khi duyệt'}.",
                    "commands": [cmd("storyboard"), "(người dùng xem output/storyboard.html)", cmd("storyboard-approve", ' --by "<tên>"')]}
        return {"step": 5, "title": "Tạo video (tốn credit Flow — báo người dùng trước)", "needs_user": True,
                "detail": f"Shot chưa có video: {', '.join(no_takes)}",
                "commands": [cmd("flow-generate", " --kind video --count 2 --dry-run"), cmd("flow-generate", " --kind video --count 2"),
                             cmd("flow-harvest", " --kind video --wait")]}
    unreviewed = [f"{s['shot_id']}#{t['take']}" for s in shots for t in s.get("takes", [])
                  if not (t.get("qa") or {}).get("vision") and not s.get("selected_take")]
    if unreviewed:
        return {"step": 6, "title": "QA từng take", "needs_user": False, "detail": f"Take chưa chấm: {', '.join(unreviewed[:12])}",
                "commands": [cmd("qa-takes"), "(agent xem sheet, ghi JSON)", cmd("qa-takes-submit"), cmd("auto-select")]}
    retake = [s["shot_id"] for s in shots if s.get("status") == "needs_retake"]
    if retake:
        return {"step": 6, "title": "Tạo lại shot lỗi (tốn credit — báo người dùng)", "needs_user": True,
                "detail": f"needs_retake: {', '.join(retake)} — sửa prompt theo retake_reasons trước.",
                "commands": [cmd("build-prompts"), cmd("flow-generate", " --kind video --retakes --count 2")]}
    unselected = [s["shot_id"] for s in shots if not s.get("selected_take")]
    if unselected:
        return {"step": 6, "title": "Chọn take", "needs_user": False, "detail": f"Chưa chọn take: {', '.join(unselected)}",
                "commands": [cmd("auto-select")]}
    no_1080 = [s["shot_id"] for s in shots
               if not any(t.get("path_1080") for t in s.get("takes", []) if t.get("take") == s.get("selected_take"))]
    if no_1080:
        return {"step": 7, "title": "Upscale 1080p", "needs_user": False, "detail": f"Còn 720p: {', '.join(no_1080)}",
                "commands": [cmd("flow-upscale", f" --shots {','.join(no_1080)}")]}
    no_vo = [b["beat_id"] for b in m.get("beats", []) if b.get("narration") and not b.get("voiceover_path")]
    if no_vo:
        return {"step": 8, "title": "Lời dẫn (TTS miễn phí)", "needs_user": False, "detail": f"Beat chưa có lời: {', '.join(no_vo)}",
                "commands": [cmd("voiceover")]}
    out_dir = Path(proj) / "output"
    vids = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime) if out_dir.exists() else []
    # Lệnh đổi nội dung phim sau lần dựng cuối → bản xuất đã cũ (bỏ qua lệnh chỉ ghi chú / đồng bộ / xuất phụ).
    passive = {"note", "progress", "media-push", "media-pull", "publish-kit", "thumbnail", "assemble", "storyboard",
               "storyboard-approve", "qa", "qa-takes", "status"}
    changed = [e["at"] for e in m.get("session_log", []) if e.get("ok") and e["command"] not in passive]
    man_time = dt.datetime.fromisoformat(changed[-1]).timestamp() if changed else 0
    pub = m.get("publish") or {}
    final = Path(proj) / pub["video_landscape"] if pub.get("video_landscape") else (vids[-1] if vids else None)
    if not final or not final.exists():
        return {"step": 9, "title": "Dựng bản cuối", "needs_user": False, "detail": "Chưa có video xuất.",
                "commands": [cmd("score"), cmd("assemble", " --format landscape"), cmd("assemble", " --format vertical --burn-subs")]}
    if not pub:
        return {"step": 10, "title": "Bộ đăng kênh", "needs_user": False, "detail": f"Đã có {final.name}.",
                "commands": ["(agent) viết manifest.publish", cmd("thumbnail"), cmd("publish-kit")]}
    return {"step": 11, "title": "Xong — chờ người dùng đăng / yêu cầu mới", "needs_user": True,
            "detail": f"Bản cuối: {Path(final).relative_to(proj).as_posix() if Path(final).is_absolute() else final}"
                      + (" (manifest sửa sau lần dựng cuối → nên dựng lại)" if final.stat().st_mtime < man_time - 5 else ""),
            "commands": [cmd("publish-kit")]}


# ---------------------------------------------------------------- nhật ký & ghi chú
def log_command(m: dict, command: str, argv: list, cfg: dict, ok: bool = True, error: str = "") -> None:
    entry = {"at": now(), "machine": machine(cfg), "command": command,
             "args": " ".join(a for a in argv if a not in ("--project",) and not a.endswith(m.get("project_slug", "\0")))[:160],
             "ok": ok}
    if command == "note":
        entry["args"] = ""  # nội dung đã nằm ở mục ghi chú — không lặp lại trong nhật ký
    if error:
        entry["error"] = error[:300]
    log = m.setdefault("session_log", [])
    log.append(entry)
    del log[:-LOG_KEEP]
    m["last_activity"] = {"at": entry["at"], "machine": entry["machine"], "command": command}


def add_note(m: dict, text: str, cfg: dict, kind: str = "note") -> dict:
    note = {"at": now(), "machine": machine(cfg), "kind": kind, "text": text.strip()}
    m.setdefault("handoff_notes", []).append(note)
    return note


def other_machine_active(m: dict, cfg: dict) -> dict:
    last = m.get("last_activity") or {}
    if not last or last.get("machine") == machine(cfg):
        return {}
    try:
        age = (dt.datetime.now() - dt.datetime.fromisoformat(last["at"])).total_seconds() / 60
    except (KeyError, ValueError):
        return {}
    return {**last, "minutes_ago": round(age)} if age < ACTIVE_WARN_MIN else {}


# ---------------------------------------------------------------- xuất markdown
def render(proj: Path, m: dict, cfg: dict) -> str:
    slug = m.get("project_slug") or Path(proj).name
    st = stage(proj, m)
    shots = [s for s in mf.ordered_shots(m) if not s.get("exclude_from_edit")]
    miss = missing_media(proj, m)
    last = m.get("last_activity") or {}
    L = [f"# Tiến độ: {m.get('project_name') or slug}", "",
         "> File này **tự sinh** sau mỗi lệnh (`progress.py`). Đừng sửa tay — thêm ghi chú bằng "
         f"`python scripts/studio_helper.py note --project {slug} \"...\"`.", "",
         "## Bắt đầu phiên trên máy khác", "",
         "```powershell",
         "git pull",
         f"python scripts/studio_helper.py media-pull --project {slug}   # lấy clip/âm thanh từ thư mục chung (STUDIO_MEDIA_DIR)",
         f"python scripts/studio_helper.py resume --project {slug}       # kiểm tra máy + in bước tiếp theo",
         "```", "",
         "Bước Flow (tạo / tải / upscale) mở đúng dự án Flow bên dưới — Chrome điều khiển của máy này (`check-browser`) "
         "phải đăng nhập **cùng tài khoản Google** (lần đầu trên máy mới: đăng nhập 1 lần, profile được giữ lại).", "",
         "Kết thúc phiên: `media-push` rồi `git add -A && git commit && git push` (quy tắc 9).", "",
         "## Trạng thái", "",
         f"- **Slug:** `{slug}` — thư mục `projects/{slug}/` (KHÔNG `init` dự án mới)",
         f"- **Flow:** {m.get('flow_project_url') or '(chưa có — sẽ tạo khi flow-generate --new-project)'}",
         f"- **Ngôn ngữ / khung:** {m.get('language', '?')} / {m.get('aspect_ratio', '16:9')}; giọng dẫn `{m.get('narrator_voice', '-')}`"
         + (f", TTS `{m['voiceover_model']}`" if m.get("voiceover_model") else ""),
         f"- **Cập nhật lần cuối:** {last.get('at', '?')} trên máy **{last.get('machine', '?')}** (lệnh `{last.get('command', '?')}`)",
         f"- **Storyboard:** {_approval_text(m)}", "",
         f"## ▶ Bước tiếp theo: {st['step']}. {st['title']}", "", st["detail"], "", "```powershell", *st["commands"], "```", ""]
    pending = [j for j in m.get("flow_jobs", []) if not j.get("harvested")]
    if pending:
        L += ["### ⚠ Job Flow đang tạo dở (đã tiêu credit, chưa tải)", "", "| Shot | Loại | Model | Số bản | Credit | Gửi lúc |", "|---|---|---|---|---|---|"]
        L += [f"| {j['shot']} | {j['kind']} | {j.get('model', '')} | {j.get('count', '')} | {j.get('credits', 0)} | {j.get('at', '')} |" for j in pending]
        L += [""]
    L += ["## Shot", "", "| # | Shot | Beat | Trạng thái | Take chọn | 1080p | Cắt |", "|---|---|---|---|---|---|---|"]
    for i, s in enumerate(shots, 1):
        sel = s.get("selected_take")
        t = next((x for x in s.get("takes", []) if x.get("take") == sel), {})
        cut = f"{s['edit_in']:.2f}–{s['edit_out']:.2f}" if "edit_in" in s and "edit_out" in s else ""
        L.append(f"| {i} | {s['shot_id']} | {s.get('beat', '')} | {s.get('status', 'pending')} | "
                 f"{sel or '-'} / {len(s.get('takes', []))} | {'✓' if t.get('path_1080') else ''} | {cut} |")
    L += [""]
    if m.get("beats"):
        L += ["## Beat & lời dẫn", ""]
        for b in sorted(m["beats"], key=lambda b: b.get("order", 0)):
            L.append(f"- **{b['beat_id']}** ({b.get('purpose', '')}) {'🔊' if b.get('voiceover_path') else '—'} {b.get('narration', '')}")
        L += [""]
    out_dir = Path(proj) / "output"
    vids = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:6] if out_dir.exists() else []
    if vids:
        L += ["## Đầu ra gần nhất", ""] + [f"- `output/{v.name}` ({dt.datetime.fromtimestamp(v.stat().st_mtime):%Y-%m-%d %H:%M})" for v in vids] + [""]
    L += ["## Media trên máy này", ""]
    total = len(media_refs(proj, m))
    if miss:
        L += [f"⚠ Máy **{machine(cfg)}** thiếu {len(miss)}/{total} file — chạy `media-pull` (hoặc tải lại take từ Flow).", ""]
        L += [f"- `{p}` — {r}" for p, r in miss[:25]] + ([f"- … và {len(miss) - 25} file khác"] if len(miss) > 25 else []) + [""]
    else:
        L += [f"Đủ {total}/{total} file media trên máy **{machine(cfg)}**.", ""]
    notes = m.get("handoff_notes", [])
    if notes:
        L += ["## Quyết định & ghi chú bàn giao", ""]
        L += [f"- {n['at'][:16].replace('T', ' ')} · {n['machine']}{' · ' + n['kind'] if n.get('kind') != 'note' else ''}: {n['text']}"
              for n in notes[-20:]] + [""]
    log = m.get("session_log", [])
    if log:
        L += ["## Nhật ký lệnh (mới nhất trước)", "", "| Lúc | Máy | Lệnh | Kết quả |", "|---|---|---|---|"]
        L += [f"| {e['at'][5:16].replace('T', ' ')} | {e['machine']} | `{e['command']} {e.get('args', '')}`".rstrip() + f" | {'ok' if e.get('ok') else '❌ ' + e.get('error', '')[:80]} |"
              for e in reversed(log[-15:])] + [""]
    return "\n".join(L)


def _approval_text(m: dict) -> str:
    try:
        from . import storyboard

        st = storyboard.approval_state(m)
    except Exception:  # noqa: BLE001
        return "?"
    if st.get("valid"):
        return f"đã duyệt ({st.get('approved_hash')})"
    return "chưa duyệt" if not st.get("approved_hash") else f"đã sửa sau khi duyệt (cần duyệt lại: {st.get('current_hash')})"


def write(proj: Path, m: dict, cfg: dict) -> Path:
    p = Path(proj) / "PROGRESS.md"
    p.write_text(render(proj, m, cfg), encoding="utf-8")
    write_index(Path(proj).parent, cfg)
    return p


def write_index(projects_dir: Path, cfg: dict) -> Path:
    rows = []
    for mp in sorted(projects_dir.glob("*/project_manifest.json")):
        try:
            m = mf.load(mp.parent)
            st = stage(mp.parent, m)
        except Exception as e:  # noqa: BLE001
            rows.append((mp.parent.name, f"lỗi đọc: {e}", "", ""))
            continue
        last = m.get("last_activity") or {}
        rows.append((mp.parent.name, f"{st['step']}. {st['title']}", last.get("at", "")[:16].replace("T", " "), last.get("machine", "")))
    rows.sort(key=lambda r: r[2], reverse=True)
    L = ["# Dự án", "", "Tự sinh. Dự án đang làm dở: mở `projects/<slug>/PROGRESS.md` hoặc chạy `resume`.", "",
         "| Dự án | Bước tiếp theo | Hoạt động cuối | Máy |", "|---|---|---|---|"]
    L += [f"| [{r[0]}]({r[0]}/PROGRESS.md) | {r[1]} | {r[2]} | {r[3]} |" for r in rows]
    p = projects_dir / "INDEX.md"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- đồng bộ media qua thư mục chung
def media_dir(cfg: dict, slug: str) -> Path:
    root = os.environ.get("STUDIO_MEDIA_DIR") or (cfg.get("sync") or {}).get("media_dir")
    return Path(os.path.expanduser(root)) / slug if root else None


def sync_media(proj: Path, m: dict, cfg: dict, direction: str, everything: bool = False) -> dict:
    """push: máy này → thư mục chung; pull: thư mục chung → máy này. Chỉ chép file thiếu hoặc khác kích thước/mới hơn."""
    import shutil

    slug = m.get("project_slug") or Path(proj).name
    shared = media_dir(cfg, slug)
    if not shared:
        raise mf.ManifestError("Chưa đặt thư mục chung: thêm STUDIO_MEDIA_DIR=<đường dẫn> vào .env của máy này "
                               "(vd. G:/My Drive/AI-video-media khi dùng Google Drive for desktop).")
    if everything:
        rels = sorted({p.relative_to(proj).as_posix() for p in Path(proj).rglob("*") if p.is_file()
                       and p.suffix.lower() in (".mp4", ".wav", ".mp3", ".jpg", ".png", ".cube")
                       and "/qa/" not in p.as_posix() and "_incoming" not in p.as_posix()})
    else:
        rels = [p for p, _ in media_refs(proj, m)]
        out_dir = Path(proj) / "output"
        if out_dir.exists():
            rels += [p.relative_to(proj).as_posix() for p in out_dir.iterdir() if p.suffix.lower() in (".mp4", ".srt", ".jpg")]
    copied, missing = [], []
    for rel_path in dict.fromkeys(rels):
        a, b = (Path(proj) / rel_path, shared / rel_path) if direction == "push" else (shared / rel_path, Path(proj) / rel_path)
        if not a.exists():
            if not b.exists():
                missing.append(rel_path)
            continue
        if b.exists() and b.stat().st_size == a.stat().st_size and b.stat().st_mtime >= a.stat().st_mtime - 2:
            continue
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a, b)
        copied.append(rel_path)
    return {"direction": direction, "shared_dir": str(shared), "copied": len(copied), "copied_files": copied[:50],
            "missing_everywhere": missing}
