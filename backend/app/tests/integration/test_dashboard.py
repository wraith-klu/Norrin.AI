import unittest
from pathlib import Path


class DashboardTests(unittest.TestCase):
    def test_dashboard_app_exists(self):
        # React frontend exists instead of the deprecated streamlit dashboard
        self.assertTrue(Path("../frontend/src/App.jsx").exists())

