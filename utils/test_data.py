"""
Central place for all test configuration and sample form data.

Keeping data separate from page objects and tests means:
- Locators can change without touching data.
- Data-driven testing (CSV/Excel) can later replace this module
  without changing the page objects or tests.
"""

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Change this to your website's URL before running the test.
BASE_URL = "https://www.smartrecruiters.com/app/jobs/ad/create"

# CDP endpoint of the already-running real Chrome we attach to.
# Start Chrome first with: ./start_chrome_debug.sh
CDP_URL = "http://localhost:9222"

# How long (ms) Playwright should wait for elements before failing.
DEFAULT_TIMEOUT = 10_000

# Pause (seconds) after filling the form so a human can verify the values.
VERIFICATION_PAUSE_SECONDS = 5

# Where screenshots are saved.
SCREENSHOT_DIR = "screenshots"

# Sample file used for file-upload fields (created automatically if missing).
UPLOAD_FILE_PATH = "sample_upload.txt"

# Max time (seconds) the test waits for you to finish logging in manually.
LOGIN_WAIT_SECONDS = 300


# ---------------------------------------------------------------------------
# Sample form data
# ---------------------------------------------------------------------------

FORM_DATA = {
    "job_title": "Senior Software Engineer",
    "work_location_type": "hybrid",      # on-site | remote | hybrid
    "company_description": (
        "We are a fast-growing technology company building products that "
        "help businesses hire better. Our teams value ownership, "
        "collaboration, and continuous learning."
    ),
    "job_description": (
        "As a Senior Software Engineer you will design, build, and maintain "
        "scalable web applications, review code, mentor junior engineers, "
        "and collaborate with product and design to ship high-quality "
        "features."
    ),
    "qualifications": (
        "5+ years of professional software development experience. Strong "
        "knowledge of Python or JavaScript, REST APIs, and relational "
        "databases. Experience with automated testing and CI/CD pipelines."
    ),
    "additional_information": (
        "Flexible working hours, health insurance, learning budget, and a "
        "collaborative hybrid work culture."
    ),
    "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "save_as_template": False,           # Checkbox
}

# ---------------------------------------------------------------------------
# Step 2 ("Details") data - fields are located by their visible label.
#   text:         plain inputs - the value is typed as-is
#   autocomplete: lookup fields - the value filters suggestions and the
#                 FIRST suggestion is picked; use None to just pick the
#                 first available option
#   select:       dropdowns - the option with this visible text is clicked
# Fields not listed here are simply left empty.
# ---------------------------------------------------------------------------

DETAILS_DATA = {
    "text": {
        "DPF SI ID No": "SI-12345",
        "TSIN Requester": "Jyoti Varade",
        "Factory Head": "Test Manager",
        "Job Description": "Senior Software Engineer",
        "Primary Skills": "Python, Playwright, REST APIs",
        "Recruitment Date": "01/09/2026",
        "Org Code": "ORG-123",
        "TSIN ID": "TSIN-001",
        "Planned Start Date": "15/09/2026",
        "Project PU": "PU-01",
    },
    "autocomplete": {
        "Cost Center": None,
        "Factory": None,
        "Billable": "Yes",
        "Demand Type": None,
        "Criticality": None,
        "Value Level": None,
        # Conditional fields: EG_MG_Mapping appears after Value Level is
        # chosen, and Level appears after EG_MG_Mapping.
        "EG_MG_Mapping": None,
        "Level": None,
        "IJP": None,
        "Role": None,
    },
    "select": {
        "Function": "Information Technology",
        "Experience Level": "Mid-Senior Level",
        # "Type of Employment" is already prefilled with "Full-time"
    },
}
