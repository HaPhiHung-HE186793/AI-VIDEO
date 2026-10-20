"""Điều khiển Google Flow qua Chrome thật của người dùng (cổng debug) — tạo ảnh/video và thu clip về.

Nguyên tắc ổn định (rút ra từ lần chạy Chương 1):
- Định vị bằng aria-label / role / placeholder / cấu trúc, KHÔNG bằng tọa độ (bố cục đổi theo nội dung ô prompt).
- Mỗi thao tác chờ trạng thái cụ thể thay vì sleep cố định khi có thể.
- Tải về: nút "Tải xuống hàng loạt" theo HÀNG (ổn định hơn mở trình chỉnh sửa từng clip); mỗi hàng được nhận
  diện bằng prompt hiển thị trong chính hàng đó.
- Không giả mạo dấu hiệu tự động hóa. Người dùng đã cho phép thao tác trên tài khoản của họ.

Giao diện Flow có thể đổi: mọi chuỗi giao diện nằm trong UI bên dưới để sửa một chỗ.
"""

import re
import time
import zipfile
from pathlib import Path

from . import media

UI = {
    "prompt_box": "div[role=textbox][aria-label='Bạn muốn tạo những gì?']",
    "settings": "button[aria-label='Điều kiện kích hoạt cài đặt']",
    "submit": "button[aria-label='Bắt đầu tạo']",
    "clear_prompt": "button[aria-label='Xoá câu lệnh']",
    "bulk_download": "button[aria-label='Tải xuống hàng loạt']",
    "editor_download": "button[aria-label='Tải nội dung nghe nhìn xuống']",
    "ingredient_search": "input[placeholder*='Tìm kiếm']",
    "group_mode": "Chế độ",
    "group_aspect": "Tỷ lệ khung hình",
    "group_duration": "Thời lượng video",
    "group_count": "Số lượng kết quả đầu ra",
    "model_trigger": ".model-select-trigger-content",
    "credit_label": "flow-credit-cost-label",
    "add_to_prompt": "Thêm vào câu lệnh",
    "not_found": "Không tìm thấy thành phần",
    "upload_btn": "Tải nội dung nghe nhìn lên",
    "plus": "button[aria-label='Thêm thành phần vào ô nhập câu lệnh']",
    "start_slot": "Bắt đầu",
    "end_slot": "Kết thúc",
    "voices_tab": "Giọng nói",
    "filter_video": "Video",
    "filter_image": "Hình ảnh",
    "filter_all": "Tất cả nội dung",
    "kind_image": "Hình ảnh",
    "kind_video": "Video",
    "mode_frames": "Khung hình",
    "mode_ingredients": "Thành phần",
}

JS_SCROLLER = """(y) => { const s = [...document.querySelectorAll('*')].find(e => e.scrollHeight > e.clientHeight + 200 &&
  /auto|scroll/.test(getComputedStyle(e).overflowY)); const el = s || document.scrollingElement;
  if (y === null) el.scrollTo(0, 0); else el.scrollBy(0, y); return el.scrollTop; }"""

# Văn bản của HÀNG chứa nút tải xuống thứ i: leo lên tổ tiên lớn nhất chỉ chứa đúng 1 nút tải xuống.
JS_ROW_TEXTS = r"""(sel) => [...document.querySelectorAll(sel)].map(btn => {
  let el = btn, best = btn;
  while (el.parentElement) { el = el.parentElement; if (el.querySelectorAll(sel).length > 1) break; best = el; }
  return (best.innerText || '').replace(/\s+/g, ' ').trim(); })"""

# Nút "+" của thanh prompt: nút có chữ 'add' nằm cùng khung với nút gửi.
JS_MARK_PLUS = r"""(submitSel) => { const sub = document.querySelector(submitSel); if (!sub) return false;
  let box = sub; for (let i = 0; i < 8 && box; i++) { box = box.parentElement;
    const b = [...box.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'add');
    if (b) { document.querySelectorAll('[data-studio-plus]').forEach(e => e.removeAttribute('data-studio-plus'));
             b.setAttribute('data-studio-plus', '1'); return true; } }
  return false; }"""


