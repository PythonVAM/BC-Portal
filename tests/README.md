# Regression tests

Install Playwright: `pip install playwright && playwright install chromium`

Run a single test: `python tests/uat_grouped_e2e.py`

Run them all: `for f in tests/uat_*.py; do echo "=== $f ==="; python "$f"; done`
