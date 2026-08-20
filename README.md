# Browser Automation - Form Fill Test

A Python + Playwright + pytest project that attaches to your real Chrome
browser (over CDP), navigates to a website, and fills out a form with sample
test data using the Page Object Model (POM). The Submit button is
intentionally not clicked.

Attaching to real Chrome (instead of launching Chromium) avoids bot
protection: the browser has a normal fingerprint, `navigator.webdriver` is
false, and the login session persists in Chrome's own profile.

## Quick Start (the commands you need)

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

If `pytest` fails with `ECONNREFUSED 127.0.0.1:9222`, the debug Chrome
window was closed - just run `./start_chrome_debug.sh` again.

## Project Structure

```text
browser_automation/
│
├── tests/
│   └── test_form_fill.py    # The test: step 1 → Next → step 2 → pause
│
├── pages/
│   ├── form_page.py         # Page Object: step 1 "Create" (job ad form)
│   └── details_page.py      # Page Object: step 2 "Details" (custom fields)
│
├── utils/
│   └── test_data.py         # URLs, timeouts, FORM_DATA and DETAILS_DATA
│
├── start_chrome_debug.sh    # Starts real Chrome with the CDP debug port
├── conftest.py              # Makes pages/ and utils/ importable
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

All data lives in `utils/test_data.py`:

- `FORM_DATA` - step 1 values (job title, descriptions, video URL, ...)
- `DETAILS_DATA` - step 2 values, grouped by field type:
  `text` (typed as-is), `autocomplete` (value filters the suggestions and
  the first match is picked; `None` picks the first available option),
  and `select` (option is chosen by its visible text)

Fields that don't exist on the page are skipped automatically with a
warning log.

## Run the Test

```bash
# 1. Start your real Chrome with remote debugging (once; leave it running)
./start_chrome_debug.sh

# 2. Log in to the website in that Chrome window (first time only -
#    the profile at ~/.chrome-debug-profile remembers the session)

# 3. Run the test
pytest -v
```

What happens:

1. Playwright attaches to the running Chrome at `http://localhost:9222`
   and opens a new tab in it.
2. Navigates to `BASE_URL` and waits for the page to fully load.
3. Takes a `before_filling` screenshot.
4. Fills step 1 ("Create"): job title, work location type, the four
   CKEditor rich-text sections, and the video URL.
5. Takes an `after_filling` screenshot, then clicks **Next**.
6. Fills step 2 ("Details"): text fields, lookup/autocomplete fields
   (first real suggestion is picked), and dropdowns. Conditional fields
   that appear mid-fill (e.g. EG_MG_Mapping, Level) are retried until
   filled. Takes an `after_filling_details` screenshot.
7. Pauses 5 seconds so you can visually verify the values.
8. Closes only the tab it opened and disconnects - your Chrome keeps
   running. **The Details step's Next button is never clicked.**

Screenshots are saved in `screenshots/`. On any error, an `error.png`
screenshot is captured automatically.

## Design Notes

- **Page Object Model** – tests never use raw selectors; all locators and
  actions live in `pages/form_page.py`.
- **Separate test data** – `utils/test_data.py` holds all data and config.
- **Explicit waits** – Playwright auto-waits for elements; the only fixed
  wait is the intentional post-fill verification pause.
- **Graceful skipping** – missing fields are logged and skipped, so the
  same test works while locators are still placeholders.

## Future Enhancements (design allows for)

- Login tests / multi-page forms (add new page objects in `pages/`)
- Dynamic dropdowns, OTP handling
- Multiple browsers & parallel execution (`pytest-xdist`)
- Data-driven testing via CSV/Excel (swap `FORM_DATA` source)
- HTML reports (`pytest-html`), video recording (Playwright contexts)
- Retry mechanism (`pytest-rerunfailures`)
- Environment configs & headless CI/CD execution
