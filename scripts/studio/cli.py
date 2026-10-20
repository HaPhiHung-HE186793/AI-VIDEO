"""CLI của AI Video Studio. Chạy: python scripts/studio_helper.py <lệnh> --help"""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import __version__
from . import assets as asset_tpl
from . import beats as bt
from . import audio as au
from . import manifest as mf
from . import media, prompts, qa, render, storyboard, takes, timeline
from .config import PROJECTS_DIR, load_config

LEGACY_DERIVED_FIELDS = (
    "end_frame_parking_policy", "start_frame_chaining_policy", "speech_start_sec", "speech_end_sec",
    "articulation_start_sec", "mid_speech_parking_detected", "mid_speech_parking_windows", "early_stasis_start_sec",
    "cgi_pop_in_detected", "cgi_pop_in_windows", "treadmill_stepping_detected", "in_shot_morphing_or_flip_reasons",
    "v9_qa_gate_status", "trim_start_sec", "trim_end_sec", "video_trim_start_sec", "video_trim_end_sec",
    "intra_scene_boundary_l1_diff", "editorial_transition_class", "transition_effect", "transition_duration_sec",
    "audit_passes_completed", "complexity_score", "complexity_reasons", "recommended_veo_model", "estimated_token_cost",
    "word_count", "start_sec", "end_sec", "duration_sec",
)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def proj_dir_of(args) -> Path:
    p = Path(args.project)
    if not p.exists() and (PROJECTS_DIR / args.project).exists():
        p = PROJECTS_DIR / args.project
    return p.resolve()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return slug or f"video-{datetime.now():%Y%m%d-%H%M%S}"


def rel(proj: Path, p: Path) -> str:
    return Path(p).resolve().relative_to(proj).as_posix()


# ---------------------------------------------------------------- plan / init

def calc_plan(duration: int, lang: str, avg_shot: float, cfg: dict, quality_share: float = 0.6) -> dict:
    """Số clip cần tạo dựa trên độ dài shot SAU DỰNG (không phải 8s/clip)."""
    lang = prompts.normalize_lang(lang)
    clips = max(1, math.ceil(duration / avg_shot))
    takes = cfg["credits"]["takes_per_shot"]
    q, f = cfg["models"]["video"]["quality"]["credits"], cfg["models"]["video"]["fast"]["credits"]
    per_clip = quality_share * q + (1 - quality_share) * f
    credits = round(clips * takes * per_clip)
    rates = prompts.LANGUAGE_RATES[lang]
    return {
        "target_duration_sec": duration,
        "avg_edited_shot_sec": avg_shot,
        "clips_to_generate": clips,
        "takes_per_clip": takes,
        "estimated_credits": credits,
        "credit_budget": cfg["credits"]["budget"],
        "budget_ok": credits <= cfg["credits"]["budget"],
        "language_code": lang,
        "max_speech_units_per_8s_clip": rates["rec_max_per_8s"],
        "speech_unit": rates["unit"],
        "note": "Mỗi clip Veo 8s được dựng còn ~avg_edited_shot_sec giây. Lời dẫn dài → dùng voiceover_external.",
    }


def cmd_plan(args, cfg):
    out(calc_plan(args.duration, args.lang, args.avg_shot, cfg))


def new_shot(i: int, n: int, audio_mode: str, manifest: dict = None) -> dict:
    sid = f"shot_{i:04d}" if n >= 100 else f"shot_{i:02d}"
    ff_path = mf.keyframe_rel_path(manifest, sid, "start") if manifest else f"assets/frames/{sid}_start.png"
    return {
        "shot_id": sid, "scene_id": f"scene_{i:02d}", "order": i,
        "camera": "", "subjects": [], "action": "", "environment": "", "setting": "", "lighting": "",
        "audio": {"mode": audio_mode, "line": "", "speaker": "", "delivery": "", "sfx": ""},
        "generation_mode": "first_frame", "first_frame_prompt": "", "first_frame_path": ff_path,
        "last_frame_prompt": "", "last_frame_path": "", "reference_images": [], "negative_prompt": "",
        "transition_to_next": "INTER_SCENE_CUT", "transition_out": "cut",
        "veo_prompt": "", "clip_output_path": f"assets/clips/{sid}.mp4", "status": mf.STATUS_PENDING, "takes": [],
    }


def cmd_init(args, cfg):
    slug = slugify(args.name)
    proj = PROJECTS_DIR / slug
    if (proj / "project_manifest.json").exists():
        sys.exit(f"[ERROR] Dự án {slug} đã tồn tại.")
    for sub in ("characters", "environments", "props", "frames", "clips/takes", "audio/vo", "audio/music", "qa"):
        (proj / "assets" / sub).mkdir(parents=True, exist_ok=True)
    (proj / "output").mkdir(exist_ok=True)
    avg = args.avg_shot or (3.5 if args.aspect == "9:16" else 5.0)
    plan = calc_plan(args.duration, args.lang, avg, cfg)
    n = plan["clips_to_generate"]
    manifest = {
        "schema_version": mf.SCHEMA_VERSION,
        "project_name": args.name, "project_slug": slug, "created_at": datetime.now().isoformat(timespec="seconds"),
        "language": plan["language_code"], "aspect_ratio": args.aspect,
        "delivery_formats": ["vertical"] if args.aspect == "9:16" else ["landscape"],
        "visual_style": args.style, "style_line": args.style, "negative_prompt": "",
        "audio_strategy": args.audio,
        "plan": plan, "characters": [], "environments": [], "props": [],
    }
    manifest["shots"] = [new_shot(i, n, args.audio, manifest) for i in range(1, n + 1)]
    mf.save(proj, manifest)
    out({"status": "ok", "project": str(proj), "clips": n, "plan": plan})


# ---------------------------------------------------------------- migrate

def _guess_audio(shot: dict) -> dict:
    vp = (shot.get("veo_prompt") or "").lower()
    line = shot.get("dialogue_text", "")
    if not line:
        return {"mode": "sfx_only"}
    if "narrator" in vp or "voiceover" in vp:
        return {"mode": "veo_narration", "line": line}
    return {"mode": "veo_dialogue", "line": line, "speaker": shot.get("active_speaker", "")}


