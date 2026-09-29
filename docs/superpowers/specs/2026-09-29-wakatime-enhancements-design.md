# Design Spec: WakaTime Enhancements & Ponytail Optimization

- **Date:** 2026-09-29
- **Topic:** wakatime-enhancements
- **Status:** Approved

---

## 1. Overview & Goal

The repository `pong34811/pong34811` manages the GitHub Profile README for user `pong34811`.
Currently, an automated GitHub Actions workflow (`update-wakatime.yml`) runs every 6 hours to execute `.github/scripts/update_waka.py`, which pulls today's WakaTime statistics (languages and editors) and updates the section between `<!-- START_WAKA_TODAY -->` and `<!-- END_WAKA_TODAY -->` in `README.md`.

### Goals:
1. **Feature Expansion:** Add daily active **Projects** badges from the WakaTime API response to the README profile section.
2. **Ponytail Optimization (Over-engineering reduction):**
   - Replace the external dependency `requests` with Python Standard Library (`urllib.request`, `base64`, `json`).
   - Remove `pip install requests` from the GitHub Actions workflow to save runner time and eliminate dependency risks.
   - Streamline delimiter replacement logic in `README.md`.

---

## 2. Architecture & Components

```
+-------------------------------------------------------------+
| GitHub Actions: update-wakatime.yml (cron: 0 */6 * * *)     |
| - Environment: Ubuntu Latest, Python 3.12 (no pip install)  |
| - Secret: WAKA_API_KEY                                      |
+------------------------------+------------------------------+
                               |
                               v executes
+-------------------------------------------------------------+
| Script: .github/scripts/update_waka.py                      |
| - urllib.request + Basic Auth to WakaTime API               |
| - Extracts: Languages, Editors, Projects (Top 4)            |
| - Formats markdown + Shields.io badges                      |
| - Safely updates README.md delimiter section                |
+------------------------------+------------------------------+
                               |
                               v commits & pushes
+-------------------------------------------------------------+
| Target: README.md (<!-- START_WAKA_TODAY --> block)         |
+-------------------------------------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 GitHub Actions Workflow (`.github/workflows/update-wakatime.yml`)
- **Triggers:** Schedule `cron: "0 */6 * * *"` and manual `workflow_dispatch`.
- **Steps:**
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` with `python-version: "3.12"`
  3. `python .github/scripts/update_waka.py` (with `env: WAKA_API_KEY: ${{ secrets.WAKA_API_KEY }}`)
  4. Git config, commit if changed, and push.
- **Change:** Step `- run: pip install requests` is completely removed.

### 3.2 Python Script (`.github/scripts/update_waka.py`)
- **Imports:** `os`, `sys`, `json`, `base64`, `urllib.request`, `urllib.parse`. (All standard library, zero external dependencies).
- **Authentication:**
  ```python
  auth_header = "Basic " + base64.b64encode(f"{API_KEY}:".encode("utf-8")).decode("ascii")
  ```
- **Fetching:**
  - Endpoint: `https://wakatime.com/api/v1/users/current/summaries?range=today`
  - Timeout: 10 seconds.
- **Data Extraction:**
  - `grand_total`: Check if `total_seconds > 0`. If 0, log message and exit cleanly without error.
  - `languages`: Sort by `total_seconds` descending, take top 4, format with progress bar `█` / `░`.
  - `editors`: Sort by `total_seconds` descending, generate editor badges (`style=flat-square`).
  - `projects`: Extract `td.get("projects", [])`, sort by `total_seconds` descending, take top 4.
- **Project Badge Formatting:**
  - Format: `<img src="https://img.shields.io/badge/Project-{clean_name}%20{clean_time}-3776AB?style=flat-square" />`
  - Sanitization: Project names with hyphens/underscores/special chars properly URL-quoted.
  - Fallback: If no projects recorded today, omit the project badges row gracefully.
- **README Updating:**
  - Find start delimiter `<!-- START_WAKA_TODAY -->` and end delimiter `<!-- END_WAKA_TODAY -->`.
  - Replace content cleanly between markers.

---

## 4. Verification & Testing Plan

1. **Syntax & Dependency Verification:**
   - Execute python syntax check (`python -m py_compile .github/scripts/update_waka.py`).
2. **Offline / Mock Simulation:**
   - Run a test script passing sample WakaTime JSON data containing mock projects, languages, and editors.
   - Verify that badges and markup match expected output.
3. **Git Cleanliness:**
   - Verify git status and diff.

---

## 5. Review & Approval

Approved by user during interactive design brainstorming sessions.
