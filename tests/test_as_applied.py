from unittest import TestCase
from unittest.mock import patch
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from os import path

import artof_utils.paths as paths
from artof_utils import as_applied

CRS = 'EPSG:32631'


def section_ring(x, y, width=1.0, length=0.1):
    return [[x, y], [x + width, y], [x + width, y + length], [x, y + length], [x, y]]


def states(y, rate=100):
    return {'flame-weeder': {'name': 'flame-weeder',
                             'sections': [{'id': 'CR', 'rate': rate, 'xy': section_ring(554300.0, 5647960.0 + y)}]}}


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

    def test_recorder_writes_and_appends(self):
        # Arrange
        start = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
        recorder = as_applied.AsAppliedRecorder('field', CRS)
        recorder.start = start
        # Act
        recorder.update(states(0.0))
        recorder.update(states(0.05))  # moved less than min_distance: skipped
        recorder.update(states(0.5, rate=80))
        written_first = recorder.flush()
        recorder.update(states(1.0, rate=0))
        written_second = recorder.flush()
        # Assert
        self.assertEqual((written_first, written_second), (1, 1))
        self.assertEqual(recorder.files, ['flame-weeder_20261008-120000.gpkg'])
        self.assertEqual(as_applied.list_sessions('field'), recorder.files)
        gdf = as_applied.read_session('field', recorder.files[0])
        self.assertEqual(gdf.crs.to_epsg(), 32631)
        self.assertEqual(gdf['rate'].tolist(), [80.0, 0.0])
        self.assertEqual(gdf['section'].tolist(), ['CR', 'CR'])
        self.assertAlmostEqual(gdf.geometry.iloc[0].area, 0.6)

    def test_flush_without_movement_creates_no_file(self):
        # Arrange
        recorder = as_applied.AsAppliedRecorder('field', CRS)
        # Act
        recorder.update(states(0.0))
        # Assert
        self.assertEqual(recorder.flush(), 0)
        self.assertEqual(recorder.files, [])
        self.assertFalse(path.exists(as_applied.as_applied_dir('field')))

    def test_session_path_rejects_traversal(self):
        with self.assertRaises(ValueError):
            as_applied.session_path('field', '../traject/traject.gpkg')
        with self.assertRaises(ValueError):
            as_applied.session_path('field', 'session.shp')
