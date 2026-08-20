# Ensures `pages` and `utils` packages are importable when pytest runs
# from the project root. Having conftest.py here adds this directory to
# sys.path automatically - no packaging setup required.
#
# Also holds the shared fixtures for the CSV-driven run: one CDP
# connection and ONE reused browser tab for the whole session (no matter
# how many CSV rows there are), plus the results.csv reporter.

import logging

import pytest
from playwright.sync_api import sync_playwright, Error as PlaywrightError

from utils import test_data
from utils.reporter import Reporter

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser():
    """
    Attach once to the already-running real Chrome over CDP for the whole
    run. Using your real Chrome (instead of launching Chromium) avoids bot
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
        yield browser
        browser.close()
        logger.info("Disconnected from Chrome (browser left running)")


class _TabHolder:
    """Holds the single tab shared by every row of the run."""

    page = None


@pytest.fixture(scope="session")
def _tab_holder(browser):
    holder = _TabHolder()
    yield holder
    if holder.page is not None and not holder.page.is_closed():
        holder.page.close()
        logger.info("Closed the automation tab")


@pytest.fixture
def page(browser, _tab_holder):
    """
    The ONE tab used for the entire run. Each row re-navigates it to the
    create-job URL; it is only reopened if it crashed or was closed.
    """
    if _tab_holder.page is None or _tab_holder.page.is_closed():
        _tab_holder.page = browser.contexts[0].new_page()
        logger.info("Opened the automation tab")
    return _tab_holder.page


@pytest.fixture(scope="session")
def reporter():
    """Per-row results.csv writer; prints the run summary at the end."""
    rep = Reporter()
    yield rep
    passed, failed = rep.summary()
    line = f"=== SUMMARY: {passed} passed, {failed} failed - see {rep.path} ==="
    print(f"\n{line}")
    logger.info(line)
