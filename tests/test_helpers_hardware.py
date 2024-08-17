from unittest import TestCase
from artof_utils.helpers.hardware import parse_gps_fix_number


class TestHelpersHardware(TestCase):
    def test_parse_gps_fix_number(self):
        self.assertEqual(parse_gps_fix_number(0), 'Not valid')
        self.assertEqual(parse_gps_fix_number(1), 'GPS Fix')
        self.assertEqual(parse_gps_fix_number(2), 'Differential GPS')
        self.assertEqual(parse_gps_fix_number(3), 'Not applicable')
        self.assertEqual(parse_gps_fix_number(4), 'RTK Fix')
        self.assertEqual(parse_gps_fix_number(5), 'RTK Float')
        self.assertEqual(parse_gps_fix_number(6), 'Not valid')
        self.assertEqual(parse_gps_fix_number(-1), 'Not valid')
        self.assertEqual(parse_gps_fix_number(None), 'Not valid')
        self.assertEqual(parse_gps_fix_number(''), 'Not valid')