def cmd_migrate(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    report = {"project": m.get("project_slug", proj.name), "from_schema": m.get("schema_version", 1), "changes": []}
    m["schema_version"] = mf.SCHEMA_VERSION
    plan = m.get("plan", {})
    m.setdefault("language", plan.get("language_code", "vi"))
    m.setdefault("style_line", m.get("visual_style", ""))
    m.setdefault("negative_prompt", "")
    m.setdefault("delivery_formats", ["vertical"] if m.get("aspect_ratio") == "9:16" else ["landscape"])
    m.pop("prompt_audit_summary", None)

    for c in m.get("characters", []):
        refs = c.setdefault("reference_images", [])
        cands = [c.get(k) for k in ("turnaround_path", "articulation_path", "scale_path")]
        cands.append(f"assets/characters/{c['id']}.png")
        for p in cands:
            if p and (proj / p).exists() and p not in refs:
                refs.append(p)
        c.setdefault("identity_line", "")

    for s in m.get("shots", []):
        sid = s.get("shot_id")
        if "audio" not in s:
            s["audio"] = _guess_audio(s)
        if s.get("ingredients_used") and not s.get("subjects"):
            chars = mf.characters_by_id(m)
            s["subjects"] = [x for x in s["ingredients_used"] if x in chars]
            envs = [x for x in s["ingredients_used"] if x in mf.environments_by_id(m)]
            if envs:
                s.setdefault("environment", envs[0])
        if s.get("camera_shot") and not s.get("camera"):
            s["camera"] = s["camera_shot"]
        mode = s.get("generation_mode") or s.get("continuity_mode") or ""
        if mode not in prompts.GENERATION_MODES:
            if "ingredient" in mode:
                s["generation_mode"] = "ingredients"
            elif s.get("first_frame_path") and (proj / s["first_frame_path"]).exists():
                s["generation_mode"] = "first_frame"
            else:
                s["generation_mode"] = "ingredients" if s.get("subjects") else "text"
        s.pop("continuity_mode", None)

        vp = s.get("veo_prompt") or ""
        cleaned, n = prompts.clean_legacy_prompt(vp)
        if n:
            s.setdefault("veo_prompt_legacy", vp)
            s["veo_prompt"] = cleaned
            report["changes"].append(f"{sid}: gỡ {n} đoạn boilerplate ({len(vp)}→{len(cleaned)} ký tự)")

        dropped = [k for k in LEGACY_DERIVED_FIELDS if k in s]
        for k in dropped:
            s.pop(k)
        s.setdefault("transition_out", "cut")
        s.setdefault("takes", [])

        clip = mf.clip_path(proj, s)
        if clip.exists() and not s["takes"]:
            s["takes"].append({"take": 1, "path": rel(proj, clip), "sha256": media.sha256_file(clip),
                               "registered_at": datetime.now().isoformat(timespec="seconds"),
                               "generation_mode": "unknown", "note": "nhập từ dự án cũ — không rõ input đã dùng"})
            s["selected_take"] = 1
            s["status"] = mf.STATUS_RENDERED
            report["changes"].append(f"{sid}: đăng ký clip hiện có làm take 1 (status=rendered)")
    mf.save(proj, m)
    out(report)


# ---------------------------------------------------------------- assets

def cmd_forge_assets(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj) if mf.manifest_path(proj).exists() else {}
    style = args.style or m.get("style_line") or m.get("visual_style") or "cinematic photorealistic"
    result = {}
    if args.char_name:
        cid = args.char_id or "CHAR_" + slugify(args.char_name).upper().replace("-", "_")
        result["character"] = asset_tpl.character_pack(cid, args.char_name, args.char_desc or args.char_name, style, args.char_type)
        if args.char_voice:
            result["character"]["voice"] = args.char_voice
    if args.env_name:
        eid = args.env_id or "ENV_" + slugify(args.env_name).upper().replace("-", "_")
        result["environment"] = asset_tpl.environment_plate(eid, args.env_name, args.env_desc or args.env_name, style)
    props = []
    for item in [p.strip() for p in (args.props or "").split(",") if p.strip()]:
        name, _, size = item.partition("@")
        pid = "PROP_" + slugify(name).upper().replace("-", "_")
        props.append(asset_tpl.prop_sheet(pid, name.strip(), size.strip(), style))
    if props:
        result["props"] = props

    if args.apply_to_manifest and m:
        def upsert(key, item):
            lst = m.setdefault(key, [])
            for i, x in enumerate(lst):
                if x.get("id") == item["id"]:
                    lst[i] = {**x, **item}
                    return
            lst.append(item)
        if "character" in result:
            upsert("characters", result["character"])
        if "environment" in result:
            upsert("environments", result["environment"])
        for p in props:
            upsert("props", p)
        mf.save(proj, m)
        result["applied_to_manifest"] = True
    out(result)


def cmd_audit_assets(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    issues, warnings, images = [], [], []
    for c in m.get("characters", []):
        cid = c["id"]
        if not c.get("identity_line"):
            issues.append(f"[{cid}] Thiếu identity_line (mô tả chuẩn dán nguyên văn vào mọi prompt).")
        refs = [p for p in c.get("reference_images", []) if (proj / p).exists()]
        missing = [p for p in c.get("reference_images", []) if not (proj / p).exists()]
        if not refs:
            issues.append(f"[{cid}] Chưa có ảnh tham chiếu nào trên đĩa → không khóa được danh tính trong Veo.")
        elif len(refs) < 2:
            warnings.append(f"[{cid}] Chỉ có {len(refs)} ảnh tham chiếu; nên có 2–3 góc (chính diện, 3/4, nghiêng).")
        if missing:
            warnings.append(f"[{cid}] Ảnh tham chiếu khai báo nhưng chưa có: {missing}")
        images += [(f"{cid}:{Path(p).stem}", proj / p) for p in refs]
    for e in m.get("environments", []):
        p = proj / e.get("path", f"assets/environments/{e['id']}.png")
        if p.exists():
            images.append((e["id"], p))
        else:
            warnings.append(f"[{e['id']}] Chưa có ảnh bối cảnh {p.name}.")
    for p in m.get("props", []):
        pp = proj / p.get("path", "")
        if pp.is_file():
            images.append((p["id"], pp))

    sheet = ""
    if images:
        import numpy as np

        cv2 = media.cv2_module()
        cells = []
        for label, path in images[:12]:
            im = cv2.imread(str(path))
            if im is None:
                continue
            im = cv2.resize(im, (480, int(480 * im.shape[0] / im.shape[1])))
            im = cv2.copyMakeBorder(im, 0, max(0, 360 - im.shape[0]), 0, 0, cv2.BORDER_CONSTANT)[:360]
            cv2.rectangle(im, (6, 6), (20 + 10 * len(label[:40]), 34), (0, 0, 0), -1)
            cv2.putText(im, label[:40], (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cells.append(im)
        while len(cells) % 3:
            cells.append(np.zeros_like(cells[0]))
        grid = np.vstack([np.hstack(cells[i:i + 3]) for i in range(0, len(cells), 3)])
        path = proj / "assets" / "qa" / "preprod_assets_qa_grid.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), grid, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        sheet = str(path)
    out({"status": "PASS" if not issues else "ACTION_REQUIRED", "issues": issues, "warnings": warnings, "contact_sheet": sheet})
    if issues:
        sys.exit(2)


# ---------------------------------------------------------------- prompts

def cmd_build_prompts(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    built, built_frames, skipped = [], [], []
    sheet = [f"# Bảng prompt cho Google Flow — {m.get('project_name', proj.name)}", "",
             f"Tạo lúc {datetime.now():%Y-%m-%d %H:%M}. Mỗi shot: chọn chế độ, đính kèm đúng input, dán prompt.", ""]
    shots = mf.ordered_shots(m)
    for idx, s in enumerate(shots):
        if prompts.is_structured(s):
            s["veo_prompt"] = prompts.build_prompt(m, s)
            built.append(s["shot_id"])
            mode = s.get("generation_mode") or "text"
            if mode in ("first_frame", "first_last"):
                s["first_frame_prompt"] = prompts.build_first_frame_prompt(m, s)
                built_frames.append(f"{s['shot_id']}:start")
                if not s.get("first_frame_path"):
                    s["first_frame_path"] = mf.keyframe_rel_path(m, s["shot_id"], "start")
            if mode == "first_last" or s.get("end_action"):
                s["last_frame_prompt"] = prompts.build_last_frame_prompt(m, s)
                built_frames.append(f"{s['shot_id']}:end")
                if mode == "first_last" and not s.get("last_frame_path"):
                    s["last_frame_path"] = mf.keyframe_rel_path(m, s["shot_id"], "end")
        elif not s.get("veo_prompt"):
            skipped.append(s["shot_id"])
            continue
    chained = mf.resolve_chained_keyframes(m)
    for idx, s in enumerate(shots):
        if not s.get("veo_prompt"):
            continue
        score, reasons = prompts.complexity_score(s, idx, len(shots))
        route = prompts.route_model(score, cfg)
        s["routing"] = {"complexity": score, "reasons": reasons, **route}
        neg = prompts.effective_negative_prompt(m, s)
        inputs = []
        if s.get("generation_mode") in ("first_frame", "first_last") and s.get("first_frame_path"):
            inputs.append(f"First frame (`{mf.keyframe_uid(m, s['shot_id'], 'start')}`): `{s['first_frame_path']}`")
        if s.get("generation_mode") == "first_last" and s.get("last_frame_path"):
            inputs.append(f"Last frame (`{mf.keyframe_uid(m, s['shot_id'], 'end')}`): `{s['last_frame_path']}`")
        if s.get("generation_mode") == "ingredients":
            refs = mf.shot_reference_paths(m, s, proj_dir=proj if (proj / "assets").exists() else None, limit=3)
            inputs += [f"Ingredient: `{r}`" for r in refs]
        if s.get("generation_mode") == "extend":
            inputs.append(f"Extend từ clip của `{s.get('extends')}`")
        voice = prompts.shot_voice(m, s)
        if voice and mf.shot_audio(s)["mode"] in ("veo_dialogue", "veo_narration"):
            inputs.append(f"Giọng nói: **{voice}** (Flow → Giọng nói → {voice} → Thêm vào câu lệnh)")
        sheet += [f"## {s['shot_id']} — {route['label']} (độ khó {score}/10)", "",
                  f"- Chế độ: **{s.get('generation_mode', 'text')}**",
                  *[f"- {x}" for x in inputs],
                  "", "```text", s["veo_prompt"], "```", ""]
        if s.get("first_frame_prompt"):
            sheet += [f"Keyframe START (`{mf.keyframe_uid(m, s['shot_id'], 'start')}`):", "", "```text", s["first_frame_prompt"], "```", ""]
        if s.get("last_frame_prompt"):
            sheet += [f"Keyframe END (`{mf.keyframe_uid(m, s['shot_id'], 'end')}` — đính kèm START frame làm chuẩn):", "", "```text", s["last_frame_prompt"], "```", ""]
        if neg:
            sheet += ["Negative prompt (nếu chế độ hỗ trợ):", "", "```text", neg, "```", ""]
    (proj / "prompts_for_flow.md").write_text("\n".join(sheet), encoding="utf-8")
    mf.save(proj, m)
    out({"status": "ok", "built_from_structured_fields": built, "built_keyframe_prompts": built_frames,
         "chained_keyframes": chained, "skipped_no_prompt": skipped,
         "flow_sheet": str(proj / "prompts_for_flow.md")})


def cmd_lint_prompts(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    shots = [s for s in mf.ordered_shots(m) if s.get("veo_prompt") or prompts.is_structured(s)]
    fixed = []
    if args.fix_legacy:
        for s in shots:
            cleaned, n = prompts.clean_legacy_prompt(s.get("veo_prompt", ""))
            if n:
                s.setdefault("veo_prompt_legacy", s["veo_prompt"])
                s["veo_prompt"] = cleaned
                fixed.append(s["shot_id"])
    report, totals = [], {"error": 0, "warn": 0, "info": 0}
    credits = 0
    for idx, s in enumerate(shots):
        findings = prompts.lint_shot(m, s, cfg)
        score, reasons = prompts.complexity_score(s, idx, len(shots))
        route = prompts.route_model(score, cfg)
        s["routing"] = {"complexity": score, "reasons": reasons, **route}
        s["lint"] = findings
        credits += route["credits"] * cfg["credits"]["takes_per_shot"]
        for f in findings:
            totals[f["level"]] += 1
        report.append({"shot_id": s["shot_id"], "chars": len(s.get("veo_prompt", "")), "model": route["label"],
                       "complexity": score, "findings": [f"{f['level'].upper()} {f['code']}: {f['msg']}" for f in findings]})
    proj_findings = prompts.lint_project(m, cfg)
    for f in proj_findings:
        totals[f["level"]] += 1
    mf.save(proj, m)
    out({"summary": {**totals, "shots": len(shots), "legacy_cleaned": fixed,
                     "estimated_credits_incl_takes": credits, "budget": cfg["credits"]["budget"]},
         "project_findings": [f"{f['level'].upper()} {f['code']}: {f['msg']}" for f in proj_findings],
         "shots": report})
    if totals["error"] and args.strict:
        sys.exit(2)


# ---------------------------------------------------------------- takes / provenance

def _default_inputs(proj: Path, m: dict, s: dict) -> list:
    mode = s.get("generation_mode")
    paths = []
    if mode in ("first_frame", "first_last"):
        paths.append(s.get("first_frame_path"))
    if mode == "first_last":
        paths.append(s.get("last_frame_path"))
    if mode == "ingredients":
        paths += mf.shot_reference_paths(m, s, proj_dir=proj, limit=3, include_env=True)
    return [p for p in dict.fromkeys(paths) if p]


def register_take(proj: Path, m: dict, s: dict, src: Path, *, mode=None, model=None, inputs=None,
                  source_url=None, note="", select=False) -> dict:
    takes = s.setdefault("takes", [])
    sha = media.sha256_file(src)
    dup = next((t for t in takes if t.get("sha256") == sha), None)
    if dup:  # cùng một file đã đăng ký (thu về lại) → không tạo take trùng
        return dup
    n = max([t["take"] for t in takes], default=0) + 1
    dst = proj / "assets" / "clips" / "takes" / f"{s['shot_id']}_take{n:02d}.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if Path(src).resolve() != dst.resolve():
        shutil.copy2(src, dst)
    input_list = inputs if inputs is not None else _default_inputs(proj, m, s)
    entry = {
        "take": n, "path": rel(proj, dst), "sha256": media.sha256_file(dst),
        "registered_at": datetime.now().isoformat(timespec="seconds"),
        "generation_mode": mode or s.get("generation_mode", "unknown"),
        "model": model or s.get("routing", {}).get("label", ""),
        "prompt": s.get("veo_prompt", ""), "negative_prompt": prompts.effective_negative_prompt(m, s),
        "inputs": [{"path": p, "sha256": media.sha256_file(proj / p) if (proj / p).exists() else None} for p in input_list],
    }
    if source_url:
        entry["source_url"] = source_url
    if note:
        entry["note"] = note
    takes.append(entry)
    if select or not s.get("selected_take"):
        select_take(proj, s, n)
    return entry


def select_take(proj: Path, s: dict, n: int) -> None:
    take = next((t for t in s.get("takes", []) if t["take"] == n), None)
    if not take:
        raise mf.ManifestError(f"{s['shot_id']} không có take {n}")
    dst = mf.clip_path(proj, s)
    dst.parent.mkdir(parents=True, exist_ok=True)
    hi = take.get("path_1080")
    src = proj / hi if hi and (proj / hi).exists() else proj / take["path"]
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    s["selected_take"] = n
    s["status"] = mf.STATUS_RENDERED
    s.pop("qa", None)


def cmd_register_clip(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    s = mf.find_shot(m, args.shot)
    inputs = [x.strip() for x in args.inputs.split(",")] if args.inputs else None
    entry = register_take(proj, m, s, Path(args.clip), mode=args.mode, model=args.model, inputs=inputs,
                          note=args.note, select=args.select)
    mf.save(proj, m)
    out({"status": "ok", "shot": s["shot_id"], "take": entry, "selected_take": s.get("selected_take")})


def cmd_select_take(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    s = mf.find_shot(m, args.shot)
    select_take(proj, s, args.take)
    mf.save(proj, m)
    out({"status": "ok", "shot": s["shot_id"], "selected_take": args.take})


def cmd_download_batch(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    tasks = []
    if args.urls_json:
        mapping = json.loads(Path(args.urls_json).read_text(encoding="utf-8"))
        for key, url in mapping.items():
            if url:
                tasks.append((key, url))
    else:
        tasks = [(s["shot_id"], s["cdn_video_url"]) for s in m.get("shots", []) if s.get("cdn_video_url")]
    if not tasks:
        out({"status": "nothing_to_download"})
        return
    tmp = proj / "assets" / "clips" / "_incoming"
    tmp.mkdir(parents=True, exist_ok=True)

    def fetch(task):
        key, url = task
        dst = tmp / (Path(key).name if key.endswith(".mp4") else f"{key}.mp4")
        for attempt in range(3):
            try:
                urllib.request.urlretrieve(url, dst)
                return key, url, dst, None
            except Exception as e:  # noqa: BLE001 — báo lỗi từng file, không dừng cả batch
                err = str(e)
                time.sleep(1.5 * (attempt + 1))
        return key, url, None, err

    results = []
    with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as pool:
        for fut in as_completed([pool.submit(fetch, t) for t in tasks]):
            results.append(fut.result())

    report = []
    for key, url, dst, err in sorted(results, key=lambda r: r[0]):
        if err:
            report.append({"key": key, "error": err})
            continue
        sid = re.search(r"shot_\d+", key)
        if sid:
            try:
                s = mf.find_shot(m, sid.group(0))
                entry = register_take(proj, m, s, dst, source_url=url)
                dst.unlink(missing_ok=True)
                report.append({"key": key, "shot": s["shot_id"], "take": entry["take"]})
                continue
            except mf.ManifestError:
                pass
        final = proj / key if "/" in key else dst
        final.parent.mkdir(parents=True, exist_ok=True)
        if final != dst:
            shutil.move(dst, final)
        report.append({"key": key, "saved": str(final)})
    mf.save(proj, m)
    out({"status": "ok", "results": report})


# ---------------------------------------------------------------- frames

def cmd_extract_frame(args, cfg):
    cv2 = media.cv2_module()
    clip, dst = Path(args.clip), Path(args.out)
    t = args.at
    if args.after_speech or args.command == "extract-active-frame":
        t = min(media.probe(clip)["duration"], au.speech_window(clip)["end"] + 0.08)
    frame, t_real = media.read_frame_at(clip, t, last=(t is None))
    dst.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst), frame)
    out({"status": "ok", "frame": str(dst), "time_sec": round(t_real, 3),
         "tip": "Với shot nối tiếp cùng cảnh, ưu tiên Extend trong Flow — nối bằng 1 frame tĩnh làm mất quán tính chuyển động."})


# ---------------------------------------------------------------- QA

def _qa_one(proj: Path, s: dict, cfg: dict) -> dict:
    clip = mf.clip_path(proj, s)
    res = qa.technical_qa(clip, cfg)
    sheet = qa.contact_sheet(clip, proj / "assets" / "qa" / f"{s['shot_id']}_qa_grid.jpg", s["shot_id"])
    return {"shot": s, "tech": res, "sheet": sheet}


def _apply_status(s: dict) -> None:
    if s.get("status") == mf.STATUS_APPROVED:
        return
    q = s.get("qa", {})
    verdicts = [q.get("technical", {}).get("verdict")]
    vision = q.get("vision") or {}
    if vision.get("verdict") == "retake":
        verdicts.append("fail")
    if "fail" in verdicts:
        s["status"] = mf.STATUS_QA_FAIL
    elif "warn" in verdicts:
        s["status"] = mf.STATUS_QA_WARN
    elif "pass" in verdicts:
        s["status"] = mf.STATUS_QA_PASS


def cmd_qa(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    shots = [s for s in mf.ordered_shots(m) if mf.clip_path(proj, s).exists() and (not args.shot or s["shot_id"] == args.shot)]
    if not shots:
        sys.exit("[ERROR] Không có clip nào để QA.")
    with ThreadPoolExecutor(max_workers=min(6, len(shots))) as pool:
        results = list(pool.map(lambda s: _qa_one(proj, s, cfg), shots))
    report = []
    for r in results:
        s = r["shot"]
        s.setdefault("qa", {})["technical"] = {"verdict": r["tech"]["verdict"], "findings": r["tech"]["findings"],
                                                "checked_at": datetime.now().isoformat(timespec="seconds")}
        s["qa"]["contact_sheet"] = rel(proj, r["sheet"])
        _apply_status(s)
        info = r["tech"]["info"]
        report.append({"shot": s["shot_id"], "verdict": r["tech"]["verdict"], "status": s["status"],
                       "media": f"{info['width']}x{info['height']} {info['fps']}fps {info['duration']:.2f}s",
                       "findings": [f"{f['level'].upper()} {f['code']}: {f['msg']}" for f in r["tech"]["findings"]]})
    mf.save(proj, m)
    out({"summary": {v: sum(1 for r in report if r["verdict"] == v) for v in ("pass", "warn", "fail")},
         "next": "Chạy `qa-vision` để kiểm danh tính nhân vật & bám prompt (lớp QA thị giác).",
         "shots": report})


def _vision_paths(proj: Path, sid: str) -> tuple:
    qa_dir = proj / "assets" / "qa"
    return qa_dir / f"{sid}_qa_grid.jpg", qa_dir / f"{sid}_vision_qa.md", qa_dir / f"{sid}_vision_result.json"


def _store_vision(s: dict, result: dict, reviewer: str) -> None:
    s.setdefault("qa", {})["vision"] = {**result, "reviewer": reviewer,
                                        "checked_at": datetime.now().isoformat(timespec="seconds")}
    _apply_status(s)


AGENT_QA_INSTRUCTIONS = (
    "Bạn (AI agent đang chat) là người chấm QA thị giác — KHÔNG gọi API. Với mỗi shot: mở packet, xem ảnh 1 "
    "(contact sheet) và các ảnh tham chiếu bằng công cụ đọc ảnh, trả lời đúng JSON schema trong checklist, "
    "ghi vào result_path. Sau đó chạy: python scripts/studio_helper.py qa-vision-submit --project {project}. "
    "Chấm khắt khe: sai danh tính / sai giải phẫu / letterbox / không đúng góc máy → verdict \"retake\"."
)


def cmd_qa_vision(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    rv = qa.detect_reviewer(cfg, args.reviewer)
    shots = [s for s in mf.ordered_shots(m) if mf.clip_path(proj, s).exists() and (not args.shot or s["shot_id"] == args.shot)]
    report = []
    for s in shots:
        sheet, packet_md, result_path = _vision_paths(proj, s["shot_id"])
        if not sheet.exists():
            qa.contact_sheet(mf.clip_path(proj, s), sheet, s["shot_id"])
        packet = qa.build_vision_packet(proj, m, s, sheet)
        if rv["mode"] == "api":
            try:
                result = qa.run_vision_qa(packet, cfg)
            except Exception as e:  # noqa: BLE001
                report.append({"shot": s["shot_id"], "error": str(e)})
                continue
            errors = qa.validate_vision_result(result)
            if errors:
                report.append({"shot": s["shot_id"], "error": f"Kết quả API sai schema: {errors}"})
                continue
            _store_vision(s, result, f"api:{cfg['models']['gemini_vision_qa']}")
            report.append({"shot": s["shot_id"], "verdict": result["verdict"], "score": result["overall_score_1_10"],
                           "advice": result.get("retake_advice", "")})
        else:
            qa.write_packet(packet, packet_md, result_path)
            report.append({"shot": s["shot_id"], "packet": str(packet_md), "contact_sheet": str(sheet.resolve()),
                           "references": [str(r.resolve()) for r in packet["references"]],
                           "result_path": str(result_path.resolve())})
    mf.save(proj, m)
    res = {"reviewer": rv, "shots": report}
    if rv["mode"] == "agent":
        res["agent_instructions"] = AGENT_QA_INSTRUCTIONS.format(project=m.get("project_slug", proj.name))
    elif rv["mode"] == "manual":
        res["instructions"] = "Duyệt bằng mắt theo packet, ghi JSON vào result_path rồi chạy qa-vision-submit."
    out(res)


def cmd_qa_vision_submit(args, cfg):
    """Nạp kết quả QA thị giác do agent/người duyệt ghi ra file JSON vào manifest."""
    proj = proj_dir_of(args)
    m = mf.load(proj)
    rv = qa.detect_reviewer(cfg, args.reviewer)
    reviewer = f"agent:{rv['agent']}" if rv["mode"] == "agent" and rv["agent"] else rv["mode"]
    report = []
    for s in mf.ordered_shots(m):
        if args.shot and s["shot_id"] != args.shot:
            continue
        _, _, result_path = _vision_paths(proj, s["shot_id"])
        if not result_path.exists():
            continue
        clip = mf.clip_path(proj, s)
        if clip.exists() and result_path.stat().st_mtime < clip.stat().st_mtime:
            report.append({"shot": s["shot_id"], "skipped": "kết quả cũ hơn take hiện tại — chấm lại"})
            continue
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            report.append({"shot": s["shot_id"], "error": f"JSON lỗi: {e}"})
            continue
        errors = qa.validate_vision_result(result)
        if errors:
            report.append({"shot": s["shot_id"], "error": errors})
            continue
        _store_vision(s, result, reviewer)
        report.append({"shot": s["shot_id"], "verdict": result["verdict"], "score": result["overall_score_1_10"],
                       "status": s["status"], "advice": result.get("retake_advice", "")})
    mf.save(proj, m)
    out({"reviewer": reviewer, "submitted": report})


def cmd_approve(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    done = []
    for sid in args.shots.split(","):
        s = mf.find_shot(m, sid.strip())
        s["status"] = mf.STATUS_APPROVED
        s["approved_at"] = datetime.now().isoformat(timespec="seconds")
        done.append(s["shot_id"])
    mf.save(proj, m)
    out({"approved": done})


# ---------------------------------------------------------------- voiceover / edit

class _VoUnit(dict):
    """Bọc beat hoặc shot để vòng lặp voiceover dùng chung (ghi voiceover_path vào đúng đối tượng gốc)."""

    def __init__(self, target: dict, label: str):
        super().__init__(shot_id=label)
        self.target = target

    def __setitem__(self, key, value):
        self.target[key] = value
        super().__setitem__(key, value)


def cmd_voiceover(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    ok, why = au.tts_available()
    vo_dir = proj / "assets" / "audio" / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)
    report, script = [], ["# Kịch bản lời dẫn", "", "Mỗi dòng → 1 file WAV `assets/audio/vo/<shot_id>.wav` (cùng 1 giọng).", ""]
    direction = m.get("voiceover_direction", "")
    voice = prompts.narrator_voice(m) or cfg["tts"]["voice"]
    beat_ids = set(bt.beats_by_id(m))
    units = [(b, b["narration"], f"beat_{b['beat_id']}", b["beat_id"]) for b in bt.ordered_beats(m) if b.get("narration")]
    for s in mf.ordered_shots(m):
        a = mf.shot_audio(s)
        if s.get("beat") in beat_ids or a["mode"] != "voiceover_external" or not a.get("line"):
            continue
        units.append((s, a["line"], s["shot_id"], s["shot_id"]))
    for s, line, stem, label in units:
        a = {"line": line}
        s = _VoUnit(s, label)
        wav = vo_dir / f"{stem}.wav"
        if not wav.exists() and wav.with_suffix(".raw.wav").exists():
            wav.with_suffix(".raw.wav").replace(wav)
        script.append(f"- **{s['shot_id']}**: {a['line']}")
        tts_model = args.model or m.get("voiceover_model") or cfg["models"]["gemini_tts"]
        h = au.text_hash(a["line"], voice, direction, tts_model)
        stale = wav.exists() and s.target.get("voiceover_hash") not in (None, h)
        if wav.exists() and not args.force and not stale:
            status = "existing"
            s.target.setdefault("voiceover_hash", h)  # file cũ chưa có dấu vân tay → coi là khớp câu hiện tại
        elif ok:
            try:
                au.synthesize(a["line"], wav, cfg, voice=voice, direction=direction, model=tts_model)
            except au.QuotaExhausted as e:
                report.append({"shot": s["shot_id"], "status": "quota_exhausted", "error": str(e)})
                break
            status = "resynthesized_changed_text" if stale else "synthesized"
            s.target["voiceover_hash"] = h
        else:
            report.append({"shot": s["shot_id"], "status": "missing_wav"})
            continue
        # Siết nhịp: luôn làm lại từ bản gốc (*.raw.wav) để chạy nhiều lần không bị siết chồng.
        raw = wav.with_suffix(".raw.wav")
        if status != "existing" or not raw.exists():
            wav.replace(raw)
        ed = cfg["editorial"]
        is_beat = "beat_id" in s.target  # lời của beat trải qua nhiều shot → không bị giới hạn theo 1 clip 8s
        max_sec = ed.get("vo_max_beat_sec", 30.0) if is_beat else ed["vo_max_sec"]
        fit = au.fit_narration(raw, wav, max_sec, ed["vo_max_pause_sec"], ed["vo_max_tempo"])
        s["voiceover_path"] = rel(proj, wav)
        mf.save(proj, m)  # lưu ngay từng câu: lỗi giữa chừng không mất phần đã tạo
        dur = au.wav_duration(wav)
        row = {"shot": s["shot_id"], "status": status, "duration_sec": round(dur, 2),
               "raw_sec": fit["before_sec"], "tempo": fit["tempo"]}
        if dur > max_sec + 0.05:
            row["warning"] = f"Vẫn dài {dur:.1f}s > {max_sec}s sau khi siết — rút gọn câu hoặc dùng Extend cho shot."
        if status != "existing":
            heard = au.transcribe(wav, cfg)
            if heard:
                score = au.words_match(a["line"], heard)
                row["transcript_match"] = round(score, 2)
                if score < 0.9:
                    row["warning"] = f"TTS đọc lệch kịch bản (khớp {score:.0%}): \"{heard}\" — chạy lại với --force."
        expected = au.expected_speech_sec(a["line"])
        if fit["before_sec"] > expected * 1.8 + 1.5 and "warning" not in row and fit["tempo"] >= 1.2:
            row["warning"] = (f"Đọc rất chậm ({dur:.1f}s, nhịp tự nhiên ~{expected:.1f}s) — bỏ 'slowly' khỏi "
                              "voiceover_direction hoặc cắt khoảng lặng.")
        report.append(row)
    (proj / "voiceover_script.md").write_text("\n".join(script), encoding="utf-8")
    mf.save(proj, m)
    out({"tts": "gemini" if ok else f"tắt ({why}) — thu âm/TTS ngoài rồi đặt WAV vào {vo_dir}",
         "voice": voice, "shots": report})


def cmd_compare_voices(args, cfg):
    """So giọng nói giữa các clip (vd. 2 clip cùng gắn giọng Charon trên Flow)."""
    clips = [Path(c) for c in args.clips]
    profiles = {}
    for c in clips:
        if not c.exists():
            sys.exit(f"[ERROR] Không có file {c}")
        prof = au.voice_profile(c)
        profiles[c.name] = prof
    names = list(profiles)
    pairs = [{"a": a, "b": b, **au.compare_voice_profiles(profiles[a], profiles[b])}
             for i, a in enumerate(names) for b in names[i + 1:]]
    summary = {n: {k: v for k, v in p.items() if k != "spectral_envelope"} for n, p in profiles.items()}
    out({"profiles": summary, "pairs": pairs,
         "note": "Số đo thô (cao độ + màu giọng), dễ lệch khi có nhạc/SFX lớn. Kết luận cuối cùng: nghe bằng tai."})


def cmd_timeline(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    segs = timeline.compute(proj, m, cfg, include_pending=args.include_failed)
    out({"total_duration_sec": timeline.total_duration(segs), "segments": timeline.to_json(segs)})


def cmd_assemble(args, cfg):
    t0 = time.time()
    proj = proj_dir_of(args)
    m = mf.load(proj)
    segs = timeline.compute(proj, m, cfg, include_pending=args.include_failed)
    used = {s["shot_id"] for s in segs}
    excluded = [{"shot": s["shot_id"], "status": s.get("status")} for s in mf.ordered_shots(m)
                if mf.clip_path(proj, s).exists() and s["shot_id"] not in used]
    outdir = proj / "output"
    outdir.mkdir(exist_ok=True)
    (outdir / "timeline.json").write_text(json.dumps(timeline.to_json(segs), ensure_ascii=False, indent=2), encoding="utf-8")

    formats = ["landscape", "vertical"] if args.format == "both" else (
        [args.format] if args.format else m.get("delivery_formats", ["landscape"]))
    music = Path(args.music) if args.music else (proj / m["music_path"] if m.get("music_path") else None)
    lut = None if args.no_lut else (Path(args.lut) if args.lut else (proj / m["lut_path"] if m.get("lut_path") else None))
    renders, srts, cues = [], [], 0
    for fmt in formats:
        path = outdir / render.output_name(args.out, fmt)
        srt = outdir / render.output_name("subtitles", fmt).replace(".mp4", ".srt")
        if not args.no_subs:
            cues = render.write_srt(segs, srt, cfg, fmt)
            srts.append(str(srt))
        info = render.render(segs, path, cfg, fmt=fmt, fit=args.fit, music=music, srt=srt,
                             burn_subs=args.burn_subs, lut=lut)
        probe = media.probe(path)
        info["duration_actual"] = round(probe["duration"], 2)
        renders.append(info)
    out({"status": "ok", "elapsed_sec": round(time.time() - t0, 1), "renders": renders,
         "subtitle_cues": cues, "subtitles_srt": srts if cues else None,
         "excluded_shots": excluded,
         "edit_notes": {s["shot_id"]: s["notes"] for s in segs if s["notes"]},
         "timeline": str(outdir / "timeline.json")})


# ---------------------------------------------------------------- nhạc nền tự tổng hợp + thumbnail

def cmd_score(args, cfg):
    from . import music

    proj = proj_dir_of(args)
    m = mf.load(proj)
    segs = timeline.compute(proj, m, cfg)
    secs = music.sections_from_timeline(segs, m)
    mood = music.detect_mood(m, getattr(args, "mood", "auto"))
    rel = "assets/audio/music/score_auto.wav"
    res = music.synth_score(timeline.total_duration(segs), secs, proj / rel, seed=args.seed,
                            cuts=music.cut_times(segs), mood=mood)
    m["music_path"] = rel
    m["music_source"] = {"kind": "procedural", "mood": mood, "seed": args.seed, "license": "tự tổng hợp, miễn bản quyền"}
    mf.save(proj, m)
    out({"status": "ok", **res, "music_path": rel,
         "sections": [{"t0": round(a, 2), "t1": round(b, 2), "purpose": c} for a, b, c in secs],
         "note": "Dựng lại timeline (độ dài đổi) → chạy lại score để nhạc khớp beat."})


def cmd_thumbnail(args, cfg):
    from . import thumbnail

    proj = proj_dir_of(args)
    m = mf.load(proj)
    segs = timeline.compute(proj, m, cfg)
    title = args.title or m.get("thumbnail_title") or m.get("title") or m.get("project_slug", "")
    res = thumbnail.make(segs, proj / "output", title, args.subtitle or m.get("thumbnail_subtitle", ""),
                         shot=args.shot or None, at=args.at)
    out({"status": "ok", **res})


def cmd_make_lut(args, cfg):
    from . import grade

    proj = proj_dir_of(args)
    m = mf.load(proj)
    rel_path = f"assets/grade/{args.preset}_{int(args.strength * 100)}.cube"
    grade.write_cube(proj / rel_path, args.preset, args.strength)
    res = {"status": "ok", "lut": rel_path}
    clip = next((mf.clip_path(proj, s) for s in mf.ordered_shots(m) if mf.clip_path(proj, s).exists()), None)
    if clip:
        cv2 = media.cv2_module()
        frame, _ = media.read_frame_at(clip, 2.0)
        prev = proj / "output" / "grade_preview.jpg"
        prev.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(prev), grade.preview(cv2.resize(frame, (960, 540)), args.preset, args.strength))
        res["preview"] = str(prev)
    if not args.no_apply:
        m["lut_path"] = rel_path
        mf.save(proj, m)
        res["note"] = "Đã đặt manifest.lut_path — assemble tự áp (tắt: --no-lut)."
    out(res)


# ---------------------------------------------------------------- bàn giao giữa các máy / phiên

def _latest_project_dir() -> Path:
    from . import progress  # noqa: F401

    best, best_at = None, ""
    for mp in PROJECTS_DIR.glob("*/project_manifest.json"):
        try:
            at = (mf.load(mp.parent).get("last_activity") or {}).get("at", "")
        except Exception:  # noqa: BLE001
            continue
        if at > best_at:
            best, best_at = mp.parent, at
    return best


def _has_ffmpeg() -> bool:
    try:
        return bool(media.ffmpeg_exe())
    except Exception:  # noqa: BLE001
        return False


def _machine_checks(cfg) -> dict:
    import os

    from . import progress

    checks = {"machine": progress.machine(cfg),
              "gemini_api_key": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
              "ffmpeg": _has_ffmpeg(),
              "media_dir": str(progress.media_dir(cfg, "")) if progress.media_dir(cfg, "") else None}
    try:
        import urllib.request

        urllib.request.urlopen(f"http://127.0.0.1:{cfg['browser']['debug_port']}/json/version", timeout=2)
        checks["chrome_debug"] = True
    except Exception:  # noqa: BLE001
        checks["chrome_debug"] = False
    fixes = []
    if not checks["gemini_api_key"]:
        fixes.append("Tạo .env (chép .env.example) và dán GEMINI_API_KEY — .env không đồng bộ qua git.")
    if not checks["media_dir"]:
        fixes.append("Thêm STUDIO_MEDIA_DIR=rclone:gdrive:AI-video-media vào .env để media-pull/push (docs/SYNC_SETUP.md).")
    if progress.media_target(cfg).startswith("rclone:"):
        try:
            checks["rclone"] = progress.rclone_exe()
        except mf.ManifestError:
            checks["rclone"] = None
            fixes.append("STUDIO_MEDIA_DIR dùng rclone nhưng máy chưa cài rclone — docs/SYNC_SETUP.md.")
    if not checks["chrome_debug"]:
        fixes.append("Chưa mở Chrome điều khiển (cần cho bước Flow): chạy `check-browser` để xem lệnh mở, đăng nhập Google một lần.")
    checks["fixes"] = fixes
    return checks


def cmd_resume(args, cfg):
    from . import progress

    proj = proj_dir_of(args) if args.project else _latest_project_dir()
    if not proj:
        out({"status": "no_project", "note": "Chưa có dự án nào — dùng init."})
        return
    m = mf.load(proj)
    st = progress.stage(proj, m)
    miss = progress.missing_media(proj, m)
    other = progress.other_machine_active(m, cfg)
    path = proj / "PROGRESS.md"
    if not args.no_write:
        progress.write(proj, m, cfg)
    res = {"project": proj.name, "progress_md": str(path), "next_step": st,
           "pending_flow_jobs": [j for j in m.get("flow_jobs", []) if not j.get("harvested")],
           "missing_media": len(miss), "missing_examples": [p for p, _ in miss[:8]],
           "last_activity": m.get("last_activity"), "recent_notes": m.get("handoff_notes", [])[-5:],
           "machine": _machine_checks(cfg)}
    warnings = []
    if other:
        warnings.append(f"Máy '{other['machine']}' vừa chạy `{other['command']}` {other['minutes_ago']} phút trước — "
                        "đừng chạy song song 2 máy trên cùng dự án (khóa dự án không có tác dụng giữa 2 máy).")
    if miss:
        warnings.append(f"Máy này thiếu {len(miss)} file media → media-pull trước khi dựng/QA.")
    res["warnings"] = warnings
    out(res)


def cmd_note(args, cfg):
    from . import progress

    proj = proj_dir_of(args)
    m = mf.load(proj)
    n = progress.add_note(m, args.text, cfg, args.kind)
    mf.save(proj, m)
    out({"status": "ok", "note": n})


def cmd_progress(args, cfg):
    from . import progress

    proj = proj_dir_of(args)
    out({"status": "ok", "progress_md": str(progress.write(proj, mf.load(proj), cfg))})


def cmd_media_sync(args, cfg):
    from . import progress

    proj = proj_dir_of(args)
    m = mf.load(proj)
    out({"status": "ok", **progress.sync_media(proj, m, cfg, "push" if args.command == "media-push" else "pull", args.all)})


def cmd_publish_kit(args, cfg):
    from . import publish

    proj = proj_dir_of(args)
    m = mf.load(proj)
    segs = timeline.compute(proj, m, cfg)
    res = publish.build(segs, m, proj / "output")
    if res["drafted"]:
        res["next"] = (f"Agent: viết {', '.join(res['drafted'])} vào manifest.publish (tiêu đề hấp dẫn, ≤ 100 ký tự; "
                       "mô tả 2–3 câu; 8–15 tag) rồi chạy lại.")
    out(res)


# ---------------------------------------------------------------- storyboard (cổng duyệt 0 credit)

def cmd_storyboard(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    per_shot = cfg["models"]["video"]["quality"]["credits"] * cfg["credits"]["takes_per_shot"]
    res = storyboard.build(proj, m, cfg, per_shot)
    mf.save(proj, m)
    res["next"] = ("Người dùng xem storyboard.html → storyboard-approve" if not res["approval"]["valid"]
                   else "Đã duyệt — flow-generate --kind video")
    out(res)


def cmd_storyboard_approve(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    st = storyboard.approval_state(m)
    if (m.get("storyboard") or {}).get("built_hash") != st["current_hash"]:
        sys.exit("[ERROR] Nội dung đã đổi từ lần xuất storyboard gần nhất — chạy `storyboard` và xem lại trước khi duyệt.")
    m["storyboard"] = {**m.get("storyboard", {}), "status": "approved", "approved_hash": st["current_hash"],
                       "approved_at": datetime.now().isoformat(timespec="seconds"), "approved_by": args.by}
    mf.save(proj, m)
    out({"approved": True, "hash": st["current_hash"]})


# ---------------------------------------------------------------- Flow automation

def _flow_targets(m: dict, args) -> list:
    shots = [s for s in mf.ordered_shots(m) if not s.get("exclude_from_edit")]
    if args.retakes:
        return [s for s in shots if s.get("status") == "needs_retake"]
    if args.shots:
        want = set(args.shots.split(","))
        return [s for s in shots if s["shot_id"] in want]
    if args.kind == "frames":
        return [s for s in shots if s.get("first_frame_prompt") or s.get("last_frame_prompt")]
    return [s for s in shots if s.get("veo_prompt")]


def sort_shots_for_flow(shots: list, kind: str, fallback_model: str, explicit_model: str = "") -> list:
    """Gom nhóm shot theo (vmode, model, bộ subjects/environment) để giảm tối đa thao tác đổi Settings & gắn lại Ingredients."""
    if kind != "video" or len(shots) <= 2:
        return list(shots)

    def group_key(item):
        idx, s = item
        mode = s.get("generation_mode", "text")
        vmode = "frames" if mode in ("first_frame", "first_last") else "ingredients"
        model = explicit_model or (s.get("routing") or {}).get("label") or fallback_model
        subj_sig = tuple(s.get("subjects") or []) if vmode == "ingredients" else ()
        env_sig = (s.get("environment") or "") if vmode == "ingredients" else ""
        return (vmode, model, subj_sig, env_sig, idx)

    return [s for _, s in sorted(enumerate(shots), key=group_key)]


def _ref_paths(proj: Path, m: dict, s: dict, limit: int = 3) -> list:
    rels = mf.shot_reference_paths(m, s, proj_dir=proj, limit=limit, include_env=True)
    return [proj / p for p in rels]


def cmd_flow_generate(args, cfg):
    from . import flow as fl

    proj = proj_dir_of(args)
    m = mf.load(proj)
    mf.resolve_chained_keyframes(m, proj)
    shots = _flow_targets(m, args)
    if not shots:
        sys.exit("[ERROR] Không có shot nào để tạo (kiểm tra --shots / prompt / --retakes).")
    kind = "image" if args.kind == "frames" else "video"
    if kind == "video" and not args.retakes and not args.skip_approval:
        st = storyboard.approval_state(m)
        if not st["valid"]:
            sys.exit("[ERROR] Storyboard chưa được duyệt (hoặc đã sửa sau khi duyệt): chạy `storyboard`, "
                     "người dùng xem và `storyboard-approve`, rồi mới tạo video. (--skip-approval để bỏ qua)")
    fallback_model = cfg["models"]["image"]["pro"] if kind == "image" else cfg["models"]["video"][args.tier]["label"]
    aspect = args.aspect or m.get("aspect_ratio", "16:9")
    stage_dir = proj / ".flow" / "staged"
    if kind == "video":
        shots = sort_shots_for_flow(shots, kind, fallback_model, args.model)
    report, spent = [], 0
    with fl.Flow(cfg["browser"]["debug_port"], m.get("flow_project_url", "")) as f:
        if args.new_project or not m.get("flow_project_url"):
            m["flow_project_url"] = f.new_project()
            mf.save(proj, m)
        last_mode, last_attach_sig, setting, cost = None, None, {}, None
        for s in shots:
            mode = s.get("generation_mode", "text") if kind == "video" else "image"
            vmode = "frames" if mode in ("first_frame", "first_last") else "ingredients"
            shot_model = args.model or (
                (s.get("routing") or {}).get("label") if kind == "video" else None
            ) or fallback_model
            if (kind, vmode, shot_model) != last_mode:
                setting = f.configure(kind=kind, video_mode=vmode, aspect=aspect, model=shot_model,
                                      duration=args.duration, count=args.count)
                cost, last_mode = setting["credits_per_submit"], (kind, vmode, shot_model)
                last_attach_sig = None
            if kind == "image":
                slots = []
                if s.get("first_frame_prompt") and not s.get("chain_from_prev"):
                    if args.retakes or not s.get("first_frame_path") or not (proj / s["first_frame_path"]).exists():
                        slots.append(("start", s["first_frame_prompt"]))
                if s.get("last_frame_prompt") and (s.get("generation_mode") == "first_last" or s.get("end_action")):
                    if args.retakes or not s.get("last_frame_path") or not (proj / s["last_frame_path"]).exists():
                        slots.append(("end", s["last_frame_prompt"]))
                for slot, text in slots:
                    row = {"shot": s["shot_id"], "slot": slot, "mode": "image", "model": shot_model,
                           "uid": mf.keyframe_uid(m, s["shot_id"], slot), "settings": setting.get("summary"), "credits": cost}
                    if slot == "end" and (not s.get("first_frame_path") or not (proj / s["first_frame_path"]).exists()):
                        row["skipped"] = "chờ tải first_frame_path trước khi tạo last_frame_path (Anchor-Locked)"
                        report.append(row)
                        continue
                    if args.max_credits and cost is not None and spent + cost > args.max_credits:
                        row["skipped"] = f"vượt ngân sách --max-credits {args.max_credits}"
                        report.append(row)
                        continue
                    refs = _ref_paths(proj, m, s)
                    if slot == "end" and s.get("first_frame_path") and (proj / s["first_frame_path"]).exists():
                        start_p = proj / s["first_frame_path"]
                        attach_list = [(start_p, mf.keyframe_uid(m, s["shot_id"], "start"))]
                        attach_list += [(r, "") for r in refs if r.resolve() != start_p.resolve()][:2]
                    else:
                        attach_list = [(r, "") for r in refs]
                    cur_sig = ("image", tuple((str(p.resolve()), u) for p, u in attach_list))
                    if cur_sig != last_attach_sig or not f.replace_prompt_text(text):
                        f.clear_prompt()
                        for p, u in attach_list:
                            f.attach_file(p, stage_dir=stage_dir, uid=u)
                        f.type_prompt(text)
                        last_attach_sig = cur_sig
                    else:
                        row["reused_attachments"] = True
                    row["composed"] = f.screenshot(proj / ".flow" / f"{s['shot_id']}_{slot}_compose.png")
                    if args.dry_run:
                        row["dry_run"] = True
                        report.append(row)
                        continue
                    f.submit()
                    spent += cost or 0
                    m.setdefault("flow_jobs", []).append({"shot": s["shot_id"], "slot": slot, "kind": kind, "model": shot_model,
                                                           "count": args.count, "credits": cost,
                                                           "at": datetime.now().isoformat(timespec="seconds")})
                    mf.save(proj, m)
                    report.append(row)
                continue

            row = {"shot": s["shot_id"], "mode": mode, "model": shot_model, "settings": setting.get("summary"), "credits": cost}
            if args.max_credits and cost is not None and spent + cost > args.max_credits:
                row["skipped"] = f"vượt ngân sách --max-credits {args.max_credits}"
                report.append(row)
                continue
            text = s.get("veo_prompt", "")
            voice = prompts.shot_voice(m, s) if mf.shot_audio(s)["mode"] in ("veo_dialogue", "veo_narration") else ""
            if mode == "ingredients":
                refs = _ref_paths(proj, m, s)
                cur_sig = ("video_ingredients", tuple(str(r.resolve()) for r in refs), voice)
                if cur_sig != last_attach_sig or not f.replace_prompt_text(text):
                    f.clear_prompt()
                    for ref in refs:
                        f.attach_file(ref, stage_dir=stage_dir)
                    if voice:
                        f.attach_voice(voice)
                    f.type_prompt(text)
                    last_attach_sig = cur_sig
                else:
                    row["reused_attachments"] = True
            else:
                last_attach_sig = None
                f.clear_prompt()
                if mode in ("first_frame", "first_last"):
                    if not s.get("first_frame_path") or not (proj / s["first_frame_path"]).exists():
                        row["skipped"] = "thiếu first_frame_path"
                        report.append(row)
                        continue
                    if mode == "first_last" and (not s.get("last_frame_path") or not (proj / s["last_frame_path"]).exists()):
                        row["skipped"] = "thiếu last_frame_path"
                        report.append(row)
                        continue
                    f.set_start_frame(proj / s["first_frame_path"], stage_dir=stage_dir,
                                      uid=mf.keyframe_uid(m, s["shot_id"], "start"))
                    if mode == "first_last":
                        f.set_end_frame(proj / s["last_frame_path"], stage_dir=stage_dir,
                                        uid=mf.keyframe_uid(m, s["shot_id"], "end"))
                if voice:
                    f.attach_voice(voice)
                f.type_prompt(text)
            row["composed"] = f.screenshot(proj / ".flow" / f"{s['shot_id']}_{kind}_compose.png")
            if args.dry_run:
                row["dry_run"] = True
                report.append(row)
                continue
            f.submit()
            spent += cost or 0
            m.setdefault("flow_jobs", []).append({"shot": s["shot_id"], "kind": kind, "model": shot_model, "count": args.count,
                                                   "credits": cost, "at": datetime.now().isoformat(timespec="seconds")})
            if s.get("status") == "needs_retake":
                s["status"] = "retake_submitted"
            mf.save(proj, m)
            report.append(row)
    out({"flow_project": m.get("flow_project_url"), "credits_spent": spent, "shots": report,
         "next": f"flow-harvest --kind {'image' if kind == 'image' else 'video'} --wait"})


def cmd_flow_harvest(args, cfg):
    from . import flow as fl

    proj = proj_dir_of(args)
    m = mf.load(proj)
    kind = args.kind
    prompt_map = {}
    for s in mf.ordered_shots(m):
        if kind == "image":
            if s.get("first_frame_prompt") and not s.get("chain_from_prev"):
                prompt_map[s["shot_id"]] = s["first_frame_prompt"]
            if s.get("last_frame_prompt"):
                prompt_map[f"{s['shot_id']}__end"] = s["last_frame_prompt"]
        elif s.get("veo_prompt"):
            prompt_map[s["shot_id"]] = s["veo_prompt"]
    only = set(args.shots.split(",")) if args.shots else None
    if only and kind == "image":
        only = only | {f"{sid}__end" for sid in list(only)}
    jobs = [j for j in m.get("flow_jobs", []) if j["kind"] == kind and (not only or j["shot"] in only)]
    pending = [j for j in jobs if not j.get("harvested")]
    quota = None
    if jobs and not args.all:
        quota = {}
        for j in pending:
            key = f"{j['shot']}__end" if kind == "image" and j.get("slot") == "end" else j["shot"]
            quota[key] = quota.get(key, 0) + 1
        if not quota:
            out({"kind": kind, "harvested": [], "note": "Không còn job nào chờ tải (dùng --all để quét lại toàn bộ)."})
            return
        only = set(quota) if not only else only & set(quota)
    incoming = proj / "assets" / ("frames/_incoming" if kind == "image" else "clips/_incoming")
    report = []

    def _handle_harvest_row(r):
        raw_sid = r["shot"]
        slot = "end" if raw_sid.endswith("__end") else "start"
        sid = raw_sid[:-5] if slot == "end" else raw_sid
        s = mf.find_shot(m, sid)
        if "error" in r or "skipped" in r:
            report.append(r)
            return
        job = next((j for j in pending if j["shot"] == sid and (j.get("slot", "start") == slot or kind == "video") and not j.get("harvested")), None)
        if job:
            job["harvested"] = datetime.now().isoformat(timespec="seconds")
        if kind == "video":
            new, rejected = [], []
            owners = {t["sha256"]: x["shot_id"] for x in m["shots"] for t in x.get("takes", [])}
            ff = proj / s["first_frame_path"] if s.get("first_frame_path") else None
            for tile_idx, fpath in enumerate(r["files"]):
                sha = media.sha256_file(fpath)
                if owners.get(sha) not in (None, s["shot_id"]):
                    rejected.append(f"file thuộc {owners[sha]} (tải nhầm hàng)")
                    Path(fpath).unlink(missing_ok=True)
                    continue
                if s.get("generation_mode") in ("first_frame", "first_last") and ff and ff.exists():
                    corr = takes.first_frame_match(Path(fpath), ff)
                    if corr < cfg["qa"].get("first_frame_min_corr", 0.8):
                        rejected.append(f"frame đầu không khớp first_frame_path (corr={corr:.2f})")
                        Path(fpath).unlink(missing_ok=True)
                        continue
                before = len(s.get("takes", []))
                entry = register_take(proj, m, s, Path(fpath), mode=s.get("generation_mode"),
                                      model=s.get("routing", {}).get("label", ""), note="flow-harvest")
                entry["flow_tile_index"] = tile_idx
                if len(s.get("takes", [])) > before:
                    new.append(entry["take"])
                Path(fpath).unlink(missing_ok=True)
            if rejected and not new and job:
                job.pop("harvested", None)  # không nhận được clip đúng → job vẫn chờ tải
            report.append({"shot": s["shot_id"], "new_takes": new, "total_takes": len(s.get("takes", [])),
                           **({"rejected": rejected} if rejected else {})})
        else:
            cand_dir = proj / "assets" / "frames" / "candidates"
            cand_dir.mkdir(parents=True, exist_ok=True)
            cand_key = "last_frame_candidates" if slot == "end" else "frame_candidates"
            path_key = "last_frame_path" if slot == "end" else "first_frame_path"
            uid_prefix = mf.keyframe_uid(m, s["shot_id"], slot)
            cands = s.setdefault(cand_key, [])
            for fpath in r["files"]:
                sha = media.sha256_file(fpath)
                if any(c.get("sha256") == sha for c in cands):
                    Path(fpath).unlink(missing_ok=True)
                    continue
                dst = cand_dir / f"{uid_prefix}_c{len(cands) + 1:02d}{Path(fpath).suffix}"
                Path(fpath).replace(dst)
                cands.append({"path": rel(proj, dst), "sha256": sha, "uid": uid_prefix})
            if cands and (not s.get(path_key) or not (proj / s[path_key]).exists()):
                chosen_rel = cands[0]["path"]
                if slot == "end" and len(cands) > 1 and s.get("first_frame_path") and (proj / s["first_frame_path"]).exists():
                    try:
                        import numpy as np
                        cv2 = media.cv2_module()
                        ref_im = cv2.resize(cv2.imread(str(proj / s["first_frame_path"])), (160, 90)).astype(np.float32)
                        scored = []
                        for c in cands:
                            cim = cv2.imread(str(proj / c["path"]))
                            if cim is not None:
                                cim = cv2.resize(cim, (160, 90)).astype(np.float32)
                                scored.append((float(1.0 - np.mean(np.abs(ref_im - cim)) / 255.0), c["path"]))
                        if scored:
                            scored.sort(reverse=True)
                            chosen_rel = scored[0][1]
                    except Exception:  # noqa: BLE001
                        pass
                canonical = proj / mf.keyframe_rel_path(m, s["shot_id"], slot, Path(chosen_rel).suffix)
                canonical.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(proj / chosen_rel, canonical)
                s[path_key] = rel(proj, canonical)
            report.append({"shot": s["shot_id"], "slot": slot, "uid": uid_prefix, "candidates": [c["path"] for c in cands]})
        mf.save(proj, m)  # Lưu ngay sau từng hàng tải xong (Streaming Harvest)

    with fl.Flow(cfg["browser"]["debug_port"], m.get("flow_project_url", ""), download_dir=incoming) as f:
        known = {s["shot_id"]: {tk["sha256"] for tk in s.get("takes", []) if tk.get("sha256")} for s in m["shots"]}
        f.harvest_rows(kind, prompt_map, incoming, only_shots=only, quota=quota, known_sha=known,
                       wait_done=bool(args.wait), wait_timeout=args.wait_timeout, on_row=_handle_harvest_row)
    if kind == "image":
        chained = mf.resolve_chained_keyframes(m, proj)
        if chained:
            mf.save(proj, m)
    out({"kind": kind, "harvested": report,
         "next": "qa-takes rồi auto-select" if kind == "video"
         else "chạy storyboard để duyệt toàn bộ Keyframe, rồi flow-generate --kind video"})


def cmd_flow_upscale(args, cfg):
    from . import flow as fl

    proj = proj_dir_of(args)
    m = mf.load(proj)
    shots = [s for s in mf.ordered_shots(m) if s.get("takes") and (not args.shots or s["shot_id"] in args.shots.split(","))]
    wanted = {}
    for s in shots:
        for t in s["takes"]:
            if args.takes == "selected" and t["take"] != s.get("selected_take"):
                continue
            key_res = f"path_{args.res}"
            if t.get(key_res) and (proj / t[key_res]).exists() and not args.force:
                continue
            src = proj / t["path"]
            if not src.exists():
                continue
            dest = src.with_name(f"{src.stem}_{args.res}p.mp4")
            video_jobs = sum(1 for j in m.get("flow_jobs", []) if j.get("shot") == s["shot_id"] and j.get("kind") == "video")
            wanted[t["sha256"]] = {"shot": s["shot_id"], "take": t["take"], "dest": str(dest),
                                   "prompt": t.get("prompt") or s.get("veo_prompt", ""),
                                   "sig": takes.visual_signature(src),
                                   "tile_index": t.get("flow_tile_index"),
                                   "single_job": video_jobs <= 1}
    if not wanted:
        out({"status": "nothing_to_do"})
        return
    prompt_map = {}
    for w in wanted.values():
        prompt_map.setdefault(w["shot"], w["prompt"])
    for s in mf.ordered_shots(m):  # mọi shot vào bảng khớp để không nhận nhầm hàng có phần đầu prompt giống nhau
        if s.get("veo_prompt"):
            prompt_map.setdefault(s["shot_id"], s["veo_prompt"])

    def match(small: Path, pending: dict):
        sha = media.sha256_file(small)
        if sha in pending:
            return sha
        sig = takes.visual_signature(small)
        scored = [(takes.signature_similarity(sig, w["sig"]), k) for k, w in pending.items()]
        best = max(scored, default=None)
        return best[1] if best and best[0] >= 0.95 else None

    report = []

    def save_result(r):  # lưu ngay sau mỗi clip — lỗi giữa chừng không mất phần đã upscale
        s = mf.find_shot(m, r["shot"])
        t = next(x for x in s["takes"] if x["take"] == r["take"])
        row = {"shot": r["shot"], "take": r["take"]}
        if "error" in r:
            row["error"] = r["error"]
        else:
            info = media.probe(r["dest"])
            t[f"path_{args.res}"] = rel(proj, Path(r["dest"]))
            row.update(size=f"{info['width']}x{info['height']}", duration=round(info["duration"], 2))
            if s.get("selected_take") == t["take"]:
                shutil.copy2(r["dest"], mf.clip_path(proj, s))  # bản dựng dùng clip độ phân giải cao
                row["now_selected_clip"] = True
        report.append(row)
        mf.save(proj, m)

    t0 = time.time()
    with fl.Flow(cfg["browser"]["debug_port"], m.get("flow_project_url", ""),
                 download_dir=proj / "assets" / "clips" / "_incoming") as f:
        results = f.upscale_takes(prompt_map, wanted, proj / "assets" / "clips" / "takes", match, res=args.res,
                                  on_result=save_result)
    missing = [{"shot": r["shot"], "take": r["take"], "error": r["error"]} for r in results
               if "shot" in r and r.get("error") == "không tìm thấy clip trên Flow"]
    skipped = [r for r in results if "skipped" in r]
    out({"res": args.res, "elapsed_sec": round(time.time() - t0), "results": report + missing,
         "skipped_items": skipped})


# ---------------------------------------------------------------- QA từng take & tự chọn

def cmd_qa_takes(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    rv = qa.detect_reviewer(cfg, args.reviewer)
    target_shots = takes.shots_with_takes(m, args.shots)
    work_items = []
    for s in target_shots:
        for t in s["takes"]:
            q = takes.ensure_take_qa(t)
            if q.get("vision") and not args.force:
                continue
            clip = proj / t["path"]
            if not clip.exists():
                continue
            work_items.append((s, t, q, clip))

    def _process_item(item):
        s, t, q, clip = item
        tech = qa.technical_qa(clip, cfg)
        paths = takes.take_paths(proj, s["shot_id"], t["take"])
        sh = takes.take_sheet(clip, paths["sheet"])
        return s, t, q, tech, paths, sh

    processed = []
    if work_items:
        with ThreadPoolExecutor(max_workers=min(8, len(work_items))) as pool:
            processed = list(pool.map(_process_item, work_items))

    report = []
    for s, t, q, tech, paths, sh in processed:
        q["technical"] = {"verdict": tech["verdict"], "findings": tech["findings"]}
        q["duration"] = round(sh["duration"], 2)
        packet = {"contact_sheet": sh["sheet"], "references": qa._reference_images(proj, m, s),
                  "prompt": takes.build_take_prompt(m, s, cfg, len(sh["times"]), sh["duration"])}
        row = {"shot": s["shot_id"], "take": t["take"], "technical": tech["verdict"]}
        if rv["mode"] == "api":
            try:
                res = qa.run_vision_qa(packet, cfg)
                errs = takes.validate_take_result(res, sh["duration"])
                if errs:
                    row["error"] = errs
                else:
                    q["vision"] = {**res, "reviewer": f"api:{cfg['models']['gemini_vision_qa']}"}
                    row["score"] = res["overall_score_1_10"]
            except Exception as e:  # noqa: BLE001
                row["error"] = str(e)[:200]
        else:
            qa.write_packet(packet, paths["packet"], paths["result"])
            row.update(sheet=str(paths["sheet"].resolve()), result_path=str(paths["result"].resolve()))
        report.append(row)
    continuity = takes.build_continuity_sheets(proj, target_shots) if target_shots else []
    mf.save(proj, m)
    res = {"reviewer": rv, "takes": report, **({"continuity_sheets": continuity} if continuity else {})}
    if rv["mode"] != "api":
        res["instructions"] = ("Với mỗi take: xem `sheet` (hoặc `continuity_sheets` để đối chiếu liền mạch 4 shot/lượt) "
                               "+ ảnh tham chiếu, trả lời JSON theo checklist trong packet (.md cạnh sheet), "
                               "ghi vào `result_path`, rồi chạy `qa-takes-submit` và `auto-select`.")
    out(res)


def cmd_qa_takes_submit(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    rv = qa.detect_reviewer(cfg, args.reviewer)
    reviewer = f"agent:{rv['agent']}" if rv["mode"] == "agent" and rv["agent"] else rv["mode"]
    report, batch_results, pending_commits = [], [], []
    for s in takes.shots_with_takes(m, args.shots):
        for t in s["takes"]:
            rp = takes.take_paths(proj, s["shot_id"], t["take"])["result"]
            if not rp.exists():
                continue
            q = takes.ensure_take_qa(t)
            try:
                res = takes.load_result(rp)
            except json.JSONDecodeError as e:
                report.append({"shot": s["shot_id"], "take": t["take"], "error": f"JSON lỗi: {e}"})
                continue
            errs = takes.validate_take_result(res, q.get("duration"))
            if errs:
                report.append({"shot": s["shot_id"], "take": t["take"], "error": errs})
                continue
            batch_results.append(res)
            pending_commits.append((s, t, q, res))
    rubber_stamp = takes.detect_rubber_stamp(batch_results)
    if rubber_stamp and not getattr(args, "allow_uniform_qa", False):
        out({"reviewer": reviewer, "error": "RUBBER_STAMP_DETECTED", "issues": rubber_stamp,
             "hint": "Chấm thực tế từng contact sheet (ghi rõ lỗi + mốc giờ). Dùng --allow-uniform-qa nếu chắc chắn."})
        sys.exit(2)
    for s, t, q, res in pending_commits:
        q["vision"] = {**res, "reviewer": reviewer, "checked_at": datetime.now().isoformat(timespec="seconds")}
        report.append({"shot": s["shot_id"], "take": t["take"], "score": res["overall_score_1_10"],
                       "defects": len(res.get("defects", []))})
    mf.save(proj, m)
    out({"reviewer": reviewer, "submitted": report, **({"warnings": rubber_stamp} if rubber_stamp else {})})


def cmd_auto_select(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    ordered = mf.ordered_shots(m)
    next_chained = {
        ordered[i]["shot_id"]: bool(ordered[i + 1].get("chain_from_prev"))
        for i in range(len(ordered) - 1)
    }
    report = []
    for s in takes.shots_with_takes(m, args.shots):
        if s.get("lock_take"):
            report.append({"shot": s["shot_id"], "locked": s.get("selected_take")})
            continue
        need = takes.needed_seconds(proj, s, cfg, m)
        in_beat = s.get("beat") in bt.beats_by_id(m)
        d = takes.choose_take(s, need, cfg, pref=need if in_beat else None,
                              chain_next=next_chained.get(s["shot_id"], False))
        if d.get("retake"):
            rounds = sum(1 for j in m.get("flow_jobs", []) if j["shot"] == s["shot_id"] and j["kind"] == "video")
            cap = cfg["credits"].get("max_retakes_per_shot", 2)
            # Đã tạo lại đủ số lượt mà vẫn hỏng: lỗi nằm ở thiết kế shot (bố cục/hành động), không phải may rủi.
            s["status"] = "needs_director" if rounds > cap else "needs_retake"
            s["retake_reasons"] = d["reasons"]
            report.append({"shot": s["shot_id"], "decision": s["status"], "video_rounds": rounds, "reasons": d["reasons"]})
            continue
        select_take(proj, s, d["take"])
        if not s.get("lock_edit"):
            s["edit_in"], s["edit_out"] = d["edit_in"], d["edit_out"]
        v = next(t for t in s["takes"] if t["take"] == d["take"])["qa"]["vision"]
        s["status"] = mf.STATUS_QA_PASS if v["verdict"] == "pass" else mf.STATUS_QA_WARN
        s["auto_selection"] = {
            **{k: d[k] for k in ("take", "edit_in", "edit_out", "score", "reason", "alternatives")},
            "window": list(d["window"]),
        }
        s.pop("retake_reasons", None)
        report.append({"shot": s["shot_id"], "take": d["take"], "edit": [d["edit_in"], d["edit_out"]], "need_sec": need,
                       "score": d["score"], "status": s["status"], "other_rejects": d["rejected_reasons"]})
    mf.save(proj, m)
    retakes = [r["shot"] for r in report if r.get("decision") == "needs_retake"]
    director = [r["shot"] for r in report if r.get("decision") == "needs_director"]
    out({"shots": report, "needs_retake": retakes, "needs_director": director,
         "next": "flow-generate --kind video --retakes" if retakes else "voiceover → assemble"})


# ---------------------------------------------------------------- status / browser

def cmd_status(args, cfg):
    proj = proj_dir_of(args)
    m = mf.load(proj)
    rows, counts = [], {}
    for s in mf.ordered_shots(m):
        st = s.get("status", mf.STATUS_PENDING)
        counts[st] = counts.get(st, 0) + 1
        rows.append(f"{s['shot_id']:<10} {st:<9} takes={len(s.get('takes', [])):<2} "
                    f"mode={s.get('generation_mode', '-'):<12} {s.get('routing', {}).get('tier', '-'):<7} "
                    f"lint={sum(1 for f in s.get('lint', []) if f['level'] != 'info')}")
    print(f"{m.get('project_name')}  (schema v{m.get('schema_version', 1)})")
    print("\n".join(rows))
    print(json.dumps(counts, ensure_ascii=False))


def cmd_browser(args, cfg):
    from . import browser

    kw = {k: getattr(args, k) for k in ("url", "text", "selector", "role", "name", "value", "key", "dest", "exact", "nth")
          if getattr(args, k, None) not in (None, "")}
    if args.xy:
        kw["x"], kw["y"] = (float(v) for v in args.xy.split(","))
    if args.dy:
        kw["dy"] = args.dy
    if args.seconds:
        kw["seconds"] = args.seconds
    if args.files:
        kw["files"] = [str(Path(f).resolve()) for f in args.files.split(",")]
    try:
        out(browser.run(args.action, port=cfg["browser"]["debug_port"], tab=args.tab, **kw))
    except browser.BrowserError as e:
        sys.exit(f"[ERROR] {e}")
    except Exception as e:  # noqa: BLE001 — trả lỗi gọn để agent chụp lại màn hình và thử cách khác
        sys.exit(f"[ERROR] {type(e).__name__}: {str(e)[:500]}")


def _find_chrome_exe(configured: str = "") -> str:
    if configured and (Path(configured).exists() or shutil.which(configured)):
        return shutil.which(configured) or configured
    for cmd in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(cmd)
        if found:
            return found
    for p in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        if Path(p).exists():
            return p
    return ""


def cmd_check_browser(args, cfg):
    b = cfg["browser"]
    port = b["debug_port"]
    ready = False
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
            ready = bool(json.loads(r.read().decode()).get("webSocketDebuggerUrl"))
    except Exception:  # noqa: BLE001
        ready = False
    if args.launch and not ready:
        exe = _find_chrome_exe(b.get("chrome_exe", ""))
        if not exe:
            sys.exit("[ERROR] Không tìm thấy Chrome — đặt browser.chrome_exe trong studio_config.json")
        profile = str(Path(b["profile_dir"]).expanduser())
        subprocess.Popen(
            [exe, f"--remote-debugging-port={port}", f"--user-data-dir={profile}",
             "--no-first-run", "--no-default-browser-check", b["flow_url"]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(20):  # chờ Chrome mở cổng debug
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
                    ready = bool(json.loads(r.read().decode()).get("webSocketDebuggerUrl"))
                    break
            except Exception:  # noqa: BLE001
                continue
    out({"debug_port": port, "ready": ready})


def cmd_list_models(args, cfg):
    """Liệt kê model mà API key hiện tại gọi được, để chọn đúng ID cho studio_config.json."""
    ok, why = au.tts_available()
    if not ok:
        sys.exit(f"[ERROR] Không gọi được Gemini API: {why}")
    from google import genai

    client = genai.Client()  # giữ tham chiếu: client bị thu gom giữa chừng sẽ đóng kết nối khi đang phân trang
    rows, all_ids = [], set()
    try:
        for m in client.models.list():
            name = m.name.removeprefix("models/")
            all_ids.add(name)
            if args.filter and args.filter.lower() not in name.lower():
                continue
            rows.append({"id": name, "display": getattr(m, "display_name", ""),
                         "actions": getattr(m, "supported_actions", None)})
    except Exception as e:  # noqa: BLE001 — báo lỗi API (key sai, hết hạn mức...) gọn gàng
        sys.exit(f"[ERROR] Gemini API từ chối: {str(e)[:400]}")
    configured = {k: cfg["models"][k] for k in ("gemini_vision_qa", "gemini_tts")}
    out({"configured": {k: {"id": v, "available": v in all_ids} for k, v in configured.items()}, "models": rows})


# ---------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studio_helper", description=f"AI Video Studio v{__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, func, help_, aliases=()):
        sp = sub.add_parser(name, help=help_, aliases=list(aliases))
        sp.set_defaults(func=func)
        return sp

    def project_arg(sp):
        sp.add_argument("--project", required=True, help="Thư mục dự án hoặc slug trong projects/")

    sp = add("plan", cmd_plan, "Ước lượng số clip & credit theo độ dài shot sau dựng")
    sp.add_argument("--duration", type=int, required=True)
    sp.add_argument("--lang", default="vi")
    sp.add_argument("--avg-shot", type=float, default=5.0, help="Độ dài TB một shot sau dựng (giây)")

    sp = add("init", cmd_init, "Khởi tạo dự án (schema v2)")
    sp.add_argument("--name", required=True)
    sp.add_argument("--duration", type=int, required=True)
    sp.add_argument("--lang", default="vi")
    sp.add_argument("--style", default="cinematic photorealistic")
    sp.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"])
    sp.add_argument("--audio", default="voiceover_external", choices=list(prompts.AUDIO_MODES))
    sp.add_argument("--avg-shot", type=float, default=0)

    sp = add("migrate", cmd_migrate, "Nâng manifest cũ lên schema v2 (dọn prompt, đăng ký clip làm take)")
    project_arg(sp)

    sp = add("forge-assets", cmd_forge_assets, "Sinh prompt bộ ảnh tham chiếu nhân vật / bối cảnh / đạo cụ")
    project_arg(sp)
    sp.add_argument("--char-name", default="")
    sp.add_argument("--char-desc", default="", help="identity_line: mô tả nhận dạng ngắn, dùng nguyên văn mọi shot")
    sp.add_argument("--char-type", default="human", choices=list(asset_tpl.REFERENCE_VIEWS))
    sp.add_argument("--char-id", default="")
    sp.add_argument("--char-voice", default="", help="Giọng cố định trên Flow/Gemini TTS, vd. Charon")
    sp.add_argument("--style", default="")
    sp.add_argument("--env-name", default="")
    sp.add_argument("--env-desc", default="")
    sp.add_argument("--env-id", default="")
    sp.add_argument("--props", default="", help='Danh sách "tên@kích thước", phân cách dấu phẩy')
    sp.add_argument("--apply-to-manifest", action="store_true")

    sp = add("audit-assets", cmd_audit_assets, "Kiểm tài nguyên tiền kỳ (identity_line, ảnh tham chiếu)")
    project_arg(sp)

    sp = add("build-prompts", cmd_build_prompts, "Dựng veo_prompt từ trường có cấu trúc + xuất prompts_for_flow.md")
    project_arg(sp)

    sp = add("lint-prompts", cmd_lint_prompts, "Lint prompt + định tuyến model + ước tính credit", aliases=["audit-prompts"])
    project_arg(sp)
    sp.add_argument("--fix-legacy", action="store_true", help="Gỡ boilerplate engine cũ khỏi veo_prompt")
    sp.add_argument("--strict", action="store_true", help="Exit 2 nếu có lỗi")
    sp.add_argument("--budget", type=int, help=argparse.SUPPRESS)

    sp = add("register-clip", cmd_register_clip, "Đăng ký 1 take vừa tạo (lưu nguồn gốc: prompt, input, model)")
    project_arg(sp)
    sp.add_argument("--shot", required=True)
    sp.add_argument("--clip", required=True)
    sp.add_argument("--mode", choices=list(prompts.GENERATION_MODES))
    sp.add_argument("--model", default="")
    sp.add_argument("--inputs", default="", help="Đường dẫn input (tương đối dự án), phân cách dấu phẩy")
    sp.add_argument("--note", default="")
    sp.add_argument("--select", action="store_true", help="Dùng take này cho bản dựng")

    sp = add("select-take", cmd_select_take, "Chọn take dùng cho bản dựng")
    project_arg(sp)
    sp.add_argument("--shot", required=True)
    sp.add_argument("--take", type=int, required=True)

    sp = add("download-batch", cmd_download_batch, "Tải clip từ URL và tự đăng ký take")
    project_arg(sp)
    sp.add_argument("--urls-json", default="", help='JSON {"shot_01": "url", ...}')

    sp = add("extract-frame", cmd_extract_frame, "Trích 1 frame (cuối / tại t / sau thoại)",
             aliases=["extract-last-frame", "extract-active-frame"])
    sp.add_argument("--clip", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--at", type=float, default=None)
    sp.add_argument("--after-speech", action="store_true")

    sp = add("qa", cmd_qa, "QA kỹ thuật + contact sheet cho mọi clip", aliases=["qa-frames"])
    project_arg(sp)
    sp.add_argument("--shot", default="")

    reviewer_help = "auto (mặc định): agent đang chat nếu có, không thì Gemini API, không thì người duyệt"
    sp = add("qa-vision", cmd_qa_vision, "QA thị giác: danh tính, bám prompt, lỗi AI (agent / Gemini API / người)")
    project_arg(sp)
    sp.add_argument("--shot", default="")
    sp.add_argument("--reviewer", choices=list(qa.REVIEWER_MODES), help=reviewer_help)
    sp.add_argument("--manual", dest="reviewer", action="store_const", const="manual", help=argparse.SUPPRESS)

    sp = add("qa-vision-submit", cmd_qa_vision_submit, "Nạp kết quả QA thị giác (JSON do agent/người ghi) vào manifest")
    project_arg(sp)
    sp.add_argument("--shot", default="")
    sp.add_argument("--reviewer", choices=list(qa.REVIEWER_MODES), help=reviewer_help)

    sp = add("approve", cmd_approve, "Đạo diễn duyệt shot (bỏ qua cảnh báo QA)")
    project_arg(sp)
    sp.add_argument("--shots", required=True, help="shot_01,shot_02")

    sp = add("voiceover", cmd_voiceover, "Tạo/liên kết WAV lời dẫn cho shot audio.mode=voiceover_external")
    project_arg(sp)
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--model", default="", help="Model TTS cho cả lượt (mặc định models.gemini_tts). Mọi câu nên cùng 1 model.")

    sp = add("compare-voices", cmd_compare_voices, "So độ giống giọng nói giữa các clip/WAV")
    sp.add_argument("clips", nargs="+", help="≥ 2 file .mp4/.wav")

    sp = add("timeline", cmd_timeline, "Xem trước timeline dựng (không render)")
    project_arg(sp)
    sp.add_argument("--include-failed", action="store_true")

    sp = add("assemble", cmd_assemble, "Dựng bản cuối: mix âm thanh, loudnorm, phụ đề, 16:9 / 9:16")
    project_arg(sp)
    sp.add_argument("--format", choices=["landscape", "vertical", "both"])
    sp.add_argument("--fit", choices=["pad", "crop", "blur"], help="Cách đưa nguồn khác tỷ lệ vào khung")
    sp.add_argument("--music", default="")
    sp.add_argument("--lut", default="", help="File .cube để chỉnh màu đồng bộ (mặc định: manifest.lut_path)")
    sp.add_argument("--no-lut", action="store_true", help="Bỏ chỉnh màu")
    sp.add_argument("--burn-subs", action="store_true", help="In cứng phụ đề lên hình (video ngắn)")
    sp.add_argument("--no-subs", action="store_true")
    sp.add_argument("--include-failed", action="store_true", help="Dựng cả shot qa_fail")
    sp.add_argument("--out", default="final_video.mp4")
    sp.add_argument("--skip-exact-tempo", action="store_true", help=argparse.SUPPRESS)

    sp = add("score", cmd_score, "Nhạc nền tự tổng hợp theo beat (miễn bản quyền, 0 credit) → music_path")
    project_arg(sp)
    sp.add_argument("--seed", type=int, default=7)
    sp.add_argument("--mood", default="auto", choices=["auto", "tension", "podcast_lofi", "wonder"],
                    help="Bảng màu nhạc: auto (tự nhận diện theo dự án) | tension | podcast_lofi | wonder")

    sp = add("thumbnail", cmd_thumbnail, "Thumbnail 16:9 + 9:16: frame đẹp nhất + tiêu đề")
    project_arg(sp)
    sp.add_argument("--title", default="")
    sp.add_argument("--subtitle", default="")
    sp.add_argument("--shot", default="", help="Chọn shot (mặc định: tự chọn frame nét + tương phản tốt nhất)")
    sp.add_argument("--at", type=float, default=None, help="Giây trong clip của --shot")

    sp = add("resume", cmd_resume, "Bắt đầu phiên (máy khác / chat mới): bước tiếp theo, job dở, media thiếu, kiểm tra máy")
    sp.add_argument("--project", default="", help="Mặc định: dự án hoạt động gần nhất")
    sp.add_argument("--no-write", action="store_true", help=argparse.SUPPRESS)

    sp = add("note", cmd_note, "Ghi chú bàn giao / quyết định vào PROGRESS.md")
    project_arg(sp)
    sp.add_argument("text")
    sp.add_argument("--kind", choices=["note", "decision", "todo", "issue"], default="note")

    sp = add("progress", cmd_progress, "Sinh lại PROGRESS.md + projects/INDEX.md")
    project_arg(sp)

    for name, desc in (("media-push", "Đẩy media (clip, lời dẫn, nhạc, đầu ra) lên thư mục chung STUDIO_MEDIA_DIR"),
                       ("media-pull", "Lấy media còn thiếu từ thư mục chung STUDIO_MEDIA_DIR về máy này")):
        sp = add(name, cmd_media_sync, desc)
        project_arg(sp)
        sp.add_argument("--all", action="store_true", help="Mọi file media của dự án (cả take không chọn), không chỉ file đang dùng")

    sp = add("make-lut", cmd_make_lut, "Tạo LUT màu .cube bằng code (0 đồng) + ảnh so sánh trước/sau")
    project_arg(sp)
    sp.add_argument("--preset", choices=["documentary", "warm_dawn"], default="documentary")
    sp.add_argument("--strength", type=float, default=1.0)
    sp.add_argument("--no-apply", action="store_true", help="Chỉ tạo file, không đặt vào manifest")

    sp = add("publish-kit", cmd_publish_kit, "Bộ đăng kênh: tiêu đề / mô tả / tag / chương / nhãn AI → output/publish.md")
    project_arg(sp)

    sp = add("storyboard", cmd_storyboard, "Xuất storyboard (ảnh mở đầu + lời dẫn theo beat) để duyệt — 0 credit")
    project_arg(sp)

    sp = add("storyboard-approve", cmd_storyboard_approve, "Người dùng duyệt storyboard hiện tại (mở khóa tạo video)")
    project_arg(sp)
    sp.add_argument("--by", default="user")

    sp = add("flow-generate", cmd_flow_generate, "Tự tạo frame (Nano Banana) hoặc video (Veo) trên Google Flow")
    project_arg(sp)
    sp.add_argument("--kind", choices=["frames", "video"], default="video")
    sp.add_argument("--shots", default="", help="shot_01,shot_02 (mặc định: mọi shot có prompt)")
    sp.add_argument("--retakes", action="store_true", help="Chỉ các shot auto-select đánh dấu needs_retake")
    sp.add_argument("--count", type=int, default=2, help="Số bản mỗi shot (x1–x4)")
    sp.add_argument("--tier", choices=["quality", "fast"], default="quality")
    sp.add_argument("--model", default="")
    sp.add_argument("--aspect", default="", help="16:9 | 9:16 (mặc định theo dự án)")
    sp.add_argument("--duration", type=int, default=8, choices=[4, 6, 8])
    sp.add_argument("--max-credits", type=int, default=0, help="Dừng gửi khi vượt ngân sách lượt này")
    sp.add_argument("--new-project", action="store_true")
    sp.add_argument("--dry-run", action="store_true", help="Soạn và chụp màn hình, không bấm tạo")
    sp.add_argument("--skip-approval", action="store_true", help="Bỏ qua cổng duyệt storyboard (không khuyến nghị)")

    sp = add("flow-harvest", cmd_flow_harvest, "Tải kết quả từ Flow theo hàng, khớp shot, đăng ký take / frame")
    project_arg(sp)
    sp.add_argument("--kind", choices=["video", "image"], default="video")
    sp.add_argument("--shots", default="")
    sp.add_argument("--wait", action="store_true", help="Chờ Flow tạo xong trước khi tải")
    sp.add_argument("--wait-timeout", type=int, default=1500)
    sp.add_argument("--all", action="store_true", help="Bỏ qua nhật ký job, quét mọi hàng khớp shot")

    sp = add("flow-upscale", cmd_flow_upscale, "Upscale lần lượt take đã chọn lên 1080p trên Flow và dùng cho bản dựng")
    project_arg(sp)
    sp.add_argument("--shots", default="")
    sp.add_argument("--takes", choices=["selected", "all"], default="selected")
    sp.add_argument("--res", choices=["1080"], default="1080")
    sp.add_argument("--force", action="store_true")

    sp = add("qa-takes", cmd_qa_takes, "QA kỹ thuật + thị giác cho TỪNG take (có mốc giờ lỗi)")
    project_arg(sp)
    sp.add_argument("--shots", default="")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--reviewer", choices=list(qa.REVIEWER_MODES))

    sp = add("qa-takes-submit", cmd_qa_takes_submit, "Nạp kết quả QA take (JSON do agent/người ghi)")
    project_arg(sp)
    sp.add_argument("--shots", default="")
    sp.add_argument("--reviewer", choices=list(qa.REVIEWER_MODES))
    sp.add_argument("--allow-uniform-qa", action="store_true",
                    help="Bỏ qua chốt chặn phát hiện chấm điểm hàng loạt (rubber-stamping)")

    sp = add("auto-select", cmd_auto_select, "Tự chọn take tốt nhất + cửa sổ cắt tránh lỗi; đánh dấu needs_retake")
    project_arg(sp)
    sp.add_argument("--shots", default="")

    sp = add("status", cmd_status, "Bảng trạng thái các shot")
    project_arg(sp)

    sp = add("list-models", cmd_list_models, "Liệt kê model Gemini API gọi được bằng key hiện tại")
    sp.add_argument("--filter", default="", help="Lọc theo chuỗi, vd. tts, pro")

    sp = add("browser", cmd_browser, "Agent điều khiển Chrome (Flow/Gemini/Drive): chụp, click, gõ, tải về")
    sp.add_argument("action", choices=["tabs", "goto", "shot", "click", "type", "press", "scroll", "wait", "text",
                                       "count", "upload", "download"])
    sp.add_argument("--tab", default="", help="Chọn tab có URL chứa chuỗi này")
    sp.add_argument("--url", default="")
    sp.add_argument("--text", default="", help="Click theo chữ hiển thị")
    sp.add_argument("--exact", action="store_true")
    sp.add_argument("--nth", type=int, default=None, help="Phần tử thứ n khi chữ trùng nhiều chỗ (-1 = cuối)")
    sp.add_argument("--role", default="")
    sp.add_argument("--name", default="")
    sp.add_argument("--selector", default="")
    sp.add_argument("--xy", default="", help="Click theo tọa độ x,y (pixel CSS của trang)")
    sp.add_argument("--value", default="")
    sp.add_argument("--key", default="")
    sp.add_argument("--dy", type=int, default=0)
    sp.add_argument("--seconds", type=float, default=0)
    sp.add_argument("--files", default="", help="File tải lên, phân cách dấu phẩy")
    sp.add_argument("--dest", default="", help="Nơi lưu file tải về")

    sp = add("check-browser", cmd_check_browser, "Kiểm tra / mở Chrome debug cho Google Flow")
    sp.add_argument("--launch", action="store_true")
    return p


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    cfg = load_config()
    read_only = {"publish-kit", "status", "timeline", "plan", "list-models", "compare-voices", "browser", "check-browser",
                 "resume", "progress"}
    try:
        if getattr(args, "project", None) and args.command not in read_only:
            proj = proj_dir_of(args)
            with mf.ProjectLock(proj):
                ok, err = False, ""
                try:
                    args.func(args, cfg)
                    ok = True
                except SystemExit as e:
                    ok, err = e.code in (0, None), "" if e.code in (0, None) else str(e.code)
                    raise
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    raise
                finally:
                    _record_progress(proj, args, argv, cfg, ok, err)
        else:
            args.func(args, cfg)
    except (mf.ManifestError, media.MediaError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def _record_progress(proj, args, argv, cfg, ok, err):
    """Sau mỗi lệnh sửa dự án: ghi nhật ký + cập nhật PROGRESS.md / INDEX.md (lỗi ở đây không được làm hỏng lệnh chính)."""
    from . import progress

    try:
        if not mf.manifest_path(proj).exists():
            return
        m = mf.load(proj)
        progress.log_command(m, args.command, list(argv if argv is not None else sys.argv[1:])[1:], cfg, ok, err)
        mf.save(proj, m)
        progress.write(proj, m, cfg)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Không cập nhật được PROGRESS.md: {e}", file=sys.stderr)
