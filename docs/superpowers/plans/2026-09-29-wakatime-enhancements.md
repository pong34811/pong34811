# WakaTime Enhancements & Ponytail Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `.github/scripts/update_waka.py` to use Python Standard Library (zero external dependencies), add daily active Projects badges, and remove `pip install requests` from GitHub Actions.

**Architecture:** A standalone Python 3.12 script using `urllib.request` with HTTP Basic Auth to fetch daily WakaTime summary statistics, format top languages, editors, and projects, and update `README.md` delimiter markers cleanly.

**Tech Stack:** Python 3.12 (`urllib.request`, `urllib.parse`, `base64`, `json`), GitHub Actions (`update-wakatime.yml`).

## Global Constraints

- No external Python dependencies (zero pip installs).
- Preserve all existing README badges, typing SVG, and profile sections.
- Gracefully handle zero coding time (`today_secs == 0`) and empty projects list.
- Display up to Top 4 projects for today as badges below Editors.

---

### Task 1: Refactor `update_waka.py` with Stdlib and Projects Badges

**Files:**
- Modify: `.github/scripts/update_waka.py`
- Create: `.github/scripts/test_update_waka.py`

**Interfaces:**
- Consumes: `WAKA_API_KEY` from environment variables, `README.md` content between `<!-- START_WAKA_TODAY -->` and `<!-- END_WAKA_TODAY -->`.
- Produces: Updated `README.md` containing today's stats, language progress bars, editor badges, and project badges.

- [ ] **Step 1: Write an offline test script for `update_waka.py`**

Create `.github/scripts/test_update_waka.py` to verify data extraction, project badge rendering, and markdown block generation without hitting the real WakaTime network endpoint:

```python
import unittest
from update_waka import fmt_time, progress_bar, generate_block

class TestUpdateWaka(unittest.TestCase):
    def test_fmt_time(self):
        self.assertEqual(fmt_time(3600), "1h 0m")
        self.assertEqual(fmt_time(7320), "2h 2m")
        self.assertEqual(fmt_time(45), "0m")
        self.assertEqual(fmt_time(125), "2m")

    def test_progress_bar(self):
        bar = progress_bar(50, width=10)
        self.assertEqual(bar, "█████░░░░░")

    def test_generate_block_with_projects(self):
        data = {
            "grand_total": {"total_seconds": 3600, "text": "1 hr"},
            "languages": [{"name": "Python", "percent": 100, "total_seconds": 3600}],
            "editors": [{"name": "VS Code", "total_seconds": 3600}],
            "projects": [
                {"name": "my-project", "total_seconds": 2400},
                {"name": "another_app", "total_seconds": 1200}
            ]
        }
        block = generate_block(data)
        self.assertIn("Today-1%20hr-6C63FF", block)
        self.assertIn("Python", block)
        self.assertIn("Editor-VS%20Code%201h%200m", block)
        self.assertIn("Project-my--project%2040m-3776AB", block)
        self.assertIn("Project-another_app%2020m-3776AB", block)

    def test_generate_block_without_projects(self):
        data = {
            "grand_total": {"total_seconds": 1800, "text": "30 mins"},
            "languages": [{"name": "JavaScript", "percent": 100, "total_seconds": 1800}],
            "editors": [{"name": "Edge", "total_seconds": 1800}],
            "projects": []
        }
        block = generate_block(data)
        self.assertNotIn("Project-", block)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify failure before refactoring**

Run: `python .github/scripts/test_update_waka.py`
Expected: FAIL with `ImportError: cannot import name 'generate_block'`

- [ ] **Step 3: Implement modular stdlib-based `update_waka.py`**

Replace `.github/scripts/update_waka.py` with:

```python
import os
import sys
import json
import base64
import urllib.request
import urllib.parse

API_KEY = os.environ.get("WAKA_API_KEY")
BASE = "https://wakatime.com/api/v1"
README = "README.md"

