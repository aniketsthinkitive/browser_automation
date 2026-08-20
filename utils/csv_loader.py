"""
Load job rows from data/jobs.csv and turn each row into the three dicts
the page objects already accept (FORM_DATA / DETAILS_DATA / HIRING_TEAM_DATA
shapes) - the page objects need no changes.

Column conventions:
- Flat columns map straight into the form / hiring-team dicts by name.
- "d_text.<Label>" / "d_select.<Label>": Details-step field located by its
  visible label. An EMPTY cell omits the field entirely (left as-is).
- "d_auto.<Label>": Details-step autocomplete. An EMPTY cell means
  "pick the first suggestion" (value None, the common case); the literal
  value SKIP omits the field entirely.
- save_as_template: true/false (case-insensitive).
- Empty hiring-team cells are skipped by the existing truthy checks.
"""

import csv
from dataclasses import dataclass

from utils import test_data

FORM_FIELDS = (
    "job_title",
    "location",
    "work_location_type",
    "company_description",
    "job_description",
    "qualifications",
    "additional_information",
    "video_url",
)
HIRING_FIELDS = ("hiring_role", "target_start_date", "position_id", "hiring_manager")


@dataclass
class JobRow:
    row_num: int  # 1-based data row index (header not counted)
    job_title: str
    form_data: dict
    details_data: dict
    hiring_team_data: dict


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "yes", "1")


def load_jobs(csv_path: str = test_data.JOBS_CSV_PATH) -> list:
    """Read the CSV and return one JobRow per data row."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row_num, raw in enumerate(csv.DictReader(f), start=1):
            form_data = {k: (raw.get(k) or "").strip() for k in FORM_FIELDS}
            form_data["save_as_template"] = _parse_bool(raw.get("save_as_template") or "")

            details = {"text": {}, "autocomplete": {}, "select": {}}
            for col, value in raw.items():
                if col is None:
                    continue
                value = (value or "").strip()
                if col.startswith("d_text."):
                    if value:
                        details["text"][col[len("d_text."):]] = value
                elif col.startswith("d_auto."):
                    if value.upper() != "SKIP":
                        details["autocomplete"][col[len("d_auto."):]] = value or None
                elif col.startswith("d_select."):
                    if value:
                        details["select"][col[len("d_select."):]] = value

            hiring = {k: ((raw.get(k) or "").strip() or None) for k in HIRING_FIELDS}

            rows.append(
                JobRow(row_num, form_data["job_title"], form_data, details, hiring)
            )
    if not rows:
        raise ValueError(f"No data rows found in {csv_path}")
    return rows
