"""
CSV-driven run: one test per row of data/jobs.csv. Each row fills the
3-step job wizard in the SAME single tab and clicks **Save** on the last
step (the green Publish button is never clicked).

A failed row is recorded in results.csv with the step it failed at, a
plain-language reason, and an error screenshot - then the run continues
with the next row (the shared tab simply re-navigates to the create URL).
"""

import logging
from datetime import datetime

import pytest
from playwright.sync_api import Page

from pages.form_page import FormPage
from pages.details_page import DetailsPage
from pages.hiring_team_page import HiringTeamPage
from utils.csv_loader import load_jobs
from utils.reporter import humanize_error

logger = logging.getLogger(__name__)

# One screenshot folder per run so batches never overwrite each other.
RUN_ID = datetime.now().strftime("run_%Y%m%d_%H%M%S")

ROWS = load_jobs()


@pytest.mark.parametrize(
    "job", ROWS, ids=lambda j: f"row{j.row_num:02d}-{j.job_title[:30]}"
)
def test_create_and_save_job(page: Page, reporter, job):
    """Fill all three wizard steps from one CSV row and click Save."""
    form_page = FormPage(page)
    step = "Login/Navigation"

    try:
        # Fresh wizard in the shared tab (also recovers from a failed row).
        form_page.open()
        form_page.wait_for_manual_login()

        step = "Step 1: Create"
        form_page.fill_form(job.form_data)
        form_page.take_screenshot(f"{RUN_ID}/row{job.row_num:02d}_step1")

        step = "Step 2: Details"
        form_page.go_to_next_step()
        details_page = DetailsPage(page)
        details_page.fill_details(job.details_data)
        form_page.take_screenshot(f"{RUN_ID}/row{job.row_num:02d}_step2")

        step = "Step 3: Hiring Team"
        details_page.go_to_next_step()
        hiring_team_page = HiringTeamPage(page)
        hiring_team_page.fill_hiring_team(job.hiring_team_data)
        form_page.take_screenshot(f"{RUN_ID}/row{job.row_num:02d}_step3")

        step = "Save"
        hiring_team_page.save()

        reporter.record(job.row_num, job.job_title, "PASS")

    except Exception as exc:
        screenshot = ""
        try:
            screenshot = form_page.take_screenshot(
                f"{RUN_ID}/row{job.row_num:02d}_error"
            )
        except Exception:
            logger.warning("Could not capture the error screenshot")
        reporter.record(
            job.row_num,
            job.job_title,
            "FAIL",
            failed_step=step,
            failed_reason=humanize_error(exc, step),
            error_detail=f"{type(exc).__name__}: {exc}"[:300],
            screenshot=screenshot,
        )
        raise