def fmt_time(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m"

def progress_bar(percent, width=40):
    filled = round(percent / 100 * width)
    return "█" * filled + "░" * (width - filled)

def clean_badge_label(text):
    # Shields.io converts double dash to single dash in path notation
    return urllib.parse.quote(text.replace("-", "--"))

def fetch(endpoint):
    if not API_KEY:
        raise ValueError("WAKA_API_KEY environment variable is not set")
    auth_bytes = f"{API_KEY}:".encode("utf-8")
    auth_header = "Basic " + base64.b64encode(auth_bytes).decode("ascii")
    req = urllib.request.Request(
        f"{BASE}{endpoint}",
        headers={"Authorization": auth_header, "User-Agent": "WakaTime-Readme-Bot"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def generate_block(td):
    gt = td["grand_total"]
    today_total = gt["text"]

    langs = sorted(td.get("languages", []), key=lambda x: x["total_seconds"], reverse=True)
    editors = sorted(td.get("editors", []), key=lambda x: x["total_seconds"], reverse=True)
    projects = sorted(td.get("projects", []), key=lambda x: x["total_seconds"], reverse=True)

    lang_lines = []
    for l in langs[:4]:
        pct = round(l["percent"])
        bar = progress_bar(pct)
        t = fmt_time(l["total_seconds"])
        name = l["name"][:10]
        lang_lines.append(f"{name:<10} {bar}  {pct:>2}%   {t:>6}")
    lang_block = "\n".join(lang_lines)

    ed_badges = []
    for e in editors:
        t = fmt_time(e["total_seconds"])
        name_clean = urllib.parse.quote(e["name"])
        color = "0078D7" if "Edge" in e["name"] else "6C63FF"
        ed_badges.append(
            f'<img src="https://img.shields.io/badge/Editor-{name_clean}%20{t}-{color}?style=flat-square" />'
        )
    ed_line = "  ".join(ed_badges)

    proj_badges = []
    for p in projects[:4]:
        t = fmt_time(p["total_seconds"])
        name_clean = clean_badge_label(p["name"])
        t_clean = urllib.parse.quote(t)
        proj_badges.append(
            f'<img src="https://img.shields.io/badge/Project-{name_clean}%20{t_clean}-3776AB?style=flat-square" />'
        )
    proj_line = f'\n\n<p align="center">\n  {"  ".join(proj_badges)}\n</p>' if proj_badges else ""

    today_badge = f'https://img.shields.io/badge/Today-{urllib.parse.quote(today_total)}-6C63FF?style=for-the-badge'

    return f"""<p align="center">
  <img src="https://wakatime.com/badge/user/1e5abd91-095a-4b62-bded-8eea82c90849.svg" />
</p>

<p align="center">
  <img src="{today_badge}" />
</p>

```
{lang_block}
```

<p align="center">
  {ed_line}
</p>{proj_line}"""

def update_readme_text(content, new_block):
    start = "<!-- START_WAKA_TODAY -->"
    end = "<!-- END_WAKA_TODAY -->"

    if start in content and end in content:
        before = content.split(start)[0]
        after = content.split(end)[1]
        return f"{before}{start}\n{new_block}\n{end}{after}"
    return content

def main():
    today = fetch("/users/current/summaries?range=today")
    td = today["data"][0]
    gt = td["grand_total"]
    today_secs = gt["total_seconds"]

    if not today_secs:
        print("No data today, skipping update")
        return

    new_block = generate_block(td)

    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    updated = update_readme_text(content, new_block)

    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)

    print("README updated successfully")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest .github/scripts/test_update_waka.py`
Expected: OK (3 tests pass)

- [ ] **Step 5: Clean up test file and commit**

```bash
git add .github/scripts/update_waka.py
git commit -m "feat(waka): optimize script with stdlib urllib and add projects badges"
```

---

### Task 2: Update GitHub Actions Workflow

**Files:**
- Modify: `.github/workflows/update-wakatime.yml:19`

**Interfaces:**
- Consumes: GitHub Secrets `WAKA_API_KEY`.
- Produces: GitHub Actions job executing without installing `requests`.

- [ ] **Step 1: Edit `.github/workflows/update-wakatime.yml` to remove `pip install requests`**

Remove the line `- run: pip install requests`. The updated job steps:

```yaml
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python .github/scripts/update_waka.py
        env:
          WAKA_API_KEY: ${{ secrets.WAKA_API_KEY }}
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add README.md
          git diff --staged --quiet || git commit -m "chore: auto-update WakaTime stats"
          git push
```

- [ ] **Step 2: Verify YAML syntax**

Run: `python -c "import urllib.request; print('Python OK')"`

- [ ] **Step 3: Commit workflow change**

```bash
git add .github/workflows/update-wakatime.yml
git commit -m "chore(ci): eliminate pip install requests dependency from workflow"
```

---

### Task 3: End-to-End Verification & Formatting Check

**Files:**
- Verify: `README.md`, `.github/scripts/update_waka.py`, `.github/workflows/update-wakatime.yml`

- [ ] **Step 1: Run temporary mock test to verify README update formatting**

Run python snippet in terminal to test `update_readme_text` on current `README.md` without damaging anything.

- [ ] **Step 2: Check Git status and diff**

Run: `git status` and `git diff HEAD~2` to confirm clean commits and changes.
