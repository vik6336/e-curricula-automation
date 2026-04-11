"""Playwright-based browser automation for uploading files to the e-curricula portal."""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser

from .portal_config import (
    LOGIN_URL,
    PORTAL_URL,
    PORTAL_USERNAME,
    PORTAL_PASSWORD,
    SELECTORS,
    NAVIGATION_TIMEOUT,
    UPLOAD_TIMEOUT,
)


def login(page: Page) -> bool:
    """Log into the e-curricula portal.

    Returns True on success, False if manual intervention needed (CAPTCHA).
    """
    page.goto(LOGIN_URL, timeout=NAVIGATION_TIMEOUT)
    page.wait_for_load_state("networkidle")

    # Fill credentials
    page.fill(SELECTORS["username_input"], PORTAL_USERNAME)
    page.fill(SELECTORS["password_input"], PORTAL_PASSWORD)
    page.click(SELECTORS["login_button"])

    # Wait for navigation after login
    page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)

    # Check if we're logged in (should redirect away from login page)
    if "login" in page.url.lower():
        print("WARNING: Still on login page. CAPTCHA or MFA may be required.", file=sys.stderr)
        print("Please complete login manually in the browser window.", file=sys.stderr)
        # Wait up to 2 minutes for manual intervention
        for _ in range(24):
            time.sleep(5)
            if "login" not in page.url.lower():
                print("Login successful after manual intervention.", file=sys.stderr)
                return True
        return False

    return True


def navigate_to_course(page: Page, course_code: str = "21CSE597T"):
    """Navigate to the specific course page."""
    # Look for the course link on the dashboard
    course_selector = SELECTORS["course_link"].format(course_code=course_code)
    try:
        page.click(course_selector, timeout=NAVIGATION_TIMEOUT)
    except Exception:
        # Fallback: navigate directly if we know the URL pattern
        page.goto(f"{PORTAL_URL}/course/{course_code}", timeout=NAVIGATION_TIMEOUT)
    page.wait_for_load_state("networkidle")


def upload_pptx_files(page: Page, module_num: int, ppt_dir: str) -> dict:
    """Upload all PPTX files for a module to the PPTx Source section.

    Args:
        page: Playwright page object (already logged in and on course page)
        module_num: Module/unit number (1-5)
        ppt_dir: Directory containing session_X_slo_Y.pptx files

    Returns:
        Dict with upload results per file
    """
    results = {}
    ppt_path = Path(ppt_dir)

    # Navigate to PPTx Source section
    try:
        page.click(SELECTORS["pptx_section"], timeout=NAVIGATION_TIMEOUT)
        page.wait_for_load_state("networkidle")
    except Exception as e:
        print(f"Could not find PPTx Source section: {e}", file=sys.stderr)
        return {"error": str(e)}

    # Select the correct unit
    try:
        page.select_option(SELECTORS["unit_dropdown"], str(module_num))
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Wait for the unit content to load
    except Exception as e:
        print(f"Could not select unit {module_num}: {e}", file=sys.stderr)

    # Upload each PPT file
    for session_num in range(1, 10):
        for slo_num in range(1, 3):
            filename = f"session_{session_num}_slo_{slo_num}.pptx"
            filepath = ppt_path / filename

            if not filepath.exists():
                results[filename] = "file_not_found"
                continue

            try:
                # Find the correct upload slot
                # The portal shows rows per session with SLO columns
                # We need to find the right "CLICK TO UPLOAD" button
                row_selector = f'tr:has-text("Session {session_num}") >> nth=0'
                slo_col_index = slo_num  # SLO 1 is first upload, SLO 2 is second

                # Try to find the file input for this slot
                upload_buttons = page.query_selector_all(
                    f'{row_selector} >> {SELECTORS["upload_button"]}'
                )

                if len(upload_buttons) >= slo_num:
                    # Click the upload button to trigger file dialog
                    with page.expect_file_chooser() as fc_info:
                        upload_buttons[slo_num - 1].click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(str(filepath))

                    # Wait for upload to complete
                    time.sleep(3)
                    results[filename] = "uploaded"
                    print(f"  Uploaded: {filename}", file=sys.stderr)
                else:
                    # Fallback: try direct file input
                    file_inputs = page.query_selector_all(
                        f'{row_selector} >> input[type="file"]'
                    )
                    if len(file_inputs) >= slo_num:
                        file_inputs[slo_num - 1].set_input_files(str(filepath))
                        time.sleep(3)
                        results[filename] = "uploaded"
                        print(f"  Uploaded: {filename}", file=sys.stderr)
                    else:
                        results[filename] = "upload_slot_not_found"
                        print(f"  Could not find upload slot for {filename}",
                              file=sys.stderr)

            except Exception as e:
                results[filename] = f"error: {str(e)}"
                # Screenshot on failure
                screenshot_path = ppt_path.parent / f"error_{filename}.png"
                page.screenshot(path=str(screenshot_path))
                print(f"  Error uploading {filename}: {e}", file=sys.stderr)

    return results


