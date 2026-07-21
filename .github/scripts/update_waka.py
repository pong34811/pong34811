import os
import requests
import re
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
    bar = "█" * filled + "░" * (width - filled)
    return bar

def fetch(endpoint):
    r = requests.get(f"{BASE}{endpoint}", auth=(API_KEY, ""), timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    today = fetch("/users/current/summaries?range=today")
    td = today["data"][0]
    gt = td["grand_total"]
    today_total = gt["text"]
    today_secs = gt["total_seconds"]

    langs = td["languages"]
    langs.sort(key=lambda x: x["total_seconds"], reverse=True)

    editors = td["editors"]
    editors.sort(key=lambda x: x["total_seconds"], reverse=True)

    lang_lines = []
    for l in langs[:4]:
        pct = round(l["percent"])
        bar = progress_bar(pct)
        t = fmt_time(l["total_seconds"])
        name = l["name"]
        if len(name) > 10:
            name = name[:10]
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

    today_badge = f'https://img.shields.io/badge/Today-{urllib.parse.quote(today_total)}-6C63FF?style=for-the-badge'

    new_block = f"""<p align="center">
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
</p>"""

    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    start = "<!-- START_WAKA_TODAY -->"
    end = "<!-- END_WAKA_TODAY -->"

    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)

    if pattern.search(content):
        replacement = f"{start}\n{new_block}\n{end}"
        content = pattern.sub(replacement, content)
    else:
        content = content.replace(
            "<!-- END_WAKA_TODAY -->",
            f"{new_block}\n<!-- END_WAKA_TODAY -->",
        )

    with open(README, "w", encoding="utf-8") as f:
        f.write(content)

    print("README updated successfully")

if __name__ == "__main__":
    main()
