"""
Test: open the form page, fill every field with sample data,
pause for manual verification, and close the browser.

The Submit button is intentionally NOT clicked.
"""

import logging

import pytest
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError

from pages.form_page import FormPage
from pages.details_page import DetailsPage
from utils import test_data

logger = logging.getLogger(__name__)


@pytest.fixture
def page():
    """
    Attach to the already-running real Chrome over CDP and yield a new page.

    Using your real Chrome (instead of launching Chromium) avoids bot
    detection: the browser has a normal fingerprint and keeps its login
    session in its own profile. Start Chrome first with:

        ./start_chrome_debug.sh
    """
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(test_data.CDP_URL)
        except PlaywrightError as exc:
            pytest.fail(
                f"Could not connect to Chrome at {test_data.CDP_URL}. "
                "Start it first with ./start_chrome_debug.sh\n"
                f"Original error: {exc}"
            )
        # Reuse the browser's existing context (the real profile with its
        # cookies/login) rather than creating a fresh, empty one.
        context = browser.contexts[0]
        page = context.new_page()
        yield page
        # Close only the tab we opened, then disconnect. The user's Chrome
        # keeps running.
        page.close()
        browser.close()
        logger.info("Disconnected from Chrome (browser left running)")


def test_fill_form(page: Page):
    """Fill the entire form with sample data (without submitting)."""
    form_page = FormPage(page)

    try:
        # Step 1: Navigate and wait for full load
        form_page.open()

        # Step 1b: If redirected to a login page, wait for manual login.
        # The test continues automatically once the form page is reached.
        form_page.wait_for_manual_login()

        # Step 2: Screenshot before filling
        form_page.take_screenshot("before_filling")

        # Step 3: Fill every available form field
        form_page.fill_form(test_data.FORM_DATA)

        # Step 4: Screenshot after filling
        form_page.take_screenshot("after_filling")

        # Step 5: Move to the "Details" step and fill it too
        form_page.go_to_next_step()
        details_page = DetailsPage(page)
        details_page.fill_details(test_data.DETAILS_DATA)

        # Step 6: Screenshot of the filled details page
        form_page.take_screenshot("after_filling_details")

        # Step 7: Pause so the values can be verified visually.
        # (Intentional hardcoded wait - it exists purely for human review.)
        logger.info(
            "Waiting %s seconds for manual verification...",
            test_data.VERIFICATION_PAUSE_SECONDS,
        )
        page.wait_for_timeout(test_data.VERIFICATION_PAUSE_SECONDS * 1000)

        # NOTE: The Details step's Next button is intentionally not clicked.
        logger.info("Test finished - both steps filled but NOT submitted")

    except Exception:
        # Capture the failure state before re-raising so pytest reports it.
        form_page.take_screenshot("error")
        logger.exception("Test failed - error screenshot saved")
        raise
