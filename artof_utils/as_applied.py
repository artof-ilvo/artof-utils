"""
As-applied maps: what each implement section actually applied, and where.

A recording session is one GeoPackage per implement in
``<ILVO_PATH>/field/<field>/as_applied/<implement>_<YYYYmmdd-HHMMSS>.gpkg`` with a polygon layer ``rate``
(columns: implement, section, rate, time) in the field's projected CRS. Each feature is the area a section swept
between two consecutive footprints taken from the redis variable ``implement.states``.
"""
from datetime import datetime, timezone
from glob import glob
from os import path, makedirs
from typing import Optional

import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union

import artof_utils.paths as paths

LAYER = 'rate'
COLUMNS = ['implement', 'section', 'rate', 'time']
TIME_FORMAT = '%Y%m%d-%H%M%S'

# Redis variables (not part of config.json, so they are read and written through the helpers below)
REDIS_RECORD = 'pc.as_applied.record'
REDIS_FILES = 'pc.as_applied.files'


def as_applied_dir(field_name: str) -> str:
    return path.join(paths.fields, field_name, 'as_applied')


def session_file_name(implement: str, start: Optional[datetime] = None) -> str:
    start = start or datetime.now(timezone.utc)
    return '%s_%s.gpkg' % (implement, start.strftime(TIME_FORMAT))


def list_sessions(field_name: str) -> list[str]:
    """File names of the recorded sessions of a field, newest first."""
    files = glob(path.join(as_applied_dir(field_name), '*.gpkg'))
    return sorted((path.basename(f) for f in files), key=lambda f: f.rsplit('_', 1)[-1], reverse=True)


def session_path(field_name: str, file_name: str) -> str:
    """Absolute path of a session file; refuses names that would leave the field's as_applied folder."""
    if path.basename(file_name) != file_name or not file_name.endswith('.gpkg'):
        raise ValueError("Invalid as-applied file name '%s'" % file_name)
    return path.join(as_applied_dir(field_name), file_name)


def read_session(field_name: str, file_name: str) -> gpd.GeoDataFrame:
    return gpd.read_file(session_path(field_name, file_name), layer=LAYER)


def swept_polygon(previous_ring, current_ring) -> Polygon:
    """Area covered by a section moving from one footprint to the next."""
    return unary_union([Polygon(previous_ring), Polygon(current_ring)]).convex_hull


def is_recording(redis_server) -> bool:
    value = redis_server.r.get(REDIS_RECORD)
    return value is not None and value.decode().lower() in ('1', 'true')


def set_recording(redis_server, active: bool) -> None:
    redis_server.set_value(REDIS_RECORD, bool(active))


class AsAppliedWriter:
    """Buffers swept section polygons of one implement and appends them to its session file."""

    def __init__(self, field_name: str, implement: str, crs, start: Optional[datetime] = None):
        self.field_name = field_name
        self.implement = implement
        self.crs = crs
        self.file_name = session_file_name(implement, start)
        self.file_path = session_path(field_name, self.file_name)
        self.buffer: list[dict] = []
        self.created = False

    def add(self, section_id: str, previous_ring, current_ring, rate: float, time: Optional[datetime] = None):
        self.buffer.append({'implement': self.implement,
                            'section': section_id,
                            'rate': float(rate),
                            'time': (time or datetime.now(timezone.utc)).isoformat(timespec='milliseconds'),
                            'geometry': swept_polygon(previous_ring, current_ring)})

    def flush(self) -> int:
        """Write the buffered features; returns how many were written."""
        if not self.buffer:
            return 0
        gdf = gpd.GeoDataFrame(self.buffer, columns=COLUMNS + ['geometry'], geometry='geometry', crs=self.crs)
        makedirs(path.dirname(self.file_path), exist_ok=True)
        gdf.to_file(self.file_path, layer=LAYER, driver='GPKG', mode='a' if self.created else 'w')
        self.created = True
        written = len(self.buffer)
        self.buffer = []
        return written


class AsAppliedRecorder:
    """
    Turns successive ``implement.states`` snapshots into as-applied features.

    Feed it with ``update(states)`` at a steady rate (the addon polls redis); a section footprint is only written
    once it moved more than ``min_distance`` meters, so standing still does not stack polygons.
    """

    def __init__(self, field_name: str, crs, min_distance: float = 0.1):
        self.field_name = field_name
        self.crs = crs
        self.min_distance = min_distance
        self.start = datetime.now(timezone.utc)
        self.writers: dict[str, AsAppliedWriter] = {}
        self.previous: dict[tuple[str, str], list] = {}

    def update(self, states: Optional[dict], time: Optional[datetime] = None) -> None:
        for implement_name, implement in (states or {}).items():
            for section in implement.get('sections', []):
                ring = section.get('xy')
                if not ring or len(ring) < 3:
                    continue
                key = (implement_name, section.get('id', ''))
                previous_ring = self.previous.get(key)
                if previous_ring is None:
                    self.previous[key] = ring
                    continue
                if Polygon(ring).centroid.distance(Polygon(previous_ring).centroid) < self.min_distance:
                    continue
                self.writer(implement_name).add(key[1], previous_ring, ring, section.get('rate', 0), time)
                self.previous[key] = ring

    def writer(self, implement_name: str) -> AsAppliedWriter:
        if implement_name not in self.writers:
            self.writers[implement_name] = AsAppliedWriter(self.field_name, implement_name, self.crs, self.start)
        return self.writers[implement_name]

    def flush(self) -> int:
        return sum(writer.flush() for writer in self.writers.values())

    @property
    def files(self) -> list[str]:
        return [writer.file_name for writer in self.writers.values() if writer.created]
