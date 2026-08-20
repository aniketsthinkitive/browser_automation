"""
Per-row PASS/FAIL reporting for the CSV-driven run.

Every processed CSV row gets one line in results.csv (written in append
mode per record, so a crash mid-run still leaves all completed rows on
disk) plus a live console log line. Failure reasons are recorded at two
levels: a plain-language `failed_reason` a non-technical reader can act
on, and the raw `error_detail` for debugging.
"""

import csv
import logging
from datetime import datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils import test_data

logger = logging.getLogger(__name__)

HEADER = [
    "row",
    "job_title",
    "status",
    "failed_step",
    "failed_reason",
    "error_detail",
    "screenshot",
    "timestamp",
]


def humanize_error(exc: Exception, step: str) -> str:
    """Translate an exception into a plain-language failure reason."""
    msg = str(exc).strip()
    first_line = msg.splitlines()[0] if msg else type(exc).__name__

    if isinstance(exc, AssertionError):
        # save() already raises with a readable message (e.g. banner text)
        return first_line
    if isinstance(exc, PlaywrightTimeoutError):
        if step == "Save":
            return (
                "Save did not complete - the page stayed on the wizard "
                "(possible validation error, check the screenshot)"
            )
        return f"A field or button did not appear on the page in time ({first_line})"
    lowered = msg.lower()
    if "econnrefused" in lowered or "browser has been closed" in lowered or "target closed" in lowered:
        return "Chrome debug connection lost - restart start_chrome_debug.sh and log in again"
    return first_line[:200]


class Reporter:
    """Appends one results.csv line per row and tracks the run summary."""

    def __init__(self, path: str = test_data.RESULTS_CSV_PATH):
        self.path = path
        self.passed = 0
        self.failed = 0
        self._header_written = False

    def record(
        self,
        row_num: int,
        job_title: str,
        status: str,
        failed_step: str = "",
        failed_reason: str = "",
        error_detail: str = "",
        screenshot: str = "",
    ) -> None:
        mode = "a" if self._header_written else "w"
        with open(self.path, mode, newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not self._header_written:
                writer.writerow(HEADER)
                self._header_written = True
            writer.writerow(
                [
                    row_num,
                    job_title,
                    status,
                    failed_step,
                    failed_reason,
                    error_detail,
                    screenshot,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )
        if status == "PASS":
            self.passed += 1
            logger.info("[row %s] '%s' ... PASS", row_num, job_title)
        else:
            self.failed += 1
            logger.error(
                "[row %s] '%s' ... FAIL at %s: %s (screenshot: %s)",
                row_num,
                job_title,
                failed_step,
                failed_reason,
                screenshot or "n/a",
            )

    def summary(self) -> tuple:
        return self.passed, self.failed
