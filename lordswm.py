

import os
import time
from playwright.sync_api import sync_playwright

# Environment variables
URL = os.environ["WEBSITE"]
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]

# Optional selectors (with defaults)
USERNAME_SELECTOR = os.environ.get("USERNAME_SELECTOR", 'input[name="login"]')
PASSWORD_SELECTOR = os.environ.get("PASSWORD_SELECTOR", 'input[name="pass"]')

# Increase timeouts for slow pages
NAVI_TIMEOUT = 60000  # 60 seconds

def login(page):
    page.goto(URL, wait_until="domcontentloaded", timeout=NAVI_TIMEOUT)

    page.locator(USERNAME_SELECTOR).fill(USERNAME)
    page.locator(PASSWORD_SELECTOR).fill(PASSWORD)

    # Click the image login button
    page.locator('input[type="image"][title="Login!"]').click()

    page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)

def try_click_maproduction_and_wbtn(page, first_text: str):
    """
    Click first_text (Map or Production), then check for '»»»'.
    If found: click it, click #wbtn, and return True.
    If not found: return False.
    """
    page.get_by_text(first_text).click()
    page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)

    link = page.get_by_text("»»»")
    if link.count() > 0:
        link.first.click()
        page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
        page.locator('#wbtn').click()
        page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
        return True

    return False

def mine_production_loop(page):
    """
    Alternate between Mining and Production every 5 minutes,
    checking for '»»»' until found, then click it and #wbtn.
    """
    delay_minutes = 5
    delay_seconds = delay_minutes * 60

    mining_text = "Mining"
    production_text = "Production"

    while True:
        # Try Mining
        #page.get_by_text(mining_text).click()
        #page.locator(".map_sel_obj_t").first.click()
        page.get_by_role("link", name="Map").hover()
        page.get_by_role("link", name="Mining").click()
        page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)

        link = page.get_by_text("»»»")
        if link.count() > 0:
            link.first.click()
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            page.locator('#wbtn').click()
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            return

        time.sleep(delay_seconds)

        # Try Production
        #page.get_by_text(production_text).click()
        page.get_by_role("link", name="Map").hover()
        page.get_by_role("link", name="Production").click()
        page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)

        link = page.get_by_text("»»»")
        if link.count() > 0:
            link.first.click()
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            page.locator('#wbtn').click()
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            return

        time.sleep(delay_seconds)

def main_loop(page):
    """
    Main loop:
    - Try Map -> check '»»»'
    - If not found, try Production -> check '»»»'
    - If still not found, alternate Mining/Production every 5 min until found.
    - After success: wait 60 minutes, reload, and restart from Map.
    """
    while True:
        # 1. Try Map
        if try_click_maproduction_and_wbtn(page, "Map"):
            time.sleep(60 * 60)
            page.reload(wait_until="networkidle", timeout=NAVI_TIMEOUT)
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            continue

        # 2. Try Production
        if try_click_maproduction_and_wbtn(page, "Production"):
            time.sleep(60 * 60)
            page.reload(wait_until="networkidle", timeout=NAVI_TIMEOUT)
            page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)
            continue

        # 3. Alternating Mining/Production loop until success
        mine_production_loop(page)

        # After success in the mine_production_loop: wait 60 min, reload, restart
        time.sleep(60 * 60)
        page.reload(wait_until="networkidle", timeout=NAVI_TIMEOUT)
        page.wait_for_load_state("networkidle", timeout=NAVI_TIMEOUT)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Set timeouts globally (optional)
        page.set_default_timeout(NAVI_TIMEOUT)
        page.set_default_navigation_timeout(NAVI_TIMEOUT)

        login(page)
        main_loop(page)

        browser.close()
