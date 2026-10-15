import unittest

from sports_predictor.data_collection import clean_and_validate, generate_sample_data


class DataCleanerTests(unittest.TestCase):
    def test_cleaner_adds_outlier_flag(self):
        df = clean_and_validate(generate_sample_data(rows_per_sport=90, persist=False))
        self.assertIn("is_outlier", df.columns)
