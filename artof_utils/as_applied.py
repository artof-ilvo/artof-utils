"""
As-applied maps: what the robot and its implement sections did, and where.

Each recording session is a folder ``<ILVO_PATH>/field/<field>/as_applied/<YYYYmmdd-HHMMSS>/`` (start time, UTC) with
two GeoPackages in the field's projected CRS:

- ``sections.gpkg`` (layer ``sections``): polygons swept by every implement section between two consecutive footprints
  of the redis variable ``implement.states``; columns implement, section, rate, time.
- ``points.gpkg`` (layer ``points``): the robot reference point (``robot.ref.state``) with all redis variables at that
  moment as columns, plus time, lat, lon and ref.yaw.
"""
import re
from datetime import datetime, timezone
from os import path, makedirs, listdir
from typing import Callable, Optional, Union

import geopandas as gpd
import pandas as pd
import pyogrio
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import artof_utils.paths as paths
from artof_utils.schemas.settings import load_settings

SECTIONS = 'sections'
POINTS = 'points'
LAYERS = (SECTIONS, POINTS)
SESSION_FORMAT = '%Y%m%d-%H%M%S'
SESSION_PATTERN = re.compile(r'^\d{8}-\d{6}$')

# Redis variables (not part of config.json, so they are read and written through the helpers below)
REDIS_RECORD = 'pc.as_applied.record'
REDIS_SESSION = 'pc.as_applied.session'
REDIS_HEARTBEAT = 'pc.as_applied.heartbeat'  # unix time, refreshed by the recording process while it runs


def as_applied_dir(field_name: str) -> str:
    return path.join(paths.fields, field_name, 'as_applied')


def session_id(start: Optional[datetime] = None) -> str:
    return (start or datetime.now(timezone.utc)).strftime(SESSION_FORMAT)


def session_start(session: str) -> datetime:
    return datetime.strptime(session, SESSION_FORMAT).replace(tzinfo=timezone.utc)


def session_dir(field_name: str, session: str) -> str:
    """Folder of a session; refuses anything that is not a session id (so no path can leave the field)."""
    if not SESSION_PATTERN.match(session or ''):
        raise ValueError("Invalid as-applied session '%s'" % session)
    return path.join(as_applied_dir(field_name), session)


def layer_path(field_name: str, session: str, layer: str) -> str:
    if layer not in LAYERS:
        raise ValueError("Invalid as-applied layer '%s'" % layer)
    return path.join(session_dir(field_name, session), '%s.gpkg' % layer)


def session_layers(field_name: str, session: str) -> list[str]:
    return [layer for layer in LAYERS if path.exists(layer_path(field_name, session, layer))]


def list_sessions(field_name: str) -> list[str]:
    """Ids of the recorded sessions of a field that hold at least one layer, newest first."""
    folder = as_applied_dir(field_name)
    if not path.isdir(folder):
        return []
    sessions = [name for name in listdir(folder) if SESSION_PATTERN.match(name) and session_layers(field_name, name)]
    return sorted(sessions, reverse=True)


def read_layer(field_name: str, session: str, layer: str, columns: Optional[list[str]] = None, skip: int = 0,
               fids: Optional[list[int]] = None) -> gpd.GeoDataFrame:
    """
    Features of a session layer, indexed by their GeoPackage fid.
    :param columns: only read these attribute columns (None reads all)
    :param skip: leave out the first features (to only read what was appended since)
    :param fids: only read these features
    """
    kwargs = {'fids': fids} if fids is not None else {'skip_features': skip}
    return gpd.read_file(layer_path(field_name, session, layer), layer=layer, columns=columns, fid_as_index=True,
                         **kwargs)


def layer_info(field_name: str, session: str, layer: str) -> dict:
    """Attribute columns ({name: numpy dtype name}) and feature count of a session layer, without reading it."""
    info = pyogrio.read_info(layer_path(field_name, session, layer), layer=layer)
    return {'columns': dict(zip(info['fields'], (str(dtype) for dtype in info['dtypes']))),
            'count': int(info['features']),
            'crs': info['crs']}


def swept_polygon(previous_ring, current_ring) -> Polygon:
    """Area covered by a section moving from one footprint to the next."""
    return unary_union([Polygon(previous_ring), Polygon(current_ring)]).convex_hull


def is_recording(redis_server) -> bool:
    value = redis_server.r.get(REDIS_RECORD)
    return value is not None and value.decode().lower() in ('1', 'true')


def set_recording(redis_server, active: bool) -> None:
    redis_server.set_value(REDIS_RECORD, bool(active))


def auto_mode_names() -> list[str]:
    """Navigation states that count as auto mode (`auto_modes` of settings.json)."""
    try:
        names = [mode.name for mode in load_settings().auto_modes]
    except Exception:
        names = []
    return names or ['auto']


def auto_mode_active(redis_server, names: Optional[list[str]] = None) -> bool:
    """Whether the robot drives in an auto mode (in simulation: pc.simulation.auto, as RobotManager does)."""
    if redis_server.get_value('pc.simulation.active') and redis_server.get_value('pc.simulation.auto'):
        return True
    return any(redis_server.get_value('plc.monitor.state.%s' % name) for name in (names or auto_mode_names()))