# Ô clip trong hàng thứ ri: trả về số ô (ti = -1) hoặc mở ô ti (click phần tử của ô, kể cả khi bị lớp phủ che).
JS_ROW_TILES = r"""([sel, ri, ti]) => { const btn = document.querySelectorAll(sel)[ri]; let row = btn;
  while (row.parentElement && row.parentElement.querySelectorAll(sel).length === 1) row = row.parentElement;
  const labels = [...row.querySelectorAll('[role=button][aria-label]')].filter(t => !t.closest('button'));
  const boxes = [];  // nhãn chân ô chỉ hiện khi hover -> leo lên khung ảnh thu nhỏ (>=150x100) bao quanh nó
  for (const l of labels) { let b = l; while (b && b !== row) { const r = b.getBoundingClientRect();
      if (r.width >= 150 && r.height >= 100) break; b = b.parentElement; }
    if (b && b !== row && !boxes.includes(b)) boxes.push(b); }
  if (ti < 0) return boxes.length;
  const box = boxes[ti]; box.scrollIntoView({block: 'center'}); const r = box.getBoundingClientRect();
  // Ô ở cuối lưới có thể nằm dưới thanh prompt cố định: click phần tử của CHÍNH ô tại điểm đó, bỏ qua lớp phủ.
  for (const [fx, fy] of [[0.5, 0.35], [0.5, 0.15], [0.3, 0.3], [0.7, 0.3]]) {
    const x = r.left + r.width * fx, y = r.top + r.height * fy;
    const hit = document.elementsFromPoint(x, y).find(e => box.contains(e));
    if (hit) { hit.click(); return {clicked: true, x, y}; } }
  box.click(); return {clicked: true, fallback: true}; }"""


# Dải ảnh thu nhỏ trên đầu trình chỉnh sửa (mọi nội dung của dự án): i = -1 → số ô; ngược lại bấm ô i.
JS_STRIP = r"""(i) => { const bs = [...document.querySelectorAll('button')].filter(b => {
    const r = b.getBoundingClientRect(); return r.top < 70 && r.width > 15 && r.width < 45 && b.querySelector('img'); });
  if (i < 0) return bs.length; bs[i].scrollIntoView({inline: 'center'}); bs[i].click(); return bs.length; }"""


class FlowError(Exception):
    pass


GENERIC_STEMS = {"front", "three_quarter", "profile", "head", "expressions", "start", "end", "clean_plate", "turnaround"}


def stage_unique_file(path: Path, stage_dir: Path = None, uid: str = "") -> Path:
    """Đảm bảo file đưa lên Google Flow có tên (stem) duy nhất để ô tìm kiếm khớp 100% ngay lần đầu.

    Nếu file có tên chung (vd: `assets/characters/nam/front.png` -> stem `front` dễ trùng với nhân vật khác)
    hoặc được cấp `uid` rõ ràng (vd: `KF_PGMT_S01_START`), tạo bản sao nhẹ trong `.flow/staged/<uid>.ext`.
    """
    import shutil

    path = Path(path)
    if not path.exists():
        return path
    stem = path.stem
    if uid:
        unique_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", uid).strip("_")
    elif stem.lower() in GENERIC_STEMS or len(stem) < 5:
        parent = re.sub(r"[^a-zA-Z0-9]+", "_", path.parent.name).strip("_").upper()
        unique_stem = f"REF_{parent}_{stem.upper()}" if parent else stem
    else:
        return path
    if unique_stem == stem:
        return path
    target_dir = Path(stage_dir) if stage_dir else (path.parent / ".staged")
    target_dir.mkdir(parents=True, exist_ok=True)
    staged = target_dir / f"{unique_stem}{path.suffix.lower()}"
    if not staged.exists() or staged.stat().st_mtime < path.stat().st_mtime or staged.stat().st_size != path.stat().st_size:
        shutil.copy2(path, staged)
    return staged


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def match_row_to_shot(row_text: str, prompts: dict, prefix_len: int = 90, min_len: int = 40) -> str:
    """Hàng hiển thị prompt (bị cắt bớt) → shot có prompt bắt đầu khớp nhất. prompts: {shot_id: prompt}.

    Phải truyền prompt của MỌI shot (không chỉ shot cần tải): nhiều prompt chung phần mở đầu
    ("Extreme close-up macro shot, 100mm lens: ..."), chỉ so toàn bộ mới chọn đúng shot khớp dài nhất.
    """
    rt = norm_text(row_text)
    scored = []
    for sid, p in prompts.items():
        head = norm_text(p)[:prefix_len]
        # Flow cắt prompt bằng "…": độ dài tiền tố dài nhất có mặt trong hàng.
        n = next((k for k in range(len(head), min_len - 1, -1) if head[:k] in rt), 0)
        if n:
            scored.append((n, sid))
    scored.sort(reverse=True)
    if not scored or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        return None  # không khớp, hoặc hòa → không đoán
    return scored[0][1]


