"""
eCurricula Portal Upload — production-grade Playwright automation.

Credentials are read EXCLUSIVELY from environment variables:
  PORTAL_USERNAME   — faculty SRM ID
  PORTAL_PASSWORD   — portal password
  PORTAL_HEADLESS   — "1" for headless (default), "0" for visible (dev only)
  PORTAL_PRODUCTION — "1" disables debug screenshots

Invoked by server.py via asyncio.create_subprocess_exec — never call directly
with credentials as CLI args.
"""

import argparse
import asyncio
import html
import json
import logging
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ── config from environment ───────────────────────────────────────────────────

PORTAL_URL = "https://dld.srmist.edu.in/etecurricula/#/"
# Set by the server per active course; falls back to the original course.
COURSE_CODE = os.environ.get("PORTAL_COURSE_CODE", "21CSE597T")

HEADLESS: bool = os.environ.get("PORTAL_HEADLESS", "1") != "0"
PRODUCTION: bool = os.environ.get("PORTAL_PRODUCTION", "0") == "1"
# The portal login has a captcha. When running with a visible browser we fill the
# credentials, then wait for the operator to solve the captcha and submit.
# Defaults: on when headful, off when headless (a headless run cannot solve it).
MANUAL_LOGIN: bool = os.environ.get("PORTAL_MANUAL_LOGIN", "0" if HEADLESS else "1") != "0"
LOGIN_WAIT_SECONDS: int = int(os.environ.get("PORTAL_LOGIN_TIMEOUT", "300"))
SESSIONS_PER_UNIT = 9
SLOS_PER_SESSION = 2

# ── logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,  # server.py reads stdout; stderr goes to server log only
)
logger = logging.getLogger("portal-upload")


# ── helpers ───────────────────────────────────────────────────────────────────

