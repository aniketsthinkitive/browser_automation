"""
Page Object for the form page.

All locators and page interactions live here (Page Object Model).
Tests never touch Playwright selectors directly - they call the
high-level methods on this class, so when the real website's locators
are known, only this file needs updating.
"""

import logging
import os

from playwright.sync_api import (
    Page,
    Locator,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

from utils import test_data

logger = logging.getLogger(__name__)


class FormPage:
    """Encapsulates every interaction with the form page."""

    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(test_data.DEFAULT_TIMEOUT)

        # -------------------------------------------------------------
        # Locators - SmartRecruiters "Create job" page (step 1: Create).
        # The page is built from spl-* web components (shadow DOM);
        # Playwright's CSS selectors pierce open shadow roots, so we can
        # target the inner <input> through the stable data-test hosts.
        # -------------------------------------------------------------
        self.job_title_input = page.locator(
            '[data-test="jobWizard-jobField-jobTitle"] input'
        )
        # value is one of: on-site | remote | hybrid
        self.work_location_radio = lambda value: page.locator(
            f"spl-radio[value='{value}']"
        )
        # The four rich-text fields are CKEditor iframes, in page order:
        # 0 = Company Description, 1 = Job Description,
        # 2 = Qualifications, 3 = Additional Information.
        self.rich_text_frame_selector = "iframe.cke_wysiwyg_frame"
        self.video_input = page.locator(
            '[data-test="jobWizard-jobField-videoUrl-1"] input'
        )
        self.save_template_checkbox = page.locator(
            '[data-test="jobWizard-createStep-saveAsTemplateCheckbox"] input'
        )
        self.next_button = page.locator(
            'spl-button[data-test="jobWizard-createStep-nextButton"]'
        )

    # -----------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------

    def open(self, url: str = test_data.BASE_URL) -> None:
        """Navigate to the form page and wait for it to load completely."""
        logger.info("Navigating to %s", url)
        try:
            self.page.goto(url, wait_until="load")
        except PlaywrightError as exc:
            # The SmartRecruiters SPA sometimes cancels the initial request
            # while re-routing (net::ERR_ABORTED). The page still loads, so
            # just continue and let the networkidle wait below settle it.
            if "ERR_ABORTED" not in str(exc):
                raise
            logger.info("Initial navigation aborted by app redirect - continuing")
        # Wait for the network to go quiet so dynamic content is ready too.
        self.page.wait_for_load_state("networkidle")
        logger.info("Page loaded completely")

    def wait_for_manual_login(self, target_url: str = test_data.BASE_URL) -> None:
        """
        If the site redirected us to a login page, pause and let the user
        log in manually in the open browser window. The test resumes as
        soon as the browser lands back on the target (form) URL.
        """
        from urllib.parse import urlparse

        target_path = urlparse(target_url).path
        if target_path in self.page.url:
            logger.info("Already on the form page - no login needed")
            return

        logger.info(
            "Login page detected. Please log in manually in the browser window. "
            "Waiting up to %s seconds...",
            test_data.LOGIN_WAIT_SECONDS,
        )
        # Resolves the moment the browser reaches the form URL after login.
        self.page.wait_for_url(
            f"**{target_path}**",
            timeout=test_data.LOGIN_WAIT_SECONDS * 1000,
        )
        self.page.wait_for_load_state("networkidle")
        logger.info("Login detected - continuing with the form")

    # -----------------------------------------------------------------
    # Reusable low-level helpers
    # -----------------------------------------------------------------
    # Each helper:
    #   1. Skips gracefully if the element does not exist on the page.
    #   2. Scrolls the element into view before interacting.
    #   3. Logs what it did (or why it skipped).

    def _is_present(self, locator: Locator, field_name: str) -> bool:
        """Return True if the element exists on the page, else log and skip."""
        if locator.count() == 0:
            logger.warning("Field '%s' not found on page - skipping", field_name)
            return False
        return True

    def fill_text(self, locator: Locator, value: str, field_name: str) -> None:
        """Fill a text-like input (text, email, password, phone, number, date)."""
        if not self._is_present(locator, field_name):
            return
        locator.scroll_into_view_if_needed()
        locator.fill(value)
        logger.info("Filled '%s' with '%s'", field_name, value)

    def select_option(self, locator: Locator, value: str, field_name: str) -> None:
        """Select a dropdown option by its visible label."""
        if not self._is_present(locator, field_name):
            return
        locator.scroll_into_view_if_needed()
        locator.select_option(label=value)
        logger.info("Selected '%s' in dropdown '%s'", value, field_name)

    def check_radio(self, locator: Locator, field_name: str) -> None:
        """Select a radio button (click - spl-radio hosts are not native inputs)."""
        if not self._is_present(locator, field_name):
            return
        locator.scroll_into_view_if_needed()
        locator.click()
        logger.info("Selected radio button '%s'", field_name)

    def fill_rich_text(self, index: int, value: str, field_name: str) -> None:
        """Fill a CKEditor rich-text field (contenteditable body in an iframe)."""
        frames = self.page.locator(self.rich_text_frame_selector)
        if frames.count() <= index:
            logger.warning("Field '%s' not found on page - skipping", field_name)
            return
        frames.nth(index).scroll_into_view_if_needed()
        body = (
            self.page.frame_locator(self.rich_text_frame_selector)
            .nth(index)
            .locator("body")
        )
        body.fill(value)
        logger.info("Filled '%s' with '%s'", field_name, value[:60])

    def set_checkbox(self, locator: Locator, checked: bool, field_name: str) -> None:
        """Check or uncheck a checkbox to match the desired state."""
        if not self._is_present(locator, field_name):
            return
        locator.scroll_into_view_if_needed()
        locator.set_checked(checked)
        logger.info("Set checkbox '%s' to %s", field_name, checked)

    def upload_file(self, locator: Locator, file_path: str, field_name: str) -> None:
        """Attach a file to a file-upload input, creating a sample file if needed."""
        if not self._is_present(locator, field_name):
            return
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Sample file used by the form automation test.\n")
            logger.info("Created sample upload file at '%s'", file_path)
        locator.scroll_into_view_if_needed()
        locator.set_input_files(file_path)
        logger.info("Uploaded '%s' to field '%s'", file_path, field_name)

    def take_screenshot(self, name: str) -> str:
        """Save a full-page screenshot into the screenshots directory."""
        os.makedirs(test_data.SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(test_data.SCREENSHOT_DIR, f"{name}.png")
        self.page.screenshot(path=path, full_page=True)
        logger.info("Screenshot saved: %s", path)
        return path

    def go_to_next_step(self) -> None:
        """Click Next and wait for the Details step to load."""
        self.next_button.scroll_into_view_if_needed()
        self.next_button.click()
        self.page.wait_for_url("**/jobs/ad/details**")
        self.page.wait_for_load_state("networkidle")
        logger.info("Moved to the Details step: %s", self.page.url)

    # -----------------------------------------------------------------
    # High-level action: fill the whole form
    # -----------------------------------------------------------------

    def fill_form(self, data: dict) -> None:
        """Fill the SmartRecruiters job ad form with the provided test data."""
        logger.info("--- Starting to fill the form ---")

        # Job Title (typing opens a template-suggestion dropdown - dismiss it)
        self.fill_text(self.job_title_input, data["job_title"], "Job Title")
        self.page.keyboard.press("Escape")

        # Location and Job Ad Language are prefilled autocompletes - left as-is.

        # Work location type radio (on-site | remote | hybrid)
        self.check_radio(
            self.work_location_radio(data["work_location_type"]),
            f"Work location: {data['work_location_type']}",
        )

        # Rich-text sections (CKEditor iframes, in page order)
        self.fill_rich_text(0, data["company_description"], "Company Description")
        self.fill_rich_text(1, data["job_description"], "Job Description")
        self.fill_rich_text(2, data["qualifications"], "Qualifications")
        self.fill_rich_text(3, data["additional_information"], "Additional Information")

        # Video URL
        self.fill_text(self.video_input, data["video_url"], "Add Videos")

        # Save-as-template checkbox
        self.set_checkbox(
            self.save_template_checkbox, data["save_as_template"], "Save as template"
        )

        logger.info("--- Finished filling the form ---")
