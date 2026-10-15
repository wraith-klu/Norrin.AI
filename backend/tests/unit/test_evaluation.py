import unittest

from sports_predictor.evaluation import evaluate_predictions


class EvaluationTests(unittest.TestCase):
    def test_metrics_include_r2(self):
        metrics = evaluate_predictions([1, 2, 3], [1, 2, 3])
        self.assertEqual(metrics["r2"], 1.0)
