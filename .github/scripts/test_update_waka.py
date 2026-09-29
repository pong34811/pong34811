import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from update_waka import fmt_time, progress_bar, generate_block, update_readme_text

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

    def test_update_readme_text(self):
        sample = "Header\n<!-- START_WAKA_TODAY -->\nOld content\n<!-- END_WAKA_TODAY -->\nFooter"
        new_block = "New content"
        res = update_readme_text(sample, new_block)
        expected = "Header\n<!-- START_WAKA_TODAY -->\nNew content\n<!-- END_WAKA_TODAY -->\nFooter"
        self.assertEqual(res, expected)

if __name__ == "__main__":
    unittest.main()
