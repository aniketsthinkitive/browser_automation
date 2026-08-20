"""
Page Object for step 2 ("Details") of the SmartRecruiters job wizard
(https://www.smartrecruiters.com/app/jobs/ad/details).

The page lists the company's custom fields plus four default fields
(Industry, Function, Experience Level, Type of Employment). Every field
host component carries a human-readable `label` attribute, so locators
are label-based. Three interaction patterns exist:

- spl-input        -> plain text input (fill)
- spl-autocomplete -> lookup: click/type, then pick a suggestion
- spl-select       -> dropdown: click, then click a spl-select-option
"""

import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils import test_data

logger = logging.getLogger(__name__)


class DetailsPage:
    """Encapsulates every interaction with the job details page."""

    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(test_data.DEFAULT_TIMEOUT)
        self.next_button = page.locator(
            'spl-button[data-test="job-details-next-button"]'
        )

    def go_to_next_step(self) -> None:
        """Click Next and wait for the Hiring Team step to load."""
        self.next_button.scroll_into_view_if_needed()
        self.next_button.click()
        self.page.wait_for_url("**/jobs/ad/publish**")
        self.page.wait_for_load_state("networkidle")
        logger.info("Moved to the Hiring Team step: %s", self.page.url)

    # -----------------------------------------------------------------
    # Label-based locator factories
    # -----------------------------------------------------------------

    def _text_input(self, label: str):
        return self.page.locator(f"spl-input[label='{label}'] input")

    def _autocomplete_input(self, label: str):
        return self.page.locator(f"spl-autocomplete[label='{label}'] input")

    def _select(self, label: str):
        return self.page.locator(f"spl-select[label='{label}']")

    # -----------------------------------------------------------------
    # Field actions (each skips gracefully if the field is missing)
    # -----------------------------------------------------------------

    def fill_text_field(self, label: str, value: str) -> None:
        locator = self._text_input(label)
        if locator.count() == 0:
            logger.warning("Text field '%s' not found - skipping", label)
            return
        locator.scroll_into_view_if_needed()
        locator.fill(value)
        logger.info("Filled '%s' with '%s'", label, value)

    def fill_autocomplete(self, label: str, value: str | None) -> bool:
        """
        Fill a lookup field. Types `value` (if given) to filter the
        suggestions, then clicks the first real suggestion.
        With value=None the first available option is picked as-is.
        Returns True if a value was picked, False if the field was skipped.
        """
        host = self.page.locator(f"spl-autocomplete[label='{label}']")
        locator = self._autocomplete_input(label)
        if locator.count() == 0:
            logger.warning("Autocomplete '%s' not found - skipping", label)
            return False
        locator.scroll_into_view_if_needed()
        locator.click()
        if value:
            locator.fill(value)
        # Give the suggestion dropdown time to load its options.
        self.page.wait_for_timeout(800)
        # Click the first real option - some lists start with a
        # "--Select ...--" placeholder entry that must be skipped.
        options = host.locator("spl-select-option").filter(has_not_text="--Select")
        try:
            options.first.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            # Dropdown did not open (or closed again) - toggle it once more.
            locator.click()
            try:
                options.first.wait_for(state="visible", timeout=3000)
            except PlaywrightTimeoutError:
                logger.warning(
                    "Autocomplete '%s': no suggestions visible - skipping", label
                )
                self.page.keyboard.press("Escape")
                return False
        options.first.click()
        logger.info(
            "Autocomplete '%s': picked first suggestion%s",
            label,
            f" for '{value}'" if value else "",
        )
        return True

    def select_option(self, label: str, option_text: str) -> None:
        """Open a spl-select dropdown and click the option with this text."""
        host = self._select(label)
        if host.count() == 0:
            logger.warning("Select '%s' not found - skipping", label)
            return
        host.scroll_into_view_if_needed()
        host.click()
        self.page.wait_for_timeout(400)
        host.locator("spl-select-option").filter(has_text=option_text).first.click()
        logger.info("Selected '%s' in '%s'", option_text, label)

    # -----------------------------------------------------------------
    # High-level action: fill the whole details step
    # -----------------------------------------------------------------

    def fill_details(self, data: dict) -> None:
        """
        Fill the details page from a dict shaped like:
        {"text": {label: value}, "autocomplete": {label: value_or_None},
         "select": {label: option_text}}
        """
        logger.info("--- Starting to fill the details page ---")
        # The custom fields render asynchronously after the SPA route
        # change - wait until the first field component is actually there.
        self.page.locator(
            '[data-test="job-details-custom-fields"] spl-input'
        ).first.wait_for(state="visible")
        for label, value in data.get("text", {}).items():
            self.fill_text_field(label, value)
        # Some lookup fields are conditional: they only appear after another
        # field gets a value (e.g. Value Level -> EG_MG_Mapping -> Level).
        # A first-pass skip is therefore retried in a second pass.
        skipped = []
        for label, value in data.get("autocomplete", {}).items():
            if not self.fill_autocomplete(label, value):
                skipped.append((label, value))
        # Retry until every remaining field is filled or no more progress
        # is made (each retry can reveal the next conditional field).
        for _ in range(3):
            if not skipped:
                break
            logger.info("Retrying %d conditional field(s)...", len(skipped))
            self.page.wait_for_timeout(1000)
            still_skipped = []
            for label, value in skipped:
                if not self.fill_autocomplete(label, value):
                    still_skipped.append((label, value))
            if len(still_skipped) == len(skipped):
                break
            skipped = still_skipped
        for label, option in data.get("select", {}).items():
            self.select_option(label, option)
        logger.info("--- Finished filling the details page ---")
