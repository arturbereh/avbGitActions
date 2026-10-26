"""
Automated Playwright script for cyclic Map, Mining, and Production tasks.
Includes automated CI/CD debugging screenshots on click failures.
"""

import itertools
import os
import time

from playwright.sync_api import Locator, Page, sync_playwright

# Environment variables
URL = os.environ["WEBSITE"]
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
USERNAME_SELECTOR = os.environ.get("USERNAME_SELECTOR", 'input[name="login"]')
PASSWORD_SELECTOR = os.environ.get("PASSWORD_SELECTOR", 'input[name="pass"]')

NAVI_TIMEOUT = 60000  # 60 seconds


def safe_click(page: Page, locator: Locator, action_name: str) -> None:
    """
    Attempts to click a locator. If it fails, takes a full-page 
    screenshot for debugging and raises the error.
    """
    try:
        locator.click(timeout=10000)
    except Exception as e:
        filename = f"cicd_error_{action_name.replace(' ', '_')}.png"
        print(f"FAILED: {action_name}. Saving screenshot to {filename}")
        page.screenshot(path=filename, full_page=True)
        raise e


def login(page: Page) -> None:
    page.goto(URL, wait_until="domcontentloaded")
    page.locator(USERNAME_SELECTOR).fill(USERNAME)
    page.locator(PASSWORD_SELECTOR).fill(PASSWORD)

    safe_click(page, page.locator('input[type="image"][title="Login!"]'), "Login_Button")
    page.wait_for_load_state("networkidle")


def attempt_workflow(page: Page, click_locator: Locator, action_name: str, hover_locator: Locator = None) -> bool:
    """
    Optionally hovers a menu, clicks the target locator, and checks for '»»»'.
    If found, completes the sequence and returns True.
    """
    if hover_locator:
        hover_locator.hover()

    safe_click(page, click_locator, action_name)
    page.wait_for_load_state("networkidle")

    arrows = page.get_by_text("»»»")
    if arrows.count() > 0:
        safe_click(page, arrows.first, f"{action_name}_Arrows")
        page.wait_for_load_state("networkidle")

        safe_click(page, page.locator("#wbtn"), f"{action_name}_W_Button")
        page.wait_for_load_state("networkidle")
        return True

    return False


def main_loop(page: Page) -> None:
    while True:
        # 1. Try Map, then try Production (short-circuits if Map succeeds)
        success = attempt_workflow(page, page.get_by_text("Map"), "Initial_Map") or \
                  attempt_workflow(page, page.get_by_text("Production"), "Initial_Production")

        # 2. If both failed, alternate Mining and Production from the dropdown menu
        if not success:
            menu_hover = page.get_by_role("link", name="Map")

            fallback_actions = itertools.cycle([
                (page.get_by_role("link", name="Mining"), "Dropdown_Mining"),
                (page.get_by_role("link", name="Production"), "Dropdown_Production"),
            ])

            for locator, name in fallback_actions:
                if attempt_workflow(page, locator, name, hover_locator=menu_hover):
                    break
                time.sleep(300)  # 5 minutes

        # 3. Success reached: wait 60 mins, reload, restart from the top
        time.sleep(3600)
        page.reload(wait_until="networkidle")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        # Force a large desktop resolution to prevent mobile layouts in CI/CD
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Handle all subsequent timeouts automatically
        page.set_default_timeout(NAVI_TIMEOUT)
        page.set_default_navigation_timeout(NAVI_TIMEOUT)

        login(page)
        main_loop(page)

        browser.close()


if __name__ == "__main__":
    main()