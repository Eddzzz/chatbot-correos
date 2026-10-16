import unittest

from evaluate import percentile


class PercentileTest(unittest.TestCase):
    def test_nearest_rank_reports_the_tail_for_small_samples(self):
        self.assertEqual(percentile([3, 1, 5, 2, 4], .95), 5)
        self.assertEqual(percentile([2], .95), 2)


if __name__ == '__main__':
    unittest.main()
