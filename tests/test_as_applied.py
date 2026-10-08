from unittest import TestCase
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from os import path

import artof_utils.paths as paths
from artof_utils import as_applied

CRS = 'EPSG:32631'
START = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)


def section_ring(x, y, width=1.0, length=0.1):
    return [[x, y], [x + width, y], [x + width, y + length], [x, y + length], [x, y]]


def states(y, rate=100):
    return {'flame-weeder': {'name': 'flame-weeder',
                             'sections': [{'id': 'CR', 'rate': rate, 'xy': section_ring(554300.0, 5647960.0 + y)}]}}


def attributes(speed=0.5, on=True, mode='auto'):
    return {'plc.monitor.wheel_f.speed': speed, 'pc.hitch.active': on, 'pc.mode': mode, 'plc.monitor.state': 3}


class TestAsApplied(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.patch = patch.object(paths, 'fields', self.tmp.name)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_swept_polygon_covers_both_footprints(self):
        # Arrange
        previous, current = section_ring(0, 0), section_ring(0, 1)
        # Act
        swept = as_applied.swept_polygon(previous, current)
        # Assert
        self.assertAlmostEqual(swept.area, 1.1)

    def test_sections_are_written_and_appended(self):
        # Arrange
        recorder = as_applied.AsAppliedRecorder('field', CRS, start=START)
        # Act
        recorder.update(states(0.0))
        recorder.update(states(0.05))  # moved less than min_distance: skipped
        recorder.update(states(0.5, rate=80))
        written_first = recorder.flush()
        recorder.update(states(1.0, rate=0))
        written_second = recorder.flush()
        # Assert
        self.assertEqual((written_first, written_second), (1, 1))
        self.assertEqual(recorder.session, '20261008-120000')
        self.assertEqual(as_applied.list_sessions('field'), ['20261008-120000'])
        self.assertEqual(as_applied.session_layers('field', recorder.session), [as_applied.SECTIONS])
        gdf = as_applied.read_layer('field', recorder.session, as_applied.SECTIONS)
        self.assertEqual(gdf.crs.to_epsg(), 32631)
        self.assertEqual(gdf['rate'].tolist(), [80.0, 0.0])
        self.assertEqual(gdf['implement'].tolist(), ['flame-weeder', 'flame-weeder'])
        self.assertAlmostEqual(gdf.geometry.iloc[0].area, 0.6)
        skipped = as_applied.read_layer('field', recorder.session, as_applied.SECTIONS, skip=1)
        self.assertEqual(skipped['rate'].tolist(), [0.0])

    def test_points_are_logged_on_movement_or_period(self):
        # Arrange
        recorder = as_applied.AsAppliedRecorder('field', CRS, point_period=5.0, start=START)
        # Act
        logged = [recorder.log_point([554300.0, 5647960.0], attributes(), START),
                  recorder.log_point([554300.0, 5647960.05], attributes(), START + timedelta(seconds=1)),
                  recorder.log_point([554300.0, 5647960.5], attributes(speed=0.8), START + timedelta(seconds=2)),
                  recorder.log_point([554300.0, 5647960.5], attributes(on=False), START + timedelta(seconds=8))]
        recorder.flush()
        recorder.log_point([554301.0, 5647960.5], attributes(speed=1.0, mode=''), START + timedelta(seconds=9))
        recorder.flush()
        # Assert
        self.assertEqual(logged, [True, False, True, True])
        self.assertEqual(recorder.layers, [as_applied.POINTS])
        gdf = as_applied.read_layer('field', recorder.session, as_applied.POINTS)
        self.assertEqual(len(gdf), 4)
        self.assertEqual(gdf['plc.monitor.wheel_f.speed'].tolist(), [0.5, 0.8, 0.5, 1.0])
        self.assertEqual(gdf['pc.hitch.active'].tolist(), [True, True, False, True])
        self.assertEqual(gdf['pc.mode'].tolist(), ['auto', 'auto', 'auto', ''])

    def test_layer_info_and_fids(self):
        # Arrange
        recorder = as_applied.AsAppliedRecorder('field', CRS, start=START)
        for i in range(3):
            recorder.log_point([554300.0 + i, 5647960.0], lambda: attributes(speed=i))
        recorder.flush()
        # Act
        info = as_applied.layer_info('field', recorder.session, as_applied.POINTS)
        second = as_applied.read_layer('field', recorder.session, as_applied.POINTS, fids=[2])
        # Assert
        self.assertEqual(info['count'], 3)
        self.assertEqual(info['columns']['plc.monitor.wheel_f.speed'], 'int64')
        self.assertEqual(info['columns']['pc.hitch.active'], 'bool')
        self.assertEqual(second.index.tolist(), [2])
        self.assertEqual(second['plc.monitor.wheel_f.speed'].tolist(), [1])

    def test_nothing_written_without_movement(self):
        # Arrange
        recorder = as_applied.AsAppliedRecorder('field', CRS)
        # Act
        recorder.update(states(0.0))
        # Assert
        self.assertEqual(recorder.flush(), 0)
        self.assertEqual(recorder.layers, [])
        self.assertEqual(as_applied.list_sessions('field'), [])
        self.assertFalse(path.exists(as_applied.as_applied_dir('field')))

    def test_invalid_session_or_layer_is_refused(self):
        with self.assertRaises(ValueError):
            as_applied.session_dir('field', '../traject')
        with self.assertRaises(ValueError):
            as_applied.layer_path('field', '20261008-120000', 'traject')


class FakeRedis:
    """Just enough of RedisServer for the record flag and the navigation state."""

    def __init__(self, **values):
        self.values = values
        self.r = self

    def get(self, name):
        value = self.values.get(name)
        return None if value is None else ('true' if value is True else 'false' if value is False else str(value)).encode()

    def get_value(self, name):
        return self.values.get(name, False)

    def set_value(self, name, value):
        self.values[name] = value


class TestAutoModeRecording(TestCase):
    def test_recording_follows_auto_mode(self):
        # Arrange
        redis = FakeRedis()
        rule = as_applied.AutoModeRecording(redis)
        rule.names = ['auto']
        # Act / Assert: manual toggle outside auto mode is kept
        redis.set_value(as_applied.REDIS_RECORD, True)
        self.assertFalse(rule.update())
        self.assertTrue(as_applied.is_recording(redis))
        redis.set_value(as_applied.REDIS_RECORD, False)
        rule.update()
        self.assertFalse(as_applied.is_recording(redis))
        # entering auto mode starts recording, and it is kept on
        redis.set_value('plc.monitor.state.auto', True)
        self.assertTrue(rule.update())
        self.assertTrue(as_applied.is_recording(redis))
        redis.set_value(as_applied.REDIS_RECORD, False)
        rule.update()
        self.assertTrue(as_applied.is_recording(redis))
        # leaving auto mode stops it once, then manual toggling works again
        redis.set_value('plc.monitor.state.auto', False)
        self.assertFalse(rule.update())
        self.assertFalse(as_applied.is_recording(redis))
        redis.set_value(as_applied.REDIS_RECORD, True)
        rule.update()
        self.assertTrue(as_applied.is_recording(redis))

    def test_simulation_auto_counts_as_auto_mode(self):
        redis = FakeRedis(**{'pc.simulation.active': True, 'pc.simulation.auto': True})
        self.assertTrue(as_applied.auto_mode_active(redis, ['auto']))
        redis.set_value('pc.simulation.active', False)
        self.assertFalse(as_applied.auto_mode_active(redis, ['auto']))
