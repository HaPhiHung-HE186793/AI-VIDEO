"""Cầu nối trình duyệt cho AI agent: điều khiển Chrome đang mở (cổng debug) để thao tác Google Flow / Gemini / Drive.

Mỗi lệnh kết nối vào Chrome thật của người dùng (profile đã đăng nhập), làm 1 thao tác, rồi chụp màn hình
để agent xem kết quả và quyết định bước tiếp. Không giả mạo dấu hiệu tự động hóa.

Người dùng đã cho phép tự động hóa tài khoản của mình; rủi ro điều khoản dịch vụ đã được thông báo.
"""

import time
from pathlib import Path

from .config import ROOT_DIR

SHOTS_DIR = ROOT_DIR / ".browser"


class BrowserError(Exception):
    pass


def _connect(port: int):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise BrowserError("Thiếu playwright: pip install playwright") from e
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    except Exception as e:  # noqa: BLE001
        pw.stop()
        raise BrowserError(f"Không kết nối được Chrome cổng {port}. Chạy `check-browser --launch` trước. ({e})") from e
    return pw, browser


def _pick_page(browser, match: str = ""):
    pages = [p for ctx in browser.contexts for p in ctx.pages]
    if not pages:
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        return ctx.new_page()
    if match:
        for p in pages:
            if match in p.url:
                return p
    return pages[-1]


def _snap(page, name: str) -> str:
    SHOTS_DIR.mkdir(exist_ok=True)
    path = SHOTS_DIR / f"{time.strftime('%H%M%S')}_{name}.png"
    page.screenshot(path=str(path))
    return str(path)


def run(action: str, port: int = 9222, tab: str = "", **kw) -> dict:
    """Thực hiện 1 thao tác. action: tabs | goto | shot | click | type | press | scroll | wait | text | download."""
    pw, browser = _connect(port)
    try:
        if action == "tabs":
            return {"tabs": [{"url": p.url, "title": p.title()} for ctx in browser.contexts for p in ctx.pages]}
        page = _pick_page(browser, tab)
        page.bring_to_front()
        res = {}
        if action == "goto":
            page.goto(kw["url"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
        elif action == "click":
            if kw.get("x") is not None:
                page.mouse.click(kw["x"], kw["y"])
            elif kw.get("text"):
                # nth: chọn phần tử thứ n khi chữ xuất hiện nhiều lần (-1 = cuối cùng, vd. trong popup vẽ sau cùng)
                page.get_by_text(kw["text"], exact=kw.get("exact", False)).nth(kw.get("nth", 0)).click(timeout=10000)
            elif kw.get("role"):
                page.get_by_role(kw["role"], name=kw.get("name")).first.click(timeout=10000)
            else:
                page.locator(kw["selector"]).first.click(timeout=10000)
            page.wait_for_timeout(1500)
        elif action == "type":
            if kw.get("selector"):
                page.locator(kw["selector"]).first.fill(kw["value"], timeout=10000)
            else:
                page.keyboard.type(kw["value"], delay=15)
            page.wait_for_timeout(500)
        elif action == "press":
            page.keyboard.press(kw["key"])
            page.wait_for_timeout(1000)
        elif action == "scroll":
            page.mouse.wheel(0, kw.get("dy", 600))
            page.wait_for_timeout(800)
        elif action == "wait":
            page.wait_for_timeout(int(kw.get("seconds", 5) * 1000))
        elif action == "count":
            res["count"] = page.get_by_text(kw["text"], exact=kw.get("exact", False)).count()
        elif action == "text":
            res["text"] = page.inner_text("body")[: kw.get("limit", 4000)]
        elif action == "upload":
            # Nhiều trang chỉ tạo ô chọn file sau khi bấm nút (vd. "+" của Flow): bấm --xy/--text trước nếu có.
            if kw.get("x") is not None or kw.get("text"):
                try:
                    with page.expect_file_chooser(timeout=8000) as fc:
                        if kw.get("x") is not None:
                            page.mouse.click(kw["x"], kw["y"])
                        else:
                            page.get_by_text(kw["text"]).first.click()
                    fc.value.set_files(kw["files"])
                except Exception:  # noqa: BLE001 — không có hộp thoại: thử ô file ẩn vừa xuất hiện
                    page.locator("input[type=file]").first.set_input_files(kw["files"], timeout=8000)
            else:
                page.locator(kw.get("selector") or "input[type=file]").first.set_input_files(kw["files"], timeout=15000)
            page.wait_for_timeout(3000)
        elif action == "download":
            # expect_download không hoạt động ổn với Chrome gắn qua CDP → dùng Browser.setDownloadBehavior
            # để Chrome lưu thẳng vào thư mục tạm, rồi chờ file tải xong.
            dest = Path(kw["dest"]).resolve()
            tmp = dest.parent / "_downloading"
            tmp.mkdir(parents=True, exist_ok=True)
            before = set(tmp.iterdir())
            cdp = browser.new_browser_cdp_session()
            cdp.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(tmp)})
            if kw.get("x") is not None:
                page.mouse.click(kw["x"], kw["y"])
            else:
                page.get_by_text(kw["text"]).first.click(timeout=10000)
            deadline = time.time() + kw.get("timeout", 180)
            got = None
            while time.time() < deadline:
                new = [f for f in tmp.iterdir() if f not in before and not f.name.endswith((".crdownload", ".tmp"))]
                if new:
                    got = new[0]
                    break
                page.wait_for_timeout(1000)
            if not got:
                raise BrowserError("Hết thời gian chờ tải file (Flow có thể đang upscale — thử lại sau).")
            page.wait_for_timeout(500)
            got.replace(dest)
            res["downloaded"] = str(dest)
        elif action != "shot":
            raise BrowserError(f"Thao tác không hỗ trợ: {action}")
        res.update(url=page.url, screenshot=_snap(page, action),
                   viewport=page.viewport_size or page.evaluate("({width: innerWidth, height: innerHeight})"))
        return res
    finally:
        # Chỉ ngắt kết nối CDP — KHÔNG đóng Chrome của người dùng.
        pw.stop()
