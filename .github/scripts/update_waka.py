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
        t_clean = urllib.parse.quote(t)
        color = "0078D7" if "Edge" in e["name"] else "6C63FF"
        ed_badges.append(
            f'<img src="https://img.shields.io/badge/Editor-{name_clean}%20{t_clean}-{color}?style=flat-square" />'
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