class AutoModeRecording:
    """
    Recording follows auto mode: it is kept on while the robot is in auto mode and switched off once when the robot
    leaves auto mode. Outside auto mode the record flag is left alone, so it can be toggled by hand.
    """

    def __init__(self, redis_server):
        self.redis_server = redis_server
        self.names = auto_mode_names()
        self.was_auto = False

    def update(self) -> bool:
        """Apply the rule for the current navigation state; returns whether the robot is in auto mode."""
        auto = auto_mode_active(self.redis_server, self.names)
        if auto and not is_recording(self.redis_server):
            set_recording(self.redis_server, True)
        elif not auto and self.was_auto:
            set_recording(self.redis_server, False)
        self.was_auto = auto
        return auto


def beat(redis_server) -> None:
    """Tell the web pages that the recording process is alive."""
    redis_server.set_value(REDIS_HEARTBEAT, '%.3f' % datetime.now(timezone.utc).timestamp())


def recorder_alive(redis_server, max_age: float = 5.0) -> bool:
    """Whether the recording process sent a heartbeat in the last `max_age` seconds."""
    try:
        last = float(redis_server.r.get(REDIS_HEARTBEAT) or 0)
    except ValueError:
        return False
    return datetime.now(timezone.utc).timestamp() - last <= max_age


def now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(time: Optional[datetime]) -> str:
    return (time or now()).isoformat(timespec='milliseconds')


class LayerWriter:
    """Buffers features of one layer and appends them to its GeoPackage, keeping the column types of the first write."""

    def __init__(self, file_path: str, layer: str, crs):
        self.file_path = file_path
        self.layer = layer
        self.crs = crs
        self.buffer: list[dict] = []
        self.dtypes: Optional[pd.Series] = None

    @property
    def created(self) -> bool:
        return self.dtypes is not None

    def add(self, feature: dict):
        self.buffer.append(feature)

    def flush(self) -> int:
        """Write the buffered features; returns how many were written."""
        if not self.buffer:
            return 0
        gdf = gpd.GeoDataFrame(self.buffer, geometry='geometry', crs=self.crs)
        if self.created:
            # A GeoPackage layer has a fixed schema: same columns, same types as the first write
            gdf = gdf.reindex(columns=self.dtypes.index)
            gdf = gdf.astype({column: dtype for column, dtype in self.dtypes.items() if column != 'geometry'})
        makedirs(path.dirname(self.file_path), exist_ok=True)
        gdf.to_file(self.file_path, layer=self.layer, driver='GPKG', mode='a' if self.created else 'w')
        if not self.created:
            self.dtypes = gdf.dtypes
        written = len(self.buffer)
        self.buffer = []
        return written


class AsAppliedRecorder:
    """
    Turns successive redis snapshots into one as-applied session.

    Feed it at a steady rate (the task-map addon polls redis): ``update(states)`` with ``implement.states`` for the
    sections layer, ``log_point(xy, attributes)`` with the robot reference point and all redis variables for the
    points layer. A section or point is written once it moved more than ``min_distance`` meters; points are also logged
    every ``point_period`` seconds while standing still, so parameter changes are not lost.
    """

    def __init__(self, field_name: str, crs, min_distance: float = 0.1, point_period: float = 5.0,
                 start: Optional[datetime] = None):
        self.field_name = field_name
        self.crs = crs
        self.min_distance = min_distance
        self.point_period = point_period
        self.session = session_id(start)
        self.sections = LayerWriter(layer_path(field_name, self.session, SECTIONS), SECTIONS, crs)
        self.points = LayerWriter(layer_path(field_name, self.session, POINTS), POINTS, crs)
        self.previous_rings: dict[tuple[str, str], list] = {}
        self.last_point: Optional[tuple[Point, datetime]] = None

    def update(self, states: Optional[dict], time: Optional[datetime] = None) -> None:
        for implement_name, implement in (states or {}).items():
            for section in implement.get('sections', []):
                ring = section.get('xy')
                if not ring or len(ring) < 3:
                    continue
                key = (implement_name, section.get('id', ''))
                previous_ring = self.previous_rings.get(key)
                if previous_ring is None:
                    self.previous_rings[key] = ring
                    continue
                if Polygon(ring).centroid.distance(Polygon(previous_ring).centroid) < self.min_distance:
                    continue
                self.sections.add({'implement': implement_name,
                                   'section': key[1],
                                   'rate': float(section.get('rate', 0)),
                                   'time': timestamp(time),
                                   'geometry': swept_polygon(previous_ring, ring)})
                self.previous_rings[key] = ring

    def log_point(self, xy, attributes: Union[dict, Callable[[], dict]], time: Optional[datetime] = None) -> bool:
        """
        Log the robot position with its attributes; returns whether it was logged.
        :param attributes: dict, or a function returning it (only called when the point is logged)
        """
        if not xy or len(xy) < 2:
            return False
        time = time or now()
        point = Point(xy[0], xy[1])
        if self.last_point is not None:
            last_point, last_time = self.last_point
            moved = point.distance(last_point) >= self.min_distance
            waited = (time - last_time).total_seconds() >= self.point_period
            if not moved and not waited:
                return False
        if callable(attributes):
            attributes = attributes()
        self.points.add({'time': timestamp(time), **attributes, 'geometry': point})
        self.last_point = (point, time)
        return True

    def flush(self) -> int:
        return self.sections.flush() + self.points.flush()

    @property
    def layers(self) -> list[str]:
        return [writer.layer for writer in (self.sections, self.points) if writer.created]
