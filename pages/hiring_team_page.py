"""
Page Object for step 3 ("Hiring Team") of the SmartRecruiters job wizard
(https://www.smartrecruiters.com/app/jobs/ad/publish).

The page contains the hiring team table, the Headcount/Positions form,
and the publishing preferences. This page has the green **Publish**
button - it is intentionally never clicked (and neither is Save).
"""

import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils import test_data

logger = logging.getLogger(__name__)


class HiringTeamPage:
    """Encapsulates every interaction with the hiring team page."""

    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(test_data.DEFAULT_TIMEOUT)

        # Hiring role dropdown of the existing team member row(s)
        self.member_role_select = page.locator(
            'spl-select[data-test="edit-hiring-team-member-role"]'
        )
        # Positions form
        self.start_date_input = page.locator(
            'spl-date-field[data-test="job-headcount-position-form-start-date"] '
            'input[type="text"]'
        )
        self.position_id_input = page.locator(
            '[data-test="job-headcount-position-form-positionId"] input'
        )
        self.hiring_manager_host = page.locator(
            '[data-test="job-headcount-position-form-hiring-manager"]'
        )

    def set_member_hiring_role(self, role: str) -> None:
        """Pick a hiring role for the first existing team member row."""
        # The team table loads asynchronously (spinner first) - wait for it.
        try:
            self.member_role_select.first.wait_for(state="visible")
        except PlaywrightTimeoutError:
            logger.warning("No hiring team member row found - skipping role")
            return
        select = self.member_role_select.first
        select.scroll_into_view_if_needed()
        select.click()
        self.page.wait_for_timeout(400)
        select.locator("spl-select-option").filter(has_text=role).first.click()
        logger.info("Set hiring role of first team member to '%s'", role)

    def fill_target_start_date(self, value: str) -> None:
        """Fill the position's target start date (format: YYYY-MM-DD)."""
        if self.start_date_input.count() == 0:
            logger.warning("Target start date field not found - skipping")
            return
        self.start_date_input.first.scroll_into_view_if_needed()
        self.start_date_input.first.fill(value)
        self.page.keyboard.press("Escape")  # close the date picker popup
        logger.info("Filled 'Target start date' with '%s'", value)

    def fill_position_id(self, value: str) -> None:
        if self.position_id_input.count() == 0:
            logger.warning("Position ID field not found - skipping")
            return
        self.position_id_input.scroll_into_view_if_needed()
        self.position_id_input.fill(value)
        logger.info("Filled 'Position ID' with '%s'", value)

    def fill_hiring_manager(self, search_text: str) -> None:
        """
        Search the employee picker and pick the first match. The field is
        optional and the directory may return no results - skipped then.
        """
        hm_input = self.hiring_manager_host.locator("input").first
        if self.hiring_manager_host.count() == 0:
            logger.warning("Hiring Manager picker not found - skipping")
            return
        hm_input.scroll_into_view_if_needed()
        hm_input.click()
        hm_input.fill(search_text)
        self.page.wait_for_timeout(2000)  # directory search is debounced
        options = self.hiring_manager_host.locator(
            "spl-select-option:not([disabled])"
        )
        try:
            options.first.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            logger.warning(
                "Hiring Manager: no match for '%s' - skipping (optional field)",
                search_text,
            )
            hm_input.fill("")
            self.page.keyboard.press("Escape")
            return
        options.first.click()
        logger.info("Hiring Manager: picked first match for '%s'", search_text)

    def fill_hiring_team(self, data: dict) -> None:
        """Fill the hiring team step. Publish/Save are NEVER clicked."""
        logger.info("--- Starting to fill the hiring team page ---")
        # Wait for the page's async content (team table renders late)
        self.page.locator(
            '[data-test="job-headcount-position-form-positionId"]'
        ).wait_for(state="visible")

        if data.get("hiring_role"):
            self.set_member_hiring_role(data["hiring_role"])
        if data.get("target_start_date"):
            self.fill_target_start_date(data["target_start_date"])
        if data.get("position_id"):
            self.fill_position_id(data["position_id"])
        if data.get("hiring_manager"):
            self.fill_hiring_manager(data["hiring_manager"])
        logger.info("--- Finished filling the hiring team page ---")
