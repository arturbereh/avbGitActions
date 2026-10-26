"""
Automated Playwright script for cyclic Map, Mining, and Production tasks.
"""

import itertools
import os
import time
from typing import Optional

from playwright.sync_api import Locator, Page, sync_playwright

# Environment variables (Will raise KeyError if WEBSITE, USERNAME, or PASSWORD are not set)
URL = os.environ["WEBSITE"]
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
USERNAME_SELECTOR = os.environ.get("USERNAME_SELECTOR", 'input[name="login"]')
PASSWORD_SELECTOR = os.environ.get("PASSWORD_SELECTOR", 'input[name="pass"]')

NAVI_TIMEOUT = 60000  # 60 seconds


def login(page: Page) -> None:
    """
    Navigates to the configured URL and logs the user in.
    """
    page.goto(URL, wait_until="domcontentloaded")
    page.locator(USERNAME_SELECTOR).fill(USERNAME)
    page.locator(PASSWORD_SELECTOR).fill(PASSWORD)

    page.locator('input[type="image"][title="Login!"]').click()
    page.wait_for_load_state("networkidle")


def attempt_workflow(
    page: Page, locator: Locator, hover_locator: Optional[Locator] = None
) -> bool:
    """
    Optionally hovers over a menu, clicks the provided locator, waits, and checks for the '»»»' link.
    If found, completes the workflow and returns True.
    """
    if hover_locator:
        hover_locator.hover()

    locator.click()
    page.wait_for_load_state("networkidle")

    arrows = page.get_by_text("»»»")
    if arrows.count() > 0:
        arrows.first.click()
        page.locator("#wbtn").click()
        page.wait_for_load_state("networkidle")
        return True

    return False


def main_loop(page: Page) -> None:
    """
    Main continuous loop for navigating Map, Production, and Mining.
    """
    map_hover = page.get_by_text("Map")

    while True:
        # 1. Try Map (no hover needed), then try Production (needs hover on Map)
        success = attempt_workflow(page, page.get_by_text("Map")) or attempt_workflow(
            page, page.get_by_text("Production"), hover_locator=map_hover
        )

        # 2. If both failed, alternate Mining and Production hints every 5 mins
        if not success:
            fallback_locators = itertools.cycle(
                [
                    page.get_by_role("hint", name="Mining"),
                    page.get_by_role("hint", name="Production"),
                ]
            )

            # Keep trying the fallback locators until one succeeds (hovering Map first)
            for current_locator in fallback_locators:
                if attempt_workflow(page, current_locator, hover_locator=map_hover):
                    break
                time.sleep(300)  # Wait 5 minutes

        # 3. Success reached: wait 60 mins, reload, restart from the top
        time.sleep(3600)
        page.reload(wait_until="networkidle")


def main() -> None:
    """
    Entry point to launch the browser and start the automation.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        # These handle all subsequent timeouts automatically
        page.set_default_timeout(NAVI_TIMEOUT)
        page.set_default_navigation_timeout(NAVI_TIMEOUT)

        login(page)
        main_loop(page)

        browser.close()


if __name__ == "__main__":
    main()