def zip_pptx(pptx_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / (pptx_path.stem + ".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pptx_path, pptx_path.name)
    size_mb = zip_path.stat().st_size / 1_048_576
    if size_mb > 1.0:
        logger.warning("ZIP %s is %.2fMB — portal limit is 1MB", zip_path.name, size_mb)
    return zip_path


async def screenshot_on_error(page, label: str, output_root: Path) -> None:
    if PRODUCTION:
        return
    try:
        path = output_root / f"debug_{label}.png"
        await page.screenshot(path=str(path), full_page=True)
        logger.info("Debug screenshot: %s", path.name)
        # Auto-delete after 1h so portal DOM doesn't linger on disk
        asyncio.get_event_loop().call_later(3600, lambda: path.unlink(missing_ok=True))
    except Exception:
        pass
    # Also dump the DOM so selectors can be diagnosed from the real markup
    await dump_dom(page, label, output_root)


def purge_debug_captures(output_root: Path) -> None:
    """Delete debug/DOM/recon captures — they hold the portal's logged-in DOM."""
    removed = 0
    for pattern in ("dom_*.html", "debug_*.png", "recon_*"):
        for f in output_root.glob(pattern):
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
    if removed:
        logger.info("Purged %d debug capture(s) from previous runs", removed)


async def dump_dom(page, label: str, output_root: Path) -> None:
    """Save the current page HTML for selector debugging (non-production only)."""
    if PRODUCTION:
        return
    try:
        html = await page.content()
        path = output_root / f"dom_{label}.html"
        path.write_text(html, encoding="utf-8")
        logger.info("DOM dump: %s (%d bytes) url=%s", path.name, len(html), page.url)
        asyncio.get_event_loop().call_later(3600, lambda: path.unlink(missing_ok=True))
    except Exception as e:
        logger.warning("DOM dump failed for %s: %s", label, e)


# ── login ─────────────────────────────────────────────────────────────────────

async def _wait_for_login(page) -> bool:
    """Poll until the login form is gone (login succeeded). Used in manual mode."""
    deadline = asyncio.get_event_loop().time() + LOGIN_WAIT_SECONDS
    while asyncio.get_event_loop().time() < deadline:
        try:
            if await page.locator("input[type='password']").count() == 0:
                # Give the post-login SPA route a moment to settle.
                await page.wait_for_load_state("networkidle", timeout=10000)
                return True
        except Exception:
            pass
        await asyncio.sleep(1.5)
    return False


async def login(page, username: str, password: str, output_root: Path) -> bool:
    logger.info("Navigating to portal")
    await page.goto(PORTAL_URL, wait_until="networkidle")
    await dump_dom(page, "01_landing_page", output_root)

    try:
        # The "#/" route is a landing page with role cards. The username/password
        # form lives behind the "Login Here" button — click it first.
        if await page.get_by_text("Login Here", exact=False).count():
            logger.info("Landing page detected — clicking 'Login Here'")
            await page.get_by_text("Login Here", exact=False).first.click(timeout=8000)
            await page.wait_for_load_state("networkidle", timeout=15000)

        # Wait for the actual credential form to render (Angular/Ant Design).
        await page.wait_for_selector("input", timeout=15000)
        await dump_dom(page, "02_login_form", output_root)

        # Pre-fill credentials only if they were supplied (convenience). In the
        # normal manual flow the professor types their own — we may have none.
        if username:
            user_field = page.locator(
                "input[type='text'], input[type='email'], input:not([type]):not([type='password'])"
            ).first
            await user_field.fill(username, timeout=8000)
        if password:
            await page.locator("input[type='password']").first.fill(password, timeout=8000)

        if MANUAL_LOGIN:
            # The portal requires a captcha — hand control to the operator.
            logger.info("=" * 60)
            logger.info("ACTION NEEDED: solve the captcha and click LOGIN in the")
            logger.info("browser window. Credentials are already filled in.")
            logger.info("Waiting up to %d seconds for login to complete...", LOGIN_WAIT_SECONDS)
            logger.info("=" * 60)
            if await _wait_for_login(page):
                logger.info("Login detected — continuing")
                await dump_dom(page, "03_after_login", output_root)
                return True
            logger.error("Timed out waiting for manual login")
            await screenshot_on_error(page, "login_failed", output_root)
            return False

        # Headless path: no captcha solver available — attempt direct submit.
        submit = page.locator("button[type='submit'], input[type='submit']")
        if await submit.count():
            await submit.first.click(timeout=5000)
        else:
            await page.get_by_role(
                "button", name=re.compile(r"log\s*in|sign\s*in|submit", re.I)
            ).first.click(timeout=5000)

        await page.wait_for_load_state("networkidle", timeout=20000)
        await dump_dom(page, "03_after_login", output_root)

        # Still seeing a password field => credentials rejected / still on form.
        if await page.locator("input[type='password']").count():
            logger.error("Password field still present after submit — login likely failed")
            logger.error("(The portal uses a captcha; run headful with PORTAL_HEADLESS=0 to solve it.)")
            await screenshot_on_error(page, "login_failed", output_root)
            return False
        logger.info("Login successful")
        return True
    except PWTimeout as e:
        logger.error("Login timed out: %s", e)
        await screenshot_on_error(page, "login_timeout", output_root)
        return False


# ── portal interaction (selectors from recon captures, 2026-07-02) ────────────
#
# Post-login we land directly on the course's Content Management page — no
# navigation needed. Content types are segments of a D3 sunburst chart; each
# segment click reveals a panel below the chart:
#   PPTx       → "PPTx Source (ZIP)": Choose Unit (ant-select #UNIT, options 1-5),
#                then Session 1..9 rows, each with SLO 1 / SLO 2 hidden
#                <input type="file" accept=".zip"> (18 inputs total, 1MB limit)
#   L Material → "Learning Material": Unit 1..5 rows, each with a hidden
#                <input type="file" accept=".pdf"> (5MB limit)

async def select_unit(page, unit_num: int, output_root: Path) -> bool:
    """Choose a unit in the PPTx panel's ant-select (#UNIT) dropdown."""
    try:
        selector = page.locator(".ant-select", has=page.locator("input#UNIT"))
        current = await selector.locator(".ant-select-selection-item").inner_text()
        if current.strip() == str(unit_num):
            return True
        await selector.click(timeout=5000)
        await asyncio.sleep(0.3)
        option = page.locator(f".ant-select-item[title='{unit_num}']").or_(
            page.locator(".ant-select-item", has_text=str(unit_num))
        )
        await option.first.click(timeout=5000)
        await asyncio.sleep(0.7)  # table re-renders for the new unit
        return True
    except Exception as e:
        logger.error("Could not select unit %d: %s", unit_num, str(e)[:200])
        await screenshot_on_error(page, f"select_unit_{unit_num}", output_root)
        return False


async def _confirm_upload(page, list_idx: int, kind: str = ".zip", timeout_s: int = 30) -> str:
    """Watch the ant-upload-list belonging to slot `list_idx` for the outcome.

    Ant Design marks the list item with -uploading / -done / -error classes.
    The upload lists appear in the same document order as their file inputs,
    so the same index addresses both.
    """
    deadline = asyncio.get_event_loop().time() + timeout_s
    last_cls = ""
    while asyncio.get_event_loop().time() < deadline:
        try:
            lst = page.locator(".ant-upload-list").nth(list_idx)
            item = lst.locator(".ant-upload-list-item").last
            if await item.count():
                last_cls = (await item.get_attribute("class")) or ""
                if "ant-upload-list-item-done" in last_cls:
                    return "ok"
                if "ant-upload-list-item-error" in last_cls:
                    return "error (portal rejected the upload)"
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return f"no_confirm (last state: {last_cls or 'no list item'})"


# ── conflict scan (existing uploads) ─────────────────────────────────────────
# Faculty may have uploaded files manually. Before uploading, scan every slot's
# status chip ("Empty" = vacant) and, in ask-mode, pause until the professor
# chooses replace/skip in the CurriculAI UI (relayed via a decision file).

async def scan_occupancy(page, modules: list[int], output_root: Path) -> dict:
    """Return {unit: {"pptx": [...], "resources": [...], "lm": true}} occupancy."""
    conflicts: dict = {}

    for segment, key in (("PPTx", "pptx"), ("Resources", "resources")):
        for unit in modules:
            if not await click_sunburst_segment(page, segment):
                break
            if not await select_unit(page, unit, output_root):
                continue
            tags = page.locator(".ant-descriptions .ant-tag")
            n = await tags.count()
            expected = SESSIONS_PER_UNIT * SLOS_PER_SESSION
            if n != expected:
                logger.warning("scan: expected %d chips, found %d (%s unit %d) — skipping",
                               expected, n, segment, unit)
                continue
            texts = await tags.all_inner_texts()
            occupied = [
                f"s{i // SLOS_PER_SESSION + 1}_slo{i % SLOS_PER_SESSION + 1}"
                for i, t in enumerate(texts)
                if t.strip() and t.strip().lower() != "empty"
            ]
            if occupied:
                conflicts.setdefault(unit, {})[key] = occupied
            logger.info("scan: unit %d %s — %d/%d slots occupied",
                        unit, segment, len(occupied), expected)

    if await click_sunburst_segment(page, "L Material"):
        tags = page.locator(".ant-descriptions .ant-tag")
        texts = await tags.all_inner_texts()
        for unit in modules:
            idx = unit - 1
            if idx < len(texts) and texts[idx].strip() and texts[idx].strip().lower() != "empty":
                conflicts.setdefault(unit, {})["lm"] = True
                logger.info("scan: unit %d Learning Material occupied", unit)

    return conflicts


async def wait_for_decision(decision_file: Path, timeout_s: int = 900) -> str:
    """Poll for the professor's replace/skip decision written by the server."""
    deadline = asyncio.get_event_loop().time() + timeout_s
    while asyncio.get_event_loop().time() < deadline:
        if decision_file.exists():
            try:
                decision = json.loads(decision_file.read_text()).get("decision", "")
                if decision in ("replace", "skip"):
                    return decision
            except Exception:
                pass
        await asyncio.sleep(2)
    logger.warning("No decision within %ds — defaulting to SKIP (safe)", timeout_s)
    return "skip"


# ── upload PPTx source ────────────────────────────────────────────────────────

async def upload_pptx_source(page, unit_num: int, output_root: Path, limit: int = 0,
                             skip_keys: set = None, segment: str = "PPTx") -> dict:
    """Upload the 18 session/SLO zips to a sunburst segment's panel.

    Used for both "PPTx" (PPTx Source) and "Resources" (Additional Resources) —
    the two panels are structurally identical, and faculty want the same zips
    in both places.
    """
    logger.info("%s — Unit %d", segment, unit_num)
    skip_keys = skip_keys or set()
    ppt_dir = output_root / f"unit_{unit_num}" / "ppts"
    if not ppt_dir.exists():
        logger.warning("No PPTs for unit %d", unit_num)
        return {"skipped": True}

    all_ppts = sorted(ppt_dir.glob("*.pptx"))
    logger.info("Found %d PPT files for unit %d", len(all_ppts), unit_num)
    tmp_dir = output_root / f"unit_{unit_num}" / "_zips"
    results = {}

    if not await click_sunburst_segment(page, segment):
        return {"error": f"{segment} segment not found"}
    if not await select_unit(page, unit_num, output_root):
        return {"error": "unit select failed"}

    # The 18 upload triggers appear in strict document order: S1/SLO1, S1/SLO2,
    # S2/SLO1, ... — address them by index. IMPORTANT: we must CLICK the real
    # button (not set files on the hidden input): the app's click handler is
    # what records the slot's target path. Bypassing it uploads to an empty
    # path and the server 500s with EISDIR.
    triggers = page.locator(".ant-upload[role='button']:has(input[accept='.zip'])")
    n_inputs = await triggers.count()
    expected = SESSIONS_PER_UNIT * SLOS_PER_SESSION
    if n_inputs != expected:
        logger.error("Expected %d zip upload buttons, found %d — aborting PPTx for unit %d",
                     expected, n_inputs, unit_num)
        await screenshot_on_error(page, f"bad_input_count_u{unit_num}", output_root)
        return {"error": f"found {n_inputs} upload buttons, expected {expected}"}

    done = 0
    for session in range(1, SESSIONS_PER_UNIT + 1):
        for slo in range(1, SLOS_PER_SESSION + 1):
            if limit and done >= limit:
                logger.info("Reached --limit %d, stopping PPTx uploads", limit)
                return results

            key = f"s{session}_slo{slo}"
            if key in skip_keys:
                logger.info("Keeping existing upload — unit=%d %s (professor's choice)",
                            unit_num, key)
                results[key] = "kept_existing"
                continue
            idx = (session - 1) * SLOS_PER_SESSION + (slo - 1)
            if idx >= len(all_ppts):
                logger.warning("Missing PPT unit=%d session=%d slo=%d", unit_num, session, slo)
                results[key] = "missing"
                continue

            zip_file = zip_pptx(all_ppts[idx], tmp_dir)
            try:
                async with page.expect_file_chooser(timeout=8000) as fc_info:
                    await triggers.nth(idx).click()
                fc = await fc_info.value
                await fc.set_files(str(zip_file))
                status = await _confirm_upload(page, idx)
                results[key] = status
                done += 1
                if status.startswith("ok"):
                    logger.info("Uploaded unit=%d session=%d slo=%d", unit_num, session, slo)
                else:
                    logger.warning("Upload not confirmed unit=%d %s: %s", unit_num, key, status)
                    await screenshot_on_error(page, f"no_confirm_u{unit_num}_{key}", output_root)
            except Exception as e:
                results[key] = "error"
                done += 1
                logger.error("Upload error unit=%d %s: %s", unit_num, key, str(e)[:200])
                await screenshot_on_error(page, f"error_u{unit_num}_{key}", output_root)
            await asyncio.sleep(0.8)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    ok = sum(1 for v in results.values() if str(v).startswith("ok"))
    logger.info("%s unit %d done: %d/%d uploaded", segment, unit_num, ok, len(results))
    return results


# ── upload learning material ──────────────────────────────────────────────────

async def upload_learning_material(page, unit_num: int, output_root: Path,
                                   skip: bool = False) -> dict:
    if skip:
        logger.info("Keeping existing Learning Material — unit %d (professor's choice)", unit_num)
        return {"status": "kept_existing"}
    logger.info("Learning Material — Unit %d", unit_num)
    pdf_path = output_root / f"unit_{unit_num}" / f"unit_{unit_num}_learning_material.pdf"
    if not pdf_path.exists():
        logger.warning("PDF not found for unit %d", unit_num)
        return {"skipped": True}

    size_mb = pdf_path.stat().st_size / 1_048_576
    if size_mb > 5.0:
        logger.error("PDF unit %d is %.2fMB — exceeds 5MB portal limit", unit_num, size_mb)
        return {"error": "exceeds_5mb"}

    if not await click_sunburst_segment(page, "L Material"):
        return {"error": "L Material segment not found"}

    try:
        # PDF upload buttons appear in unit order (Unit 1..5) — click the real
        # button so the app records the target path (see PPTx note above).
        triggers = page.locator(".ant-upload[role='button']:has(input[accept='.pdf'])")
        n_inputs = await triggers.count()
        if n_inputs < unit_num:
            logger.error("Found %d pdf upload buttons, need index %d", n_inputs, unit_num)
            await screenshot_on_error(page, f"lm_bad_input_count_u{unit_num}", output_root)
            return {"error": f"found {n_inputs} pdf upload buttons"}

        async with page.expect_file_chooser(timeout=8000) as fc_info:
            await triggers.nth(unit_num - 1).click()
        fc = await fc_info.value
        await fc.set_files(str(pdf_path))
        status = await _confirm_upload(page, unit_num - 1)
        if status.startswith("ok"):
            logger.info("Learning Material uploaded for unit %d", unit_num)
            return {"status": status}
        logger.warning("LM upload not confirmed unit %d: %s", unit_num, status)
        await screenshot_on_error(page, f"lm_no_confirm_u{unit_num}", output_root)
        return {"status": status}
    except Exception as e:
        logger.error("Learning material error unit=%d: %s", unit_num, str(e)[:200])
        await screenshot_on_error(page, f"lm_error_u{unit_num}", output_root)
        return {"error": "upload_failed"}


# ── recon mode ────────────────────────────────────────────────────────────────
# Walks the portal after login, capturing DOM + screenshot + a clickable-element
# inventory at every step. Attempts NO uploads. One recon run gives us the real
# markup needed to write correct selectors for the actual upload flow.

async def recon_capture(page, label: str, output_root: Path) -> None:
    logger.info("[recon] capturing: %s (url=%s)", label, page.url)
    try:
        await page.screenshot(path=str(output_root / f"recon_{label}.png"), full_page=True)
    except Exception as e:
        logger.warning("[recon] screenshot failed for %s: %s", label, e)
    try:
        html = await page.content()
        (output_root / f"recon_{label}.html").write_text(html, encoding="utf-8")
    except Exception as e:
        logger.warning("[recon] dom dump failed for %s: %s", label, e)
    # Inventory of everything clickable — the cheat sheet for selector writing.
    try:
        inventory = await page.evaluate(
            """() => {
                const els = document.querySelectorAll(
                    'a, button, [role=button], input, select, [onclick], [class*="click"], [class*="upload"]');
                return Array.from(els).slice(0, 400).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.getAttribute('type') || '',
                    text: (el.innerText || el.value || '').trim().slice(0, 80),
                    cls: (el.className || '').toString().slice(0, 120),
                    id: el.id || '',
                }));
            }"""
        )
        import json as _json
        (output_root / f"recon_{label}_clickables.json").write_text(
            _json.dumps(inventory, indent=1), encoding="utf-8"
        )
    except Exception as e:
        logger.warning("[recon] clickable inventory failed for %s: %s", label, e)


async def click_sunburst_segment(page, label: str) -> bool:
    """Click a segment of the D3 sunburst chart by its label.

    The labels are SVG <textPath> elements with pointer-events:none, so normal
    text clicks never reach the chart. The click handler lives on the sibling
    `path.sunburst-main-arc`, which we fire via a dispatched MouseEvent.
    """
    ok = await page.evaluate(
        """(label) => {
            const tps = Array.from(document.querySelectorAll('textPath'));
            const tp = tps.find(t => t.textContent.trim() === label);
            if (!tp) return false;
            const g = tp.closest('g');
            const arc = g && g.querySelector('path.sunburst-main-arc');
            if (!arc) return false;
            arc.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            return true;
        }""",
        label,
    )
    if ok:
        logger.info("clicked sunburst segment: %s", label)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except PWTimeout:
            pass
        await asyncio.sleep(0.8)
    else:
        logger.warning("sunburst segment not found: %s", label)
    return ok


# Segments worth mapping for uploads. Resources (gets the same PPT zips),
# Short/Long (question-bank automation), Solution (question answers?).
RECON_SEGMENTS = ["Resources", "Short", "Long", "Solution", "MCQ"]


async def run_recon(page, output_root: Path) -> None:
    await recon_capture(page, "10_home_after_login", output_root)

    for seg in RECON_SEGMENTS:
        safe = seg.replace(" ", "_").replace("/", "-").lower()
        if not await click_sunburst_segment(page, seg):
            continue
        await recon_capture(page, f"50_seg_{safe}", output_root)

        # Try to reveal the per-unit table: native <select> first, then ant-select
        try:
            await page.select_option("select", index=1, timeout=3000)
            await asyncio.sleep(1.2)
            await recon_capture(page, f"51_seg_{safe}_unit_selected", output_root)
        except Exception:
            try:
                await page.locator(".ant-select").first.click(timeout=3000)
                await asyncio.sleep(0.6)
                await recon_capture(page, f"52_seg_{safe}_dropdown_open", output_root)
                await page.keyboard.press("Escape")
            except Exception:
                pass

    logger.info("[recon] DONE — files are in %s (recon_*.png/.html/.json)", output_root)


# ── question-bank form automation ─────────────────────────────────────────────
# Fills the MCQ / Short / Long panels from unit_N/questions.json. The panels are
# ant-descriptions forms with CKEditor fields (drive via the CKEDITOR JS API),
# ant-selects, taxonomy verb chips (.ant-tag) and PO checkboxes.

async def select_session(page, session_num: int) -> bool:
    """Choose a session in the panel's ant-select (#SESSION) dropdown."""
    try:
        selector = page.locator(".ant-select", has=page.locator("input#SESSION"))
        current = await selector.locator(".ant-select-selection-item").inner_text()
        if current.strip() == str(session_num):
            return True
        await selector.click(timeout=5000)
        await asyncio.sleep(0.3)
        await page.locator(f".ant-select-item[title='{session_num}']").first.click(timeout=5000)
        await asyncio.sleep(0.6)
        return True
    except Exception as e:
        logger.error("Could not select session %d: %s", session_num, str(e)[:150])
        return False


async def fill_ckeditor_in_row(page, row_label: str, text: str) -> bool:
    """Set a CKEditor field's content, addressed by its form-row label."""
    name = await page.evaluate(
        """(label) => {
            const rows = document.querySelectorAll('tr.ant-descriptions-row');
            for (const r of rows) {
                const th = r.querySelector('th');
                if (!th) continue;
                const t = th.textContent.replace(/\\s+/g, ' ').trim();
                if (!t.includes(label)) continue;
                const inline = r.querySelector('[contenteditable="true"][aria-label*="Rich Text Editor"]');
                if (inline) {
                    const m = (inline.getAttribute('aria-label') || '').match(/editor\\d+/);
                    if (m) return m[0];
                }
                const iframe = r.querySelector('iframe.cke_wysiwyg_frame');
                if (iframe) {
                    const m = ((iframe.getAttribute('title') || '') + ' ' +
                               (iframe.getAttribute('aria-describedby') || '')).match(/editor\\d+/);
                    if (m) return m[0];
                    // fall back: containing .cke wrapper id is cke_editorN
                    const wrap = iframe.closest('[id^="cke_editor"]');
                    if (wrap) return wrap.id.replace('cke_', '');
                }
            }
            return null;
        }""",
        row_label,
    )
    if not name:
        logger.warning("CKEditor not found for row %r", row_label)
        return False
    await page.evaluate(
        "([n, txt]) => { CKEDITOR.instances[n].setData(txt); "
        "CKEDITOR.instances[n].updateElement(); }",
        [name, text],
    )
    await asyncio.sleep(0.1)
    return True


async def select_in_row(page, row_label: str, option_title: str,
                        option_index: int = None) -> bool:
    """Open the ant-select in the labelled form row, pick an option, VERIFY it.

    `option_index` picks by POSITION in the dropdown (0-based) — immune to
    however the portal labels its options. (Title matching failed silently for
    Bloom's Level and Correct Answer: the options are not titled '2'/'Option 2',
    so every attempt missed and the defaults were submitted.)
    """
    option_title = str(option_title)
    for attempt in range(3):
        try:
            row = page.locator("tr.ant-descriptions-row").filter(has_text=row_label).first
            selector = row.locator(".ant-select").first
            await selector.click(timeout=5000)
            await asyncio.sleep(0.3)
            dropdown = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            options = dropdown.locator(".ant-select-item")
            n_opts = await options.count()
            if attempt == 0:
                labels = await options.all_inner_texts()
                logger.info("%s dropdown options: %s", row_label, labels[:10])

            expected_label = ""
            if option_index is not None and 0 <= option_index < n_opts:
                option = options.nth(option_index)
                expected_label = (await option.inner_text()).strip()
            else:
                option = dropdown.locator(f".ant-select-item[title='{option_title}']").first
                if not await option.count():
                    option = dropdown.locator(
                        ".ant-select-item",
                        has_text=re.compile(rf"^{re.escape(option_title)}$")).first
            await option.click(timeout=4000)
            await asyncio.sleep(0.25)
            # Verify against the clicked option's own label when known;
            # otherwise loose-match (labels may be decorated: "2 — Understand")
            shown = (await selector.locator(".ant-select-selection-item")
                     .first.inner_text()).strip()
            if (expected_label and shown == expected_label) or option_title in shown:
                logger.info("%s = %r (verified on screen)", row_label, shown)
                return True
            logger.warning("select_in_row(%r): shows %r, wanted %r (attempt %d/3)",
                           row_label, shown, option_title, attempt + 1)
        except Exception as e:
            logger.warning("select_in_row(%r, %r) attempt %d failed: %s",
                           row_label, option_title, attempt + 1, str(e)[:120])
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass
        await asyncio.sleep(0.8)
    return False


async def click_taxonomy_verb(page, verb: str) -> None:
    try:
        row = page.locator("tr.ant-descriptions-row").filter(has_text="Taxonomy").first
        await row.locator(".ant-tag", has_text=re.compile(rf"^{re.escape(verb)}$")).first.click(
            timeout=4000)
        await asyncio.sleep(0.1)
    except Exception as e:
        logger.warning("taxonomy verb %r not clickable: %s", verb, str(e)[:100])


async def check_outcomes(page, pos: list) -> None:
    for p in pos:
        label = f"PO {p:02d}"
        try:
            row = page.locator("tr.ant-descriptions-row").filter(has_text="Outcomes").first
            await row.locator(".ant-checkbox-wrapper", has_text=label).first.click(timeout=3000)
            await asyncio.sleep(0.08)
        except Exception as e:
            logger.warning("PO checkbox %r not clickable: %s", label, str(e)[:100])


async def _question_rows_count(page) -> int:
    try:
        return await page.locator(".ant-table-tbody tr.ant-table-row").count()
    except Exception:
        return -1


async def submit_question(page, label: str, output_root: Path) -> str:
    """Click ADD NEW and confirm the question landed in the table."""
    before = await _question_rows_count(page)
    try:
        await page.get_by_role("button", name=re.compile(r"ADD NEW", re.I)).first.click(
            timeout=5000)
    except Exception as e:
        logger.error("ADD NEW click failed (%s): %s", label, str(e)[:120])
        await screenshot_on_error(page, f"q_addnew_{label}", output_root)
        return "error"

    deadline = asyncio.get_event_loop().time() + 20
    while asyncio.get_event_loop().time() < deadline:
        after = await _question_rows_count(page)
        if before >= 0 and after > before:
            return "ok"
        await asyncio.sleep(0.5)
    logger.warning("No confirmation for %s (rows %d -> %d)", label,
                   before, await _question_rows_count(page))
    await screenshot_on_error(page, f"q_no_confirm_{label}", output_root)
    return "no_confirm"


async def wait_form_ready(page, timeout_s: int = 15) -> bool:
    """Wait until the Question editor exists and is blank (form reset done).

    Filling too early — while the app is still resetting the form after
    ADD NEW — is how questions got lost. 'Type Here' is the panel's initial
    editor content, so treat it as blank.
    """
    deadline = asyncio.get_event_loop().time() + timeout_s
    while asyncio.get_event_loop().time() < deadline:
        try:
            state = await page.evaluate(
                """() => {
                    const rows = document.querySelectorAll('tr.ant-descriptions-row');
                    for (const r of rows) {
                        const th = r.querySelector('th');
                        if (!th) continue;
                        const t = th.textContent.replace(/\\s+/g, ' ').trim();
                        if (!t.includes('Question')) continue;
                        const el = r.querySelector('[contenteditable="true"][aria-label*="Rich Text Editor"]')
                               || r.querySelector('iframe.cke_wysiwyg_frame');
                        if (!el) continue;
                        const m = ((el.getAttribute('aria-label') || '') + ' ' +
                                   (el.getAttribute('title') || '')).match(/editor\\d+/);
                        if (!m || !window.CKEDITOR || !CKEDITOR.instances[m[0]]) return 'no-instance';
                        const txt = CKEDITOR.instances[m[0]].getData()
                            .replace(/<[^>]+>/g, '').trim();
                        return (txt === '' || txt === 'Type Here') ? 'ready' : 'has-content';
                    }
                    return 'no-editor';
                }""")
            if state == "ready":
                return True
        except Exception:
            pass
        await asyncio.sleep(0.3)
    logger.warning("Form did not become ready within %ds", timeout_s)
    return False


def _as_safe_html(text: str) -> str:
    """Escape content before it enters the portal's rich-text editors.

    Question text is data, not markup. Without escaping, a crafted question
    (AI-generated or faculty-edited) containing <script> would become stored
    XSS on the SRM portal, served to students.
    """
    return f"<p>{html.escape(str(text))}</p>"


async def enter_mcq(page, q: dict, label: str, output_root: Path) -> str:
    await wait_form_ready(page)
    issues = []
    if not await fill_ckeditor_in_row(page, "Question", _as_safe_html(q["question"])):
        return "error (question field not found)"
    for i, opt in enumerate(q["options"], 1):
        if not await fill_ckeditor_in_row(page, f"Options {i}", _as_safe_html(opt)):
            issues.append(f"option{i}")
    if not await select_in_row(page, "Correct", f"Option {q['correct_option']}",
                               option_index=q["correct_option"] - 1):
        issues.append("correct_answer")
    if not await select_in_row(page, "Bloom", str(q["blooms_level"]),
                               option_index=q["blooms_level"] - 1):
        issues.append("blooms_level")
    await click_taxonomy_verb(page, q["taxonomy_verb"])
    await check_outcomes(page, q["program_outcomes"])
    if "_s1_" in label and label.endswith("1"):
        # Visual evidence of the filled form (first question of session 1)
        await screenshot_on_error(page, f"filledform_{label}", output_root)
    status = await submit_question(page, label, output_root)
    if issues:
        status += f" [field problems: {', '.join(issues)}]"
        logger.error("Field problems on %s: %s", label, ", ".join(issues))
    return status


async def enter_written(page, q: dict, label: str, output_root: Path) -> str:
    await wait_form_ready(page)
    issues = []
    if not await fill_ckeditor_in_row(page, "Question", _as_safe_html(q["question"])):
        return "error (question field not found)"
    if not await fill_ckeditor_in_row(page, "Answer", _as_safe_html(q["answer"])):
        issues.append("answer")
    if not await select_in_row(page, "Level", str(q["level"]),
                               option_index=q["level"] - 1):
        issues.append("level")
    await click_taxonomy_verb(page, q["taxonomy_verb"])
    await check_outcomes(page, q["program_outcomes"])
    status = await submit_question(page, label, output_root)
    if issues:
        status += f" [field problems: {', '.join(issues)}]"
        logger.error("Field problems on %s: %s", label, ", ".join(issues))
    return status


QUESTION_KINDS = (
    ("mcqs", "MCQ", enter_mcq),
    ("short_questions", "Short", enter_written),
    ("long_questions", "Long", enter_written),
)


async def scan_question_occupancy(page, output_dir: Path, modules: list[int]) -> dict:
    """Which unit/session slots already hold questions on the portal.

    Returns {"<unit>": {"MCQ": [sessions...], "Short": [...], "Long": [...]}}
    — only for sessions we are about to fill.
    """
    conflicts: dict = {}
    for unit in modules:
        qpath = output_dir / f"unit_{unit}" / "questions.json"
        if not qpath.exists():
            continue
        qbank = json.loads(qpath.read_text())
        for kind, segment, _ in QUESTION_KINDS:
            if not await click_sunburst_segment(page, segment):
                continue
            occupied = []
            for sess in qbank["sessions"]:
                if not sess.get(kind):
                    continue
                if not await select_unit(page, unit, output_dir):
                    break
                if not await select_session(page, sess["session"]):
                    continue
                if await _question_rows_count(page) > 0:
                    occupied.append(sess["session"])
            if occupied:
                conflicts.setdefault(str(unit), {})[segment] = occupied
            logger.info("scan: unit %d %s — %d sessions already have questions",
                        unit, segment, len(occupied))
    return conflicts


async def delete_existing_questions(page, label: str, output_root: Path,
                                    max_rows: int = 60) -> bool:
    """Delete every existing question row in the current unit/session table."""
    removed = 0
    initial = await page.locator(".ant-table-tbody tr.ant-table-row").count()
    logger.info("Deleting %d existing question(s) — %s", initial, label)
    while removed < max_rows:
        rows = page.locator(".ant-table-tbody tr.ant-table-row")
        before = await rows.count()
        if before == 0:
            logger.info("Cleared all existing questions — %s (%d deleted)", label, removed)
            return True
        try:
            row = rows.first
            # Confirmed from portal screenshot (2026-07-08): Action column has
            # explicit "EDIT" and "DELETE" buttons — target DELETE by its label.
            btn = row.get_by_role("button", name=re.compile(r"DELETE", re.I))
            if not await btn.count():
                btn = row.locator(".anticon-delete")  # icon fallback
            if not await btn.count():
                btn = row.locator("button").last
            await btn.first.click(timeout=4000)
            await asyncio.sleep(0.5)
            # Ant usually asks for confirmation via popconfirm/modal
            for sel in (".ant-popover-buttons .ant-btn-primary",
                        ".ant-popconfirm-buttons .ant-btn-primary",
                        ".ant-modal-confirm-btns .ant-btn-primary",
                        ".ant-modal-footer .ant-btn-primary"):
                try:
                    confirm = page.locator(sel)
                    if await confirm.count():
                        await confirm.first.click(timeout=2500)
                        break
                except Exception:
                    pass
            # wait for the row to actually disappear
            deadline = asyncio.get_event_loop().time() + 12
            while asyncio.get_event_loop().time() < deadline:
                if await rows.count() < before:
                    break
                await asyncio.sleep(0.8)
            else:
                raise RuntimeError("row count did not decrease after delete")
            removed += 1
            await asyncio.sleep(0.4)
        except Exception as e:
            logger.error("Delete failed (%s): %s", label, str(e)[:150])
            await screenshot_on_error(page, f"q_delete_{label}", output_root)
            return False
    logger.warning("Delete loop hit max_rows for %s", label)
    return False


async def run_questions(page, output_dir: Path, modules: list[int]) -> int:
    """Fill MCQ / Short / Long panels from each unit's questions.json."""
    # If the portal uses a NATIVE browser confirm() for deletes, Playwright
    # would auto-dismiss it and the delete would never happen — accept instead.
    page.on("dialog", lambda d: asyncio.create_task(d.accept()))

    # Conflict phase — mirror of the file-upload flow: never silently pile
    # AI questions onto sessions the faculty already populated.
    on_conflict = os.environ.get("PORTAL_ON_CONFLICT", "replace")
    decision_path = os.environ.get("UPLOAD_DECISION_FILE", "")
    decision = "replace"
    conflicts: dict = {}
    if on_conflict in ("ask", "skip"):
        conflicts = await scan_question_occupancy(page, output_dir, modules)
        if conflicts:
            decision = "skip"
            if on_conflict == "ask" and decision_path:
                logger.info("CONFLICTS_JSON: %s", json.dumps(conflicts))
                logger.info("Existing questions found — waiting for your decision "
                            "in the CurriculAI window…")
                decision = await wait_for_decision(Path(decision_path))
                logger.info("DECISION_RECEIVED: %s", decision)
            logger.info("Conflict handling: decision=%s occupied=%s",
                        decision, json.dumps(conflicts))
        else:
            logger.info("scan: no existing questions — nothing to ask")

    overall_ok = True
    for unit in modules:
        qpath = output_dir / f"unit_{unit}" / "questions.json"
        if not qpath.exists():
            logger.warning("No questions.json for unit %d — skipping", unit)
            continue
        qbank = json.loads(qpath.read_text())

        for kind, segment, entry_fn in QUESTION_KINDS:
            if not await click_sunburst_segment(page, segment):
                overall_ok = False
                continue
            occupied_sessions = conflicts.get(str(unit), {}).get(segment, [])
            for sess in qbank["sessions"]:
                s_num = sess["session"]
                questions = sess.get(kind, [])
                if not questions:
                    continue
                if s_num in occupied_sessions and decision == "skip":
                    logger.info("Keeping existing %s questions — unit %d session %d "
                                "(professor's choice)", segment, unit, s_num)
                    continue
                if not await select_unit(page, unit, output_dir):
                    overall_ok = False
                    break
                if not await select_session(page, s_num):
                    overall_ok = False
                    continue
                if s_num in occupied_sessions and decision == "replace":
                    logger.info("Replacing existing %s questions — unit %d session %d",
                                segment, unit, s_num)
                    if not await delete_existing_questions(
                            page, f"u{unit}_s{s_num}_{segment.lower()}", output_dir):
                        logger.warning("Could not clear existing questions — "
                                       "adding ours alongside")
                failed = []
                for qi, q in enumerate(questions, 1):
                    label = f"u{unit}_s{s_num}_{segment.lower()}{qi}"
                    status = await entry_fn(page, q, label, output_dir)
                    logger.info("Question %s: %s", label, status)
                    if not status.startswith("ok"):
                        failed.append((qi, q))
                    await asyncio.sleep(0.3)

                # One retry pass — transient races (form reset timing) are the
                # usual cause of a lost question.
                for qi, q in failed:
                    label = f"u{unit}_s{s_num}_{segment.lower()}{qi}_retry"
                    logger.info("Retrying %s...", label)
                    status = await entry_fn(page, q, label, output_dir)
                    logger.info("Question %s: %s", label, status)
                    if not status.startswith("ok"):
                        overall_ok = False
                    await asyncio.sleep(0.3)
        logger.info("Questions for unit %d complete", unit)

    return 0 if overall_ok else 1


# ── sniff mode ────────────────────────────────────────────────────────────────
# After login, do nothing — the OPERATOR manually uploads a file in the window
# while we record every upload-related request/response. Comparing a manual
# (working) request against ours reveals what the server needs.

async def run_sniff(page, output_root: Path, minutes: int = 10) -> None:
    def _log_request(req):
        try:
            if req.method == "GET":
                return
            ct = req.headers.get("content-type", "")
            pd = ""
            try:
                pd = req.post_data or ""
            except Exception:
                pd = "(binary)"
            # keep multipart readable: strip long runs of file bytes
            if len(pd) > 1500:
                pd = pd[:1500] + f"... ({len(pd)} bytes total)"
            logger.info("[sniff] %s %s\n    content-type: %s\n    post_data: %s",
                        req.method, req.url[:140], ct, pd)
        except Exception:
            pass

    page.on("request", _log_request)
    logger.info("=" * 60)
    logger.info("[sniff] RECORDING. Now do a MANUAL upload in this window:")
    logger.info("[sniff]  1. click the PPTx segment on the donut chart")
    logger.info("[sniff]  2. Session 1 / SLO 1 → CLICK TO UPLOAD")
    logger.info("[sniff]  3. choose the zip and watch whether it succeeds")
    logger.info("[sniff] Recording for %d minutes — Ctrl+C when done.", minutes)
    logger.info("=" * 60)
    await asyncio.sleep(minutes * 60)


# ── main ──────────────────────────────────────────────────────────────────────

async def run(output_dir: Path, modules: list[int], recon: bool = False,
              limit: int = 0, sniff: bool = False, questions: bool = False) -> int:
    username = os.environ.get("PORTAL_USERNAME", "")
    password = os.environ.get("PORTAL_PASSWORD", "")

    # Purge debug/recon captures from previous runs — these contain the portal's
    # authenticated DOM and should never linger on disk after a run.
    purge_debug_captures(output_dir)

    # In manual-login mode the professor types their own credentials in the
    # visible browser, so env credentials are optional. Headless has no human,
    # so it still needs them (and can't solve the captcha anyway).
    if not MANUAL_LOGIN and (not username or not password):
        logger.error("PORTAL_USERNAME / PORTAL_PASSWORD not set in environment")
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            accept_downloads=False,
            ignore_https_errors=False,
        )
        page = await context.new_page()
        success = True

        # Log every non-GET response — shows exactly what the portal's upload
        # API answered. For failures (>=400), also capture the response body:
        # that's where the server states WHY it rejected an upload.
        async def _log_response(resp):
            try:
                if resp.request.method == "GET":
                    return
                if resp.status >= 400:
                    body = ""
                    try:
                        body = (await resp.text())[:600]
                    except Exception:
                        body = "(body unavailable)"
                    logger.warning("HTTP %s %s -> %d\n    BODY: %s",
                                   resp.request.method, resp.url[:120], resp.status, body)
                else:
                    logger.info("HTTP %s %s -> %d",
                                resp.request.method, resp.url[:120], resp.status)
            except Exception:
                pass
        page.on("response", _log_response)

        try:
            if not await login(page, username, password, output_dir):
                return 1
            if recon:
                await run_recon(page, output_dir)
                return 0
            if sniff:
                await run_sniff(page, output_dir)
                return 0
            if questions:
                return await run_questions(page, output_dir, modules)
            # Login lands directly on the course's Content Management page —
            # no navigation needed (we are the course coordinator).

            # Conflict phase: existing uploads are the faculty's work — never
            # silently overwrite. In ask-mode we pause for their decision.
            on_conflict = os.environ.get("PORTAL_ON_CONFLICT", "replace")
            decision_path = os.environ.get("UPLOAD_DECISION_FILE", "")
            skip_map: dict = {}
            if on_conflict in ("ask", "skip"):
                conflicts = await scan_occupancy(page, modules, output_dir)
                if conflicts:
                    decision = "skip"
                    if on_conflict == "ask" and decision_path:
                        logger.info("CONFLICTS_JSON: %s", json.dumps(conflicts))
                        logger.info("Existing uploads found — waiting for your decision "
                                    "in the CurriculAI window…")
                        decision = await wait_for_decision(Path(decision_path))
                        logger.info("DECISION_RECEIVED: %s", decision)
                    if decision == "skip":
                        skip_map = conflicts
                else:
                    logger.info("scan: no existing uploads — nothing to ask")

            for unit in modules:
                unit_skips = set(skip_map.get(unit, {}).get("pptx", []))
                await upload_pptx_source(page, unit, output_dir, limit=limit,
                                         skip_keys=unit_skips, segment="PPTx")
            if limit:
                logger.info("--limit set: skipping Resources + learning material (test mode)")
            else:
                # Faculty requirement: the same zips also go to Additional Resources
                for unit in modules:
                    res_skips = set(skip_map.get(unit, {}).get("resources", []))
                    await upload_pptx_source(page, unit, output_dir,
                                             skip_keys=res_skips, segment="Resources")
                for unit in modules:
                    await upload_learning_material(
                        page, unit, output_dir,
                        skip=bool(skip_map.get(unit, {}).get("lm")),
                    )
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            await screenshot_on_error(page, "unexpected_error", output_dir)
            success = False
        finally:
            # Clear references before browser closes
            username = ""
            password = ""
            await context.close()
            await browser.close()

    logger.info("Upload complete — success=%s", success)
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--modules", nargs="+", type=int, default=list(range(1, 6)))
    parser.add_argument(
        "--recon", action="store_true",
        help="Reconnaissance only: after login, walk the portal capturing DOM + "
             "screenshots at each step. Performs NO uploads.",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Test mode: upload at most N PPT slots, skip learning material. "
             "Use --limit 1 to verify a single upload end-to-end.",
    )
    parser.add_argument(
        "--sniff", action="store_true",
        help="After login, record upload-related network traffic while the "
             "operator uploads a file MANUALLY in the window. No auto uploads.",
    )
    parser.add_argument(
        "--questions", action="store_true",
        help="Fill the MCQ/Short/Long question forms from unit_N/questions.json "
             "instead of uploading files.",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logger.error("Output directory not found: %s", output_dir)
        sys.exit(1)
    sys.exit(asyncio.run(run(output_dir, args.modules, recon=args.recon,
                             limit=args.limit, sniff=args.sniff,
                             questions=args.questions)))


if __name__ == "__main__":
    main()