def upload_learning_material(page: Page, module_num: int, pdf_path: str) -> dict:
    """Upload the Learning Material PDF for a module.

    Args:
        page: Playwright page (logged in, on course page)
        module_num: Module/unit number (1-5)
        pdf_path: Path to the PDF file

    Returns:
        Upload result dict
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return {"error": "PDF file not found"}

    try:
        # Navigate to Learning Material section
        page.click(SELECTORS["learning_material_section"], timeout=NAVIGATION_TIMEOUT)
        page.wait_for_load_state("networkidle")

        # Find the upload slot for the correct unit
        unit_row = page.query_selector(f'tr:has-text("Unit {module_num}")')
        if not unit_row:
            return {"error": f"Could not find Unit {module_num} row"}

        # Click upload
        upload_btn = unit_row.query_selector(SELECTORS["upload_button"])
        if upload_btn:
            with page.expect_file_chooser() as fc_info:
                upload_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(pdf_file))
            time.sleep(3)
            print(f"  Uploaded Learning Material for Unit {module_num}", file=sys.stderr)
            return {"status": "uploaded"}
        else:
            # Fallback to direct file input
            file_input = unit_row.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(str(pdf_file))
                time.sleep(3)
                return {"status": "uploaded"}
            return {"error": "Upload button not found"}

    except Exception as e:
        screenshot_path = pdf_file.parent / f"error_pdf_unit_{module_num}.png"
        page.screenshot(path=str(screenshot_path))
        return {"error": str(e)}


def upload_all(output_dir: str, modules: list[int] = None) -> dict:
    """Upload all generated files for specified modules.

    Args:
        output_dir: Base output directory containing unit_N folders
        modules: List of module numbers to upload (default: all 1-5)

    Returns:
        Dict with results per module
    """
    if modules is None:
        modules = list(range(1, 6))

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible for debugging/CAPTCHA
        page = browser.new_page()

        # Login
        if not login(page):
            return {"error": "Login failed"}

        # Navigate to course
        navigate_to_course(page)

        for module_num in modules:
            print(f"\nUploading Module {module_num}...", file=sys.stderr)
            module_results = {}

            # Upload PPTs
            ppt_dir = Path(output_dir) / f"unit_{module_num}" / "ppts"
            if ppt_dir.exists():
                module_results["ppts"] = upload_pptx_files(page, module_num, str(ppt_dir))

            # Upload PDF
            pdf_path = Path(output_dir) / f"unit_{module_num}" / f"unit_{module_num}_learning_material.pdf"
            if pdf_path.exists():
                module_results["pdf"] = upload_learning_material(page, module_num, str(pdf_path))

            results[f"module_{module_num}"] = module_results

        browser.close()

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.upload.portal_upload <output_dir> [module_nums]",
              file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    modules = [int(m) for m in sys.argv[2:]] if len(sys.argv) > 2 else None

    results = upload_all(output_dir, modules)
    print(json.dumps(results, indent=2))
