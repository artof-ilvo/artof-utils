from unittest import TestCase

from pydantic import ValidationError

from artof_utils.schemas.settings import HitchName, PlatformSettings


def settings_with_hitch(**hitch):
    return {
        'name': 'test',
        'robot': {'width': 1.66, 'length': 3.3, 'transform': {'T': [0, 1.2, -1.45], 'R': [0, 0, 0]}},
        'auto_max_accel': {'linear': 0.1, 'angular': 0.1},
        'auto_velocity': {'min': 0.2, 'max': 1.7},
        'nav_modes': [{'id': 3, 'name': 'pure pp'}],
        'auto_modes': [{'id': 1, 'name': 'auto'}],
        'hitches': [dict({'min': 10, 'max': 65, 'types': ['hitch'], 'link_length': 0.6,
                          'transform': {'T': [0, 0.33, -1.38], 'R': [0, 0, 0]}}, **hitch)],
        'gps': {'device': 'socket', 'transform': {'T': [-0.61, 0, 0], 'R': [0, 0, 0]}},
    }


class TestHitchSettings(TestCase):
    def test_new_hitch_names(self):
        for name in ('R', 'L', 'RF', 'FF', 'FB', 'RB'):
            settings = PlatformSettings.model_validate(settings_with_hitch(name=name))
            self.assertEqual(settings.hitches[0].name, HitchName(name))

    def test_unknown_hitch_name_is_refused(self):
        with self.assertRaises(ValidationError):
            PlatformSettings.model_validate(settings_with_hitch(name='X'))

    def test_hitch_without_id(self):
        settings = PlatformSettings.model_validate(settings_with_hitch(name='R'))
        self.assertNotIn('id', settings.hitches[0].model_dump())

    def test_old_hitch_id_is_ignored(self):
        settings = PlatformSettings.model_validate(settings_with_hitch(name='FB', id=2))
        self.assertNotIn('id', settings.hitches[0].model_dump())
