import os
import requests
import re

# ดึงข้อมูลจาก WakaTime API (cache=false เพื่อให้ได้ข้อมูลล่าสุด)
api_key = os.environ['WAKATIME_API_KEY']
response = requests.get(
    'https://wakatime.com/api/v1/users/current/status_bar/today',
    auth=(api_key, ''),
    params={'cache': 'false'}
)
data = response.json()['data']

# ดึงเวลาทั้งหมด
total_seconds = data['grand_total']['total_seconds']
hours = int(total_seconds // 3600)
minutes = int((total_seconds % 3600) // 60)
total_time = f"{hours}h_{minutes}m"

# ดึงข้อมูล languages
languages = data.get('languages', [])
language_lines = []
for lang in languages[:5]:
    name = lang['name']
    percent = lang['percent']
    lang_hours = int(lang.get('hours', 0))
    lang_minutes = int(lang.get('minutes', 0))
    time_str = f"{lang_hours}h {lang_minutes}m" if lang_hours > 0 else f"{lang_minutes}m"

    bar_length = 30
    filled = int(percent * bar_length / 100)
    empty = bar_length - filled
    bar = '█' * filled + '░' * empty

    language_lines.append(f"{name:<12} {bar}  {percent:>5.1f}%    {time_str}")

language_bar = '\n'.join(language_lines)

# ดึงข้อมูล editors
editors = data.get('editors', [])
editor_badges = []
for editor in editors[:3]:
    name = editor['name']
    editor_hours = int(editor.get('hours', 0))
    editor_minutes = int(editor.get('minutes', 0))
    time_str = f"{editor_hours}h_{editor_minutes}m" if editor_hours > 0 else f"{editor_minutes}m"
    editor_badges.append(f'  <img src="https://img.shields.io/badge/Editor-{name}_{time_str}-6C63FF?style=flat-square" />')

# ดึงข้อมูล projects
projects = data.get('projects', [])
project_badges = []
for project in projects[:3]:
    name = project['name']
    project_hours = int(project.get('hours', 0))
    project_minutes = int(project.get('minutes', 0))
    time_str = f"{project_hours}h_{project_minutes}m" if project_hours > 0 else f"{project_minutes}m"
    project_badges.append(f'  <img src="https://img.shields.io/badge/Project-{name}_{time_str}-3776AB?style=flat-square" />')

# อ่าน README.md
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

# สร้างส่วนใหม่สำหรับ "วันนี้"
new_section = f'''<!-- START_WAKA_TODAY -->
<p align="center">
  <img src="https://wakatime.com/badge/user/1e5abd91-095a-4b62-bded-8eea82c90849.svg" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Today-{total_time}-6C63FF?style=for-the-badge" />
</p>

```
{language_bar}
```

<p align="center">
{chr(10).join(editor_badges)}
{chr(10).join(project_badges)}
</p>
<!-- END_WAKA_TODAY -->'''

# แทนที่ส่วนเดิม
readme = re.sub(
    r'<!-- START_WAKA_TODAY -->.*?<!-- END_WAKA_TODAY -->',
    new_section,
    readme,
    flags=re.DOTALL
)

# เขียน README.md กลับ
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)

print(f"Updated WakaTime stats: {total_time}")