class Flow:
    def __init__(self, port: int = 9222, project_url: str = "", download_dir: Path = None):
        self.port, self.project_url = port, project_url
        self.download_dir = Path(download_dir) if download_dir else None
        self._pw = self.browser = self.page = self._cdp = None

    # ------------------------------------------------------------- phiên
    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        try:
            self.browser = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{self.port}")
        except Exception as e:  # noqa: BLE001
            self._pw.stop()
            raise FlowError(f"Không kết nối được Chrome cổng {self.port} — chạy `check-browser --launch`. ({e})") from e
        pages = [p for c in self.browser.contexts for p in c.pages if "flow.google.com" in p.url]
        if self.project_url:
            pages = [p for p in pages if self.project_url in p.url] or pages
        if not pages:
            if not self.project_url or not self.browser.contexts:
                raise FlowError("Không có tab Google Flow nào đang mở.")
            pages = [self.browser.contexts[0].new_page()]  # máy mới / phiên mới: tự mở tab dự án
        self.page = pages[0]
        if self.project_url and self.project_url not in self.page.url:
            self.page.goto(self.project_url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)
        if self.project_url and self.project_url.rstrip("/") not in self.page.url:
            # Bị chuyển hướng (chưa đăng nhập / khác tài khoản Google) → dừng, không thao tác nhầm chỗ.
            raise FlowError(f"Không mở được dự án Flow {self.project_url} (trang hiện tại: {self.page.url[:120]}). "
                            "Chrome điều khiển trên máy này phải đăng nhập ĐÚNG tài khoản Google đã tạo dự án.")
        self.page.bring_to_front()
        try:
            if self.page.evaluate("() => window.innerWidth") < 1000:
                pcdp = self.page.context.new_cdp_session(self.page)
                win = pcdp.send("Browser.getWindowForTarget")
                pcdp.send("Browser.setWindowBounds", {
                    "windowId": win["windowId"],
                    "bounds": {"width": 1280, "height": 960, "windowState": "normal"},
                })
                self.page.wait_for_timeout(400)
        except Exception:
            pass
        if self.download_dir:
            self.download_dir.mkdir(parents=True, exist_ok=True)
            self._cdp = self.browser.new_browser_cdp_session()
            self._cdp.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(self.download_dir)})
        return self

    def __exit__(self, *exc):
        if self._pw:
            self._pw.stop()  # chỉ ngắt kết nối, không đóng Chrome

    def wait(self, sec: float):
        self.page.wait_for_timeout(int(sec * 1000))

    def screenshot(self, path: Path) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(path))
        return str(path)

    def escape(self, n: int = 1):
        for _ in range(n):
            self.page.keyboard.press("Escape")
            self.wait(0.3)

    # ------------------------------------------------------------- dự án
    def new_project(self) -> str:
        self.page.goto("https://flow.google.com/", wait_until="domcontentloaded")
        self.wait(2.5)
        self.page.get_by_text("Dự án mới").first.click()
        self.page.wait_for_url(re.compile(r"/project/"), timeout=30000)
        self.wait(2)
        self.project_url = self.page.url.split("/edit/")[0]
        return self.project_url

    def back_to_grid(self):
        if "/edit/" in self.page.url:
            self.page.goto(self.page.url.split("/edit/")[0], wait_until="domcontentloaded")
            self.wait(2.5)

    # ------------------------------------------------------------- cài đặt
    def _toggle(self, group: str, label: str):
        btn = self.page.locator(f"flow-toggles[aria-label='{group}'] button[role=radio]", has_text=label).first
        if btn.get_attribute("aria-checked") != "true":
            btn.click()
            self.wait(0.6)

    def configure(self, kind: str = "video", video_mode: str = "frames", aspect: str = "16:9",
                  model: str = "", duration: int = 8, count: int = 2) -> dict:
        """Đặt cài đặt tạo. Trả về chuỗi tóm tắt + số credit Flow báo sẽ tốn."""
        self.back_to_grid()
        self.close_panels()
        mode_toggle = self.page.locator(f"flow-toggles[aria-label='{UI['group_mode']}']").first
        if not (mode_toggle.count() and mode_toggle.is_visible()):
            self.page.locator(UI["settings"]).click()
        mode_toggle.wait_for(timeout=8000)
        self._toggle(UI["group_mode"], UI["kind_video"] if kind == "video" else UI["kind_image"])
        if kind == "video":
            mode_label = UI["mode_frames"] if video_mode in ("frames", "first_frame", "first_last") else UI["mode_ingredients"]
            self.page.get_by_role("radio", name=mode_label).first.click()
            self.wait(0.5)
            self._toggle(UI["group_duration"], f"{duration} giây")
        self._toggle(UI["group_aspect"], aspect)
        self._toggle(UI["group_count"], f"x{count}")
        if model:
            current = self.page.locator(UI["model_trigger"]).first.inner_text()
            if model not in current:
                self.page.locator(UI["model_trigger"]).first.click()
                self.wait(0.8)
                pat = re.compile(rf"(?:^|\s){re.escape(model)}(?:\.1)?\s*$", re.I)
                opt = self.page.locator("[role=menuitem], [role=option], button, li").filter(has_text=pat)
                if opt.count():
                    opt.last.click()
                else:
                    self.page.get_by_text(model, exact=False).last.click()
                self.wait(0.8)
        cost_txt = self.page.locator(UI["credit_label"]).first.inner_text()
        m = re.search(r"(\d[\d.,]*)\s*tín dụng", cost_txt)
        cost = int(re.sub(r"[.,]", "", m.group(1))) if m else None
        self.escape()
        summary = self.page.locator(UI["settings"]).inner_text().replace("\n", " ")
        return {"summary": summary, "credits_per_submit": cost}

    # ------------------------------------------------------------- ô prompt
    def clear_prompt(self):
        """Xóa sạch ô prompt: chữ + frame/thành phần đính kèm (nút ✕ "Xoá câu lệnh" chỉ hiện khi có nội dung)."""
        self.close_panels()
        clear_btn = self.page.locator(UI["clear_prompt"])
        if clear_btn.count() and clear_btn.first.is_visible():
            clear_btn.first.click()
            self.wait(0.8)
        box = self.page.locator(UI["prompt_box"])
        box.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Delete")
        self.wait(0.3)

    def replace_prompt_text(self, text: str) -> bool:
        """Chỉ thay phần văn bản câu lệnh, giữ nguyên các thẻ Ingredients/Voice đang đính kèm trên thanh composer.

        Trả về True nếu giữ được thành phần đính kèm, False nếu cần đính kèm lại.
        """
        self.close_panels()
        box = self.page.locator(UI["prompt_box"])
        box.click()
        # Đếm số thẻ thành phần (chip/button) bên trong khung composer trước khi xóa chữ
        chip_sel = "flow-prompt-chip, [data-ingredient-chip], button[aria-label*='Xoá'], mat-chip"
        chips_before = self.page.locator(chip_sel).count()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        self.wait(0.2)
        chips_after = self.page.locator(chip_sel).count()
        if chips_before > 0 and chips_after == 0:
            return False
        self.type_prompt(text)
        return True

    def type_prompt(self, text: str):
        box = self.page.locator(UI["prompt_box"])
        box.click()
        self.page.keyboard.press("Control+End")
        self.page.keyboard.insert_text((" " if box.inner_text().strip() else "") + text)
        self.wait(0.5)

    def prompt_text(self) -> str:
        return self.page.locator(UI["prompt_box"]).inner_text()

    def close_panels(self):
        """Đóng mọi bảng chọn/popup đang mở (bảng bị bỏ mở sẽ che nút cài đặt và làm hỏng bước sau)."""
        for _ in range(4):
            search = self.page.locator(UI["ingredient_search"])
            backdrop = self.page.locator(".cdk-overlay-backdrop-showing")
            mode_toggle = self.page.locator(f"flow-toggles[aria-label='{UI['group_mode']}']")
            if not (
                (search.count() and search.last.is_visible())
                or (backdrop.count() and backdrop.first.is_visible())
                or (mode_toggle.count() and mode_toggle.first.is_visible())
            ):
                return
            self.escape()

    def _open_ingredients(self):
        self.close_panels()
        plus = self.page.locator(UI["plus"])
        if plus.count() and plus.first.is_visible():
            plus.first.click()
        elif self.page.evaluate(JS_MARK_PLUS, UI["submit"]):
            self.page.locator("[data-studio-plus]").click()
        else:  # chế độ Khung hình không có nút "+": gõ "@" mở bảng thành phần
            self.page.locator(UI["prompt_box"]).click()
            self.page.keyboard.press("Control+End")
            self.page.keyboard.type("@")
        self.page.locator(UI["ingredient_search"]).first.wait_for(timeout=8000)

    def _pick_in_picker(self, path: Path = None, query: str = "", stage_dir: Path = None, uid: str = "") -> None:
        """Trong bảng chọn (thành phần / khung hình): tìm theo tên Unique ID, tải lên nếu chưa có, chọn, thêm vào câu lệnh."""
        if path:
            path = stage_unique_file(Path(path), stage_dir=stage_dir, uid=uid)
        query = query or Path(path).stem
        target = Path(path).name if path else query
        search = self.page.locator(UI["ingredient_search"]).last
        search.fill(query)
        # Chờ phản hồi linh hoạt (0.25s/bước thay vì cố định 1.5s) để tăng tốc khi thành phần đã có sẵn
        for _ in range(6):
            self.wait(0.25)
            if self.page.get_by_text(target, exact=False).count() or self.page.get_by_text(UI["not_found"]).count():
                break
        if path and (self.page.get_by_text(UI["not_found"]).count() or not self.page.get_by_text(Path(path).name).count()):
            with self.page.expect_file_chooser(timeout=10000) as fc:
                self.page.locator("button", has_text=UI["upload_btn"]).last.click()
            fc.value.set_files(str(Path(path).resolve()))
            # Danh sách không tự làm mới theo ô tìm kiếm: xóa rồi gõ lại cho tới khi file vừa tải xuất hiện.
            for _ in range(30):
                self.wait(1.5)
                search.fill("")
                self.wait(0.3)
                search.fill(query)
                self.wait(0.8)
                if self.page.get_by_text(Path(path).name).count():
                    break
            else:
                raise FlowError(f"Tải lên {Path(path).name} nhưng không thấy trong danh sách sau 60s.")
        self.page.get_by_text(target, exact=False).last.click()
        self.wait(0.5)
        add = self.page.get_by_role("button", name=UI["add_to_prompt"], exact=True)
        if add.count():
            add.last.click()
            self.wait(0.5)

    def attach_file(self, path: Path, stage_dir: Path = None, uid: str = ""):
        """Đính ảnh tham chiếu (thành phần) theo tên file / Unique ID — tải lên nếu dự án chưa có."""
        self._open_ingredients()
        self._pick_in_picker(path=path, stage_dir=stage_dir, uid=uid)

    def attach_voice(self, voice: str):
        self._open_ingredients()
        self.page.get_by_text(UI["voices_tab"], exact=True).last.click()
        self.wait(0.5)
        self._pick_in_picker(query=voice)

    def set_start_frame(self, path: Path, stage_dir: Path = None, uid: str = ""):
        self.close_panels()
        self.page.get_by_role("button", name=UI["start_slot"], exact=True).first.click()
        self.page.locator(UI["ingredient_search"]).last.wait_for(timeout=8000)
        self._pick_in_picker(path=path, stage_dir=stage_dir, uid=uid)
        self.wait(0.8)

    def set_end_frame(self, path: Path, stage_dir: Path = None, uid: str = ""):
        self.close_panels()
        self.page.get_by_role("button", name=UI["end_slot"], exact=True).first.click()
        self.page.locator(UI["ingredient_search"]).last.wait_for(timeout=8000)
        self._pick_in_picker(path=path, stage_dir=stage_dir, uid=uid)
        self.wait(0.8)

    def submit(self):
        btn = self.page.locator(UI["submit"])
        if btn.is_disabled():
            raise FlowError("Nút tạo đang bị khóa (thiếu prompt hoặc frame).")
        btn.click()
        self.wait(3)

    # ------------------------------------------------------------- theo dõi & thu về
    def progress(self) -> list:
        return re.findall(r"\b(\d{1,2})%", self.page.evaluate("() => document.body.innerText"))

    def wait_until_done(self, timeout: int = 1200, poll: int = 15) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if not self.progress():
                return True
            self.wait(poll)
        return False

    def _filter(self, label: str):
        self.back_to_grid()
        clicked = self.page.evaluate(
            r"""(lbl) => {
                const wantIcon = /hình ảnh|image/i.test(lbl) ? 'image' : (/video/i.test(lbl) ? 'videocam' : '');
                const allBtns = [...document.querySelectorAll('button, [mat-list-item]')];
                const visBtns = allBtns.filter(b => b.getBoundingClientRect().width > 0 && b.getBoundingClientRect().left < 280);
                for (const pool of [visBtns, allBtns]) {
                    const hit = pool.find(b => {
                        const tc = (b.textContent || '').trim();
                        const it = (b.innerText || '').trim();
                        return tc.includes(lbl) || (wantIcon && (it === wantIcon || it.startsWith(wantIcon + ' ') || tc.startsWith(wantIcon)));
                    });
                    if (hit) { hit.click(); return true; }
                }
                return false;
            }""",
            label,
        )
        if not clicked:
            loc = self.page.get_by_text(label, exact=True).first
            if loc.is_visible():
                loc.click()
        self.wait(2.5)
        self.page.evaluate(JS_SCROLLER, None)
        self.wait(1)

    def _wait_new_file(self, watch_dirs: list, before: set, timeout: int) -> Path:
        t0 = time.time()
        while time.time() - t0 < timeout:
            for d in watch_dirs:
                for f in d.iterdir():
                    if f not in before and f.is_file() and not f.name.endswith((".crdownload", ".tmp")):
                        self.wait(0.8)
                        return f
            self.wait(1.5)
        return None

    def harvest_rows(self, kind: str, prompts: dict, out_dir: Path, skip_shots: set = (), timeout: int = 150,
                     only_shots: set = None, quota: dict = None, known_sha: dict = None,
                     wait_done: bool = False, wait_timeout: int = 1500, on_row=None) -> list:
        """Tải từng HÀNG có prompt khớp shot (Streaming Harvest: tải cuốn chiếu ngay khi hàng vừa xong).

        quota {shot: n}: chỉ tải n hàng MỚI NHẤT của shot (lưới xếp mới → cũ) — tương ứng số job đang chờ;
        shot không có trong quota thì không giới hạn (dự án cũ chưa có nhật ký job).
        known_sha {shot: {sha256}}: hàng cũ đã tải (mọi file trùng take sẵn có) → bỏ, KHÔNG trừ quota.
        wait_done: nếu True, vừa tải cuốn chiếu các hàng đã xong vừa chờ các hàng đang render (%) hoàn tất.
        on_row: callback(row_dict) gọi ngay sau mỗi hàng tải xong để đăng ký take & lưu manifest tức thì.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        quota = dict(quota or {})
        watch = [d for d in (self.download_dir, Path.home() / "Downloads") if d and d.exists()]
        self._filter(UI["filter_video"] if kind == "video" else UI["filter_image"])
        results, done_rows, stall = [], set(), 0
        t0 = time.time()
        while stall < 3:
            texts = self.page.evaluate(JS_ROW_TEXTS, UI["bulk_download"])
            progressed, seen_count = False, {}
            for i, txt in enumerate(texts):
                # Hàng đang render dở (có chỉ báo %) → bỏ qua ở vòng đầu; nếu vòng sau vẫn kẹt 99% nhưng đã có ít nhất 1 video xong (play_arrow) thì vẫn tải.
                if re.search(r"\b\d{1,3}%", txt) and (stall == 0 or kind == "image" or "play_arrow" not in txt):
                    continue
                # Hai hàng có thể trùng chữ (tạo lại cùng prompt) → khóa = chữ + thứ tự xuất hiện.
                seen_count[txt] = seen_count.get(txt, 0) + 1
                key = f"{txt[:200]}#{seen_count[txt]}"
                if key in done_rows:
                    continue
                done_rows.add(key)
                progressed = True
                sid = match_row_to_shot(txt, prompts)
                if not sid or sid in skip_shots or (only_shots and sid not in only_shots):
                    continue
                if sid in quota and quota[sid] <= 0:
                    continue
                if kind == "video" and "Không thành công" in txt and "play_arrow" not in txt:
                    row = {"shot": sid, "error": "Flow báo Không thành công trên cả hàng", "row_text": txt[:120]}
                    results.append(row)
                    if on_row:
                        on_row(row)
                    continue
                btn = self.page.locator(UI["bulk_download"]).nth(i)
                btn.scroll_into_view_if_needed()
                self.wait(0.8)
                # Lưới có thể nạp/xê dịch hàng khi cuộn → xác nhận lại đúng hàng (theo khóa) trước khi bấm.
                keys_now = self._row_keys()
                if i >= len(keys_now) or keys_now[i] != key:
                    if key not in keys_now:
                        row = {"shot": sid, "error": "hàng bị xê dịch, không tìm lại được", "row_text": txt[:120]}
                        results.append(row)
                        if on_row:
                            on_row(row)
                        continue
                    i = keys_now.index(key)
                    btn = self.page.locator(UI["bulk_download"]).nth(i)
                    btn.scroll_into_view_if_needed()
                before = {f for d in watch for f in d.iterdir()}
                partial_hung = kind == "video" and bool(re.search(r"\b\d{1,3}%", txt)) and "play_arrow" in txt
                got = None
                files = []
                if not partial_hung:
                    btn.click()
                    got = self._wait_new_file(watch, before, timeout)
                    if got:
                        files = _unpack(got, out_dir, kind)
                if not files and kind == "video" and "play_arrow" in txt:
                    n_tiles = max(1, int(self.page.evaluate(JS_ROW_TILES, [UI["bulk_download"], i, -1]) or 1))
                    for ti in range(n_tiles):
                        try:
                            ri_cur = self._find_row(key) if ti > 0 else i
                            if ri_cur is None:
                                break
                            self.page.evaluate(JS_ROW_TILES, [UI["bulk_download"], ri_cur, ti])
                            self.page.wait_for_url(re.compile(r"/edit/"), timeout=15000)
                            self.wait(1.5)
                            single = self._download_from_editor("720", watch, timeout)
                            if single:
                                files.extend(_unpack(single, out_dir, kind))
                        except Exception:
                            pass
                        finally:
                            if "/edit/" in self.page.url:
                                self._filter(UI["filter_video"])
                if not files:
                    row = {"shot": sid, "error": "timeout", "row_text": txt[:120]}
                    results.append(row)
                    if on_row:
                        on_row(row)
                    continue
                known = (known_sha or {}).get(sid)
                if known and files and all(media.sha256_file(f) in known for f in files):
                    for f in files:
                        Path(f).unlink(missing_ok=True)
                    row = {"shot": sid, "skipped": "hàng cũ đã có trong take", "row_text": txt[:120]}
                    results.append(row)
                    if on_row:
                        on_row(row)
                    continue
                if sid in quota:
                    quota[sid] -= 1
                row = {"shot": sid, "files": [str(f) for f in files], "row_text": txt[:120]}
                results.append(row)
                if on_row:
                    on_row(row)
                self.wait(1.0)
            targets = only_shots or set(quota)
            if quota and targets and all(quota.get(s, 1) <= 0 for s in targets):
                break  # đã đủ mọi hàng cần tải — không quét tiếp lưới cũ
            stall = 0 if progressed else stall + 1
            if stall >= 3 and wait_done and (time.time() - t0 < wait_timeout) and self.progress():
                # Vẫn còn hàng đang render (%) trên đầu lưới → cuộn về đầu trang chờ cuốn chiếu
                self.page.evaluate(JS_SCROLLER, None)
                self.wait(8.0)
                stall = 0
                continue
            self.page.evaluate(JS_SCROLLER, 800)
            self.wait(1.2)
        return results

    # ------------------------------------------------------------- upscale 1080p
    def _download_from_editor(self, res: str, watch: list, timeout: int) -> Path:
        before = {f for d in watch for f in d.iterdir()}
        self.page.locator(UI["editor_download"]).first.click()
        self.wait(1.2)
        self.page.get_by_role("menuitem", name=f"{res}p").first.click()
        return self._wait_new_file(watch, before, timeout)

    def _open_any_video_editor(self):
        if "/edit/" in self.page.url:
            return
        self._filter(UI["filter_video"])
        self.page.evaluate(JS_ROW_TILES, [UI["bulk_download"], 0, 0])
        self.page.wait_for_url(re.compile(r"/edit/"), timeout=20000)
        self.wait(2)

    def upscale_takes(self, prompts: dict, wanted: dict, out_dir: Path, match_fn, res: str = "1080",
                      timeout: int = 420, on_result=None) -> list:
        """Upscale LẦN LƯỢT các clip cần (wanted: {key: {shot, take, dest, ...}}).

        Duyệt dải ảnh thu nhỏ của trình chỉnh sửa (mọi clip của dự án, không phụ thuộc lưới tải lười):
        clip có prompt khớp shot cần → tải bản 720p gốc (nhanh) → match_fn(file, pending) -> key của take
        → đúng clip thì tải bản {res}p về dest. Lỗi ở một clip không làm hỏng cả lượt; on_result(r) gọi ngay
        sau mỗi clip để lưu tiến độ.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        watch = [d for d in (self.download_dir, Path.home() / "Downloads") if d and d.exists()]
        shots_needed = {w["shot"] for w in wanted.values()}
        pending, results, seen = dict(wanted), [], set()
        if any(w.get("tile_index") is not None for w in pending.values()):
            self.back_to_grid()
            self._upscale_via_grid(prompts, pending, watch, match_fn, res, timeout, results, on_result)
            if not pending:
                return results
        self._open_any_video_editor()
        n = self.page.evaluate(JS_STRIP, -1)
        for i in range(n):
            if not pending:
                break
            try:
                self.page.evaluate(JS_STRIP, i)
                self.wait(2.5)
                edit_id = self.page.url.rsplit("/", 1)[-1]
                if edit_id in seen:
                    continue
                seen.add(edit_id)
                sid = match_row_to_shot(self.page.evaluate("() => document.body.innerText"), prompts)
                if sid not in shots_needed:
                    continue
                small = self._download_from_editor("720", watch, 120)
                key = match_fn(small, pending) if small else None
                if small:
                    small.unlink(missing_ok=True)
                hit = pending.get(key) if key else None
                if not hit:
                    continue
                big = self._download_from_editor(res, watch, timeout)
                pending.pop(key, None)
                if big:
                    dest = Path(hit["dest"])
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    big.replace(dest)
                    r = {**hit, "dest": str(dest), "edit_id": edit_id}
                else:
                    r = {**hit, "error": f"timeout chờ upscale {res}p"}
                results.append(r)
                if on_result:
                    on_result(r)
            except Exception as e:  # noqa: BLE001 — bỏ qua clip lỗi (vd. ảnh, menu khác), tiếp tục clip sau
                self.escape(2)
                results.append({"strip_index": i, "skipped": str(e)[:120]})
        if pending:  # dải thu nhỏ chỉ hiện một phần dự án → quét nốt qua lưới, tìm hàng theo nội dung
            self.back_to_grid()
            self._upscale_via_grid(prompts, pending, watch, match_fn, res, timeout, results, on_result)
        results += [{**w, "error": "không tìm thấy clip trên Flow"} for w in pending.values()]
        return results

    def _row_keys(self) -> list:
        texts = self.page.evaluate(JS_ROW_TEXTS, UI["bulk_download"])
        seen, keys = {}, []
        for txt in texts:
            seen[txt] = seen.get(txt, 0) + 1
            keys.append(f"{txt[:200]}#{seen[txt]}")
        return keys

    def _find_row(self, key: str, max_scroll: int = 40):
        """Cuộn lưới tới khi hàng có khóa `key` được nạp; trả về chỉ số hàng hoặc None."""
        self.page.evaluate(JS_SCROLLER, None)
        self.wait(1)
        for _ in range(max_scroll):
            keys = self._row_keys()
            if key in keys:
                return keys.index(key)
            self.page.evaluate(JS_SCROLLER, 700)
            self.wait(1.2)
        return None

    def _upscale_via_grid(self, prompts, pending, watch, match_fn, res, timeout, results, on_result):
        shots_needed = {w["shot"] for w in pending.values()}
        self._filter(UI["filter_video"])
        targets, last = [], None
        for _ in range(40):  # gom khóa các hàng cần (cuộn hết lưới)
            for k in self._row_keys():
                if k not in targets and match_row_to_shot(k.rsplit("#", 1)[0], prompts) in shots_needed:
                    targets.append(k)
            pos = self.page.evaluate(JS_SCROLLER, 700)
            self.wait(1.2)
            if pos == last:
                break
            last = pos
        grid_url = self.page.url
        for key in targets:
            ri = self._find_row(key)
            if ri is None:
                continue
            row_sid = match_row_to_shot(key.rsplit("#", 1)[0], prompts)
            n_tiles = self.page.evaluate(JS_ROW_TILES, [UI["bulk_download"], ri, -1])
            # Ưu tiên mở thẳng ô `tile_index` đã ghi nhận lúc harvest (bỏ qua bước tải nháp 720p nếu khớp duy nhất)
            direct_candidates = [
                (k_sha, w) for k_sha, w in pending.items()
                if w["shot"] == row_sid and w.get("tile_index") is not None and 0 <= int(w["tile_index"]) < n_tiles
            ]
            tile_order = [int(w["tile_index"]) for _, w in direct_candidates]
            tile_order += [t for t in range(n_tiles) if t not in tile_order]
            for ti in tile_order:
                if not pending:
                    return
                try:
                    ri = self._find_row(key)
                    self.page.evaluate(JS_ROW_TILES, [UI["bulk_download"], ri, ti])
                    self.page.wait_for_url(re.compile(r"/edit/"), timeout=20000)
                    self.wait(2)
                    direct_hit = next(
                        ((k_sha, w) for k_sha, w in direct_candidates if int(w["tile_index"]) == ti and w.get("single_job", True)),
                        None,
                    )
                    if direct_hit:
                        k, hit = direct_hit
                    else:
                        small = self._download_from_editor("720", watch, 120)
                        k = match_fn(small, pending) if small else None
                        if small:
                            small.unlink(missing_ok=True)
                        hit = pending.get(k) if k else None
                    if hit:
                        big = self._download_from_editor(res, watch, timeout)
                        pending.pop(k, None)
                        if big:
                            dest = Path(hit["dest"])
                            big.replace(dest)
                            r = {**hit, "dest": str(dest), "edit_id": self.page.url.rsplit("/", 1)[-1], "direct_tile": bool(direct_hit)}
                        else:
                            r = {**hit, "error": f"timeout chờ upscale {res}p"}
                        results.append(r)
                        if on_result:
                            on_result(r)
                except Exception as e:  # noqa: BLE001
                    results.append({"grid_row": key[:60], "tile": ti, "skipped": str(e)[:120]})
                finally:
                    if "/edit/" in self.page.url:
                        self.page.go_back()
                        self.wait(2.5)
                    if "/edit/" in self.page.url or "flow.google.com/project" not in self.page.url:
                        self.page.goto(grid_url, wait_until="domcontentloaded")
                        self.wait(2.5)
                        self._filter(UI["filter_video"])


def _unpack(path: Path, out_dir: Path, kind: str) -> list:
    """Giải nén zip tải hàng loạt (hoặc chuyển file đơn) vào out_dir; chỉ giữ đúng loại media."""
    exts = (".mp4",) if kind == "video" else (".jpg", ".jpeg", ".png", ".webp")
    stamp = time.strftime("%H%M%S")
    files = []
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            infos = sorted(zf.infolist(), key=lambda x: x.filename)
            for k, info in enumerate(infos):
                if info.filename.lower().endswith(exts):
                    dst = out_dir / f"{stamp}_{k}{Path(info.filename).suffix.lower()}"
                    dst.write_bytes(zf.read(info))
                    files.append(dst)
        path.unlink()
    elif path.suffix.lower() in exts:
        dst = out_dir / f"{stamp}_0{path.suffix.lower()}"
        path.replace(dst)
        files.append(dst)
    return files
