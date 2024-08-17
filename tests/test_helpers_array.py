from unittest import TestCase
import numpy as np
from artof_utils.helpers.array import get_depth


class TestHelpersArray(TestCase):

    def test_get_depth_list_0(self):
        self.assertEqual(get_depth(4), 0)
        self.assertEqual(get_depth(None), 0)
        self.assertEqual(get_depth(False), 0)
        self.assertEqual(get_depth("string"), 0)

    def test_get_depth_list_empty(self):
        depth = get_depth([])
        self.assertEqual(depth, 1)

    def test_get_depth_list_1(self):
        depth = get_depth([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(depth, 1)

    def test_get_depth_np_1(self):
        depth = get_depth(np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))

        self.assertEqual(depth, 1)

    def test_get_depth_list_2(self):
        depth = get_depth([[0, 1], [0, 1], [0, 1]])

        self.assertEqual(depth, 2)

    def test_get_depth_np_2(self):
        depth = get_depth(np.array([[0, 1], [0, 1], [0, 1]]))

        self.assertEqual(depth, 2)

    def test_get_depth_list_2_special(self):
        depth = get_depth([[0, 1], 1, None, [0, 1]])

        self.assertEqual(depth, 2)

    def test_get_depth_list_3(self):
        depth = get_depth([[[0, 1], [0, 1], [0, 1]], [[0, 1], [0, 1], [0, 1]]])

        self.assertEqual(depth, 3)

    def test_get_depth_np_3(self):
        depth = get_depth(np.array([[[0, 1], [0, 1], [0, 1]], [[0, 1], [0, 1], [0, 1]]]))

        self.assertEqual(depth, 3)
