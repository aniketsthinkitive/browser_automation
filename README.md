# Browser Automation - Form Fill Test

A Python + Playwright + pytest project that attaches to your real Chrome
browser (over CDP), navigates to a website, and fills out a form with sample
test data using the Page Object Model (POM). The Submit button is
intentionally not clicked.

Attaching to real Chrome (instead of launching Chromium) avoids bot
protection: the browser has a normal fingerprint, `navigator.webdriver` is
false, and the login session persists in Chrome's own profile.

## Project Structure

```text
browser_automation/
│
├── tests/
│   └── test_form_fill.py    # The test: navigate → fill → verify pause
│
├── pages/
│   └── form_page.py         # Page Object: all locators + reusable actions
│
├── utils/
│   └── test_data.py         # BASE_URL, timeouts, and sample form data
│
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

1. Set your website URL in `utils/test_data.py`:

   ```python
   BASE_URL = "https://example.com"
   ```

2. Replace the placeholder locators in `pages/form_page.py`
   (e.g. `input[name='first_name']`) with the actual locators
   from your website. Fields that don't exist on the page are
   skipped automatically with a warning log.

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
4. Fills all text/email/password/phone/number/date fields, textarea,
   dropdowns, radio buttons, checkboxes, and uploads a sample file
   if a file input exists (scrolling to each element as needed).
5. Takes an `after_filling` screenshot.
6. Pauses 5 seconds so you can visually verify the values.
7. Closes only the tab it opened and disconnects - your Chrome keeps
   running. **Submit is never clicked.**

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
