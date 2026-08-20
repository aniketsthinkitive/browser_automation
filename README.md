# Browser Automation - Form Fill Test

A Python + Playwright + pytest project that attaches to your real Chrome
browser (over CDP) and creates one SmartRecruiters job ad per row of
`data/jobs.csv`, using the Page Object Model (POM). Each row fills the
3-step wizard and clicks **Save** on the last step (the green **Publish**
button is never clicked), so every successful row creates a real saved
job in the account. Each row's PASS/FAIL result - with the failure step,
a plain-language reason, and an error screenshot - is written to
`results.csv` and printed live in the console.

The whole run uses **one single browser tab**, no matter how many CSV
rows there are - each row just re-navigates that tab back to the
create-job page.

Attaching to real Chrome (instead of launching Chromium) avoids bot
protection: the browser has a normal fingerprint, `navigator.webdriver` is
false, and the login session persists in Chrome's own profile.

## Quick Start (the commands you need)

**Linux / macOS:**

```bash
cd ~/Documents/Learn/form-filler/browser_automation

# 1. Activate the virtual environment
source venv/bin/activate

# 2. Start your real Chrome with remote debugging
#    (only needed if that Chrome window is not already open)
./start_chrome_debug.sh

# 3. First time only: log in to SmartRecruiters in that Chrome window
#    (the profile at ~/.chrome-debug-profile remembers the session)

# 4. Run the test
pytest -v
```

**Windows (cmd):**

```bat
cd path\to\form-filler\browser_automation

REM 1. Activate the virtual environment
venv\Scripts\activate

REM 2. Start your real Chrome with remote debugging
start_chrome_debug.bat

REM 3. First time only: log in to SmartRecruiters in that Chrome window
REM    (the profile at %USERPROFILE%\.chrome-debug-profile remembers it)

REM 4. Run the test
pytest -v
```

Windows PowerShell users: activate the venv with
`venv\Scripts\Activate.ps1` and start Chrome with
`.\start_chrome_debug.bat`; the rest is identical.

If `pytest` fails with `ECONNREFUSED 127.0.0.1:9222`, the debug Chrome
window was closed - just run `./start_chrome_debug.sh` again.

## Project Structure

```text
browser_automation/
│
├── data/
│   └── jobs.csv             # One job ad per row - the input data
│
├── tests/
│   └── test_form_fill.py    # One test per CSV row: 3 steps → Save
│
├── pages/
│   ├── form_page.py         # Page Object: step 1 "Create" (job ad form)
│   ├── details_page.py      # Page Object: step 2 "Details" (custom fields)
│   └── hiring_team_page.py  # Page Object: step 3 "Hiring Team" + save()
│
├── utils/
│   ├── test_data.py         # URLs, timeouts, sample data shapes
│   ├── csv_loader.py        # Turns CSV rows into the page-object dicts
│   └── reporter.py          # Writes results.csv + console summary
│
├── results.csv              # Per-row PASS/FAIL report (created by a run)
├── start_chrome_debug.sh    # Starts real Chrome with the CDP debug port (Linux/macOS)
├── start_chrome_debug.bat   # Same for Windows
├── conftest.py              # Fixtures: CDP connection, the single tab, reporter
├── requirements.txt
├── pytest.ini
└── README.md
```

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install
```

## Configuration

URLs and timeouts live in `utils/test_data.py` (its `FORM_DATA` /
`DETAILS_DATA` / `HIRING_TEAM_DATA` dicts now only document the data
shapes - the run reads `data/jobs.csv`).

### The input CSV (`data/jobs.csv`)

One job ad per row. Column rules (full details in `utils/csv_loader.py`):

- Plain columns (`job_title`, `work_location_type`, descriptions,
  `hiring_role`, `target_start_date`, `position_id`, ...) map directly to
  the form. `save_as_template` is `true`/`false`.
- `d_text.<Label>` / `d_select.<Label>` - step 2 field with that visible
  label. Leave the cell EMPTY to skip the field.
- `d_auto.<Label>` - step 2 autocomplete. EMPTY cell = pick the first
  suggestion (the usual case); write `SKIP` to skip the field entirely.

Fields that don't exist on the page are skipped automatically with a
warning log.

### The results report (`results.csv`)

One line per processed row:

| column | meaning |
|---|---|
| `row`, `job_title` | which CSV row |
| `status` | `PASS` or `FAIL` |
| `failed_step` | where it broke: Step 1: Create / Step 2: Details / Step 3: Hiring Team / Save |
| `failed_reason` | plain-language reason, e.g. `Save rejected: 'Recruitment Date is required'` |
| `error_detail` | the raw technical error, for debugging |
| `screenshot` | full-page error screenshot path |

The file is written row by row, so even if a run is interrupted the
completed rows are already on disk. The console prints each row's result
live plus `=== SUMMARY: X passed, Y failed ===` at the end.

## Run the Test

```bash
# 1. Start your real Chrome with remote debugging (once; leave it running)
./start_chrome_debug.sh

# 2. Log in to the website in that Chrome window (first time only -
#    the profile at ~/.chrome-debug-profile remembers the session)

# 3. Run all CSV rows
pytest -v

# ...or re-run just one row
pytest -v -k row02
```

> **Note:** every row that passes SAVES a real job in the SmartRecruiters
> account. Try a 1-row CSV first.

What happens, per CSV row (all in the same single tab):

1. Playwright attaches to the running Chrome at `http://localhost:9222`
   and opens ONE tab (reused for every row).
2. Navigates to `BASE_URL` and waits for the page to fully load.
3. Fills step 1 ("Create"): job title, work location type, the four
   CKEditor rich-text sections, and the video URL. Clicks **Next**.
4. Fills step 2 ("Details"): text fields, lookup/autocomplete fields
   (first real suggestion is picked), and dropdowns. Conditional fields
   that appear mid-fill (e.g. EG_MG_Mapping, Level) are retried until
   filled. Clicks **Next**.
5. Fills step 3 ("Hiring Team"): the hiring role of the existing team
   member, the position's target start date and Position ID, and
   optionally the Hiring Manager picker.
6. Clicks **Save** (never Publish) and waits for the app to confirm the
   job was saved.
7. Records PASS or FAIL (step + reason + error screenshot) in
   `results.csv`, then continues with the next row - a failed row never
   stops the batch.

When all rows are done the tab is closed and Playwright disconnects -
your Chrome keeps running.

Screenshots are saved per run in `screenshots/run_<timestamp>/` as
`row01_step1.png` ... `row01_error.png`, so batches never overwrite each
other.

## Design Notes

- **Page Object Model** – tests never use raw selectors; all locators and
  actions live in `pages/form_page.py`.
- **Separate test data** – `utils/test_data.py` holds all data and config.
- **Explicit waits** – Playwright auto-waits for elements; the only fixed
  wait is the intentional post-fill verification pause.
- **Graceful skipping** – missing fields are logged and skipped, so the
  same test works while locators are still placeholders.
- **Single shared tab** – rows run one after another in one tab; do NOT
  run with `pytest-xdist` parallelism (the tab and Chrome profile are
  shared).

## Future Enhancements (design allows for)

- Login tests / multi-page forms (add new page objects in `pages/`)
- Dynamic dropdowns, OTP handling
- HTML reports (`pytest-html`), video recording (Playwright contexts)
- Retry mechanism (`pytest-rerunfailures`)
- Environment configs & headless CI/CD execution
