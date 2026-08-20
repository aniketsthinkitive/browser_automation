@echo off
REM Start real Google Chrome with remote debugging enabled so Playwright
REM can attach to it over CDP (see tests/test_form_fill.py).
REM Windows equivalent of start_chrome_debug.sh.
REM
REM Chrome 136+ refuses --remote-debugging-port on your default profile,
REM so a dedicated profile directory is used. Log in to SmartRecruiters
REM once in this window - the profile keeps the session for future runs.

set PORT=9222
set PROFILE_DIR=%USERPROFILE%\.chrome-debug-profile

REM Find the Chrome executable (covers the common install locations)
set CHROME="%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% (
    echo ERROR: chrome.exe not found. Edit this file and set CHROME to your Chrome path.
    exit /b 1
)

start "" %CHROME% --remote-debugging-port=%PORT% --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check

echo Chrome started with debugging on http://localhost:%PORT%
echo Profile: %PROFILE_DIR% (log in once; the session is remembered)
