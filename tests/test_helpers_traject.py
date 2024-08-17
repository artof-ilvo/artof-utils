from unittest import TestCase
import numpy as np
import pandas as pd
from shapely.geometry import Point
from artof_utils.helpers import traject


class TestHelpersTraject(TestCase):
    def test_reverse_point_array_list_1(self):
        points = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]]
        reversed_points = traject.reverse(points)
        self.assertEqual(reversed_points, [[9, 9], [8, 8], [7, 7], [6, 6], [5, 5], [4, 4], [3, 3], [2, 2], [1, 1], [0, 0]])

    def test_reverse_points_np_1(self):
        points = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]])
        reversed_points = traject.reverse(points)
        self.assertTrue(np.array_equal(reversed_points, [[9, 9], [8, 8], [7, 7], [6, 6], [5, 5], [4, 4], [3, 3], [2, 2], [1, 1], [0, 0]]))

    def test_reverse_points_list_2(self):
        points = [[[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]], [[0, 0], [1, 1], [2, 2], [3, 3]]]
        reversed_points = traject.reverse(points)
        self.assertEqual(reversed_points, [[[9, 9], [8, 8], [7, 7], [6, 6], [5, 5], [4, 4], [3, 3], [2, 2], [1, 1], [0, 0]], [[3, 3], [2, 2], [1, 1], [0, 0]]])

    def test_reverse_points_np_2(self):
        points = np.array([[[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9]]])
        reversed_points = traject.reverse(points)
        self.assertTrue(np.array_equal(reversed_points, [[[9, 9], [8, 8], [7, 7], [6, 6], [5, 5], [4, 4], [3, 3], [2, 2], [1, 1], [0, 0]]]))

    def test_traject_extract(self):
        file_name = "tests/files/traject/complex.csv"
        df = pd.read_csv(file_name)
        df = df.apply(pd.to_numeric, errors='coerce')
        points = [Point(xy) for xy in zip(df['X'], df['Y'])]
        rows = traject.get_rows(points)

        self.assertEqual(len(rows), 4, "Expected 4 rows, got %d" % len(rows))