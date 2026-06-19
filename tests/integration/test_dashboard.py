import unittest
from pathlib import Path


class DashboardTests(unittest.TestCase):
    def test_dashboard_app_exists(self):
        self.assertTrue(Path("dashboard/app.py").exists())
