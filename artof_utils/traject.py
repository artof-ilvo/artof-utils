import numpy as np
import pandas as pd
from enum import Enum
from typing import Union, List, Any
from shapely.coords import CoordinateSequence
from shapely.geometry import LineString, Point
from artof_utils.shapefile import Shapefile
from shapely.affinity import translate


class SegmentType(str, Enum):
    SWATH1 = "swath1"
    SWATH2 = "swath2"
    HEADLAND1 = "headland1"
    HEADLAND2 = "headland2"
    NONE = "none"

class LineSegment:
    def __init__(self, coords: Union[CoordinateSequence, List[Any], np.ndarray[tuple[Any]]],
                 direction: SegmentType=SegmentType.NONE):
        self.line = LineString(coords)
        self.direction = direction

    def __repr__(self):
        return f"LineSegment(len={self.line.length:.2f}, {self.direction})"


def extend_linestring(line: LineString, start_extension: float = 0, end_extension: float = 0) -> LineString:
    """Extend a LineString by given distances at start and/or end."""
    if line.is_empty or len(line.coords) < 2:
        return line  # Can't extend a degenerate line

    # Convert to numpy array for convenience
    coords = np.array(line.coords)

    # Start and end points
    p_start, p_end = coords[0], coords[-1]

    # Unit direction vectors
    dir_start = coords[0] - coords[1]
    dir_end = coords[-1] - coords[-2]
    dir_start = dir_start / np.linalg.norm(dir_start)
    dir_end = dir_end / np.linalg.norm(dir_end)

    # Extended points
    new_start = p_start + dir_start * start_extension
    new_end = p_end + dir_end * end_extension

    # Build new LineString
    new_coords = np.vstack([new_start, coords[1:-1], new_end]) if len(coords) > 2 else np.vstack([new_start, new_end])
    return LineString(new_coords)


def shift_linestring(line: LineString, distance: float) -> LineString:
    """Shift a LineString orthogonally (to the left if distance > 0)."""
    x1, y1 = line.coords[0]
    x2, y2 = line.coords[-1]

    # Direction vector
    dx, dy = x2 - x1, y2 - y1
    length = np.hypot(dx, dy)

    # Unit normal vector (orthogonal)
    nx, ny = -dy / length, dx / length

    # Apply orthogonal shift
    return translate(line, xoff=nx * distance, yoff=ny * distance)


def get_traject_props(gdf, tol=0.0):
    coords = np.array(gdf.get_coordinates())

    # Compute direction (angle) for each segment
    coords1 = coords.copy()
    coords2 = np.roll(coords, -1, axis=0)
 # coords1 was already sliced to remove wrap-around

    dx = coords2[:, 0] - coords1[:, 0]
    dy = coords2[:, 1] - coords1[:, 1]

    dx = dx[:-1]
    dy = dy[:-1]
    # Store last point
    last_point = coords1[-1]
    # drop the last pair because it wraps around
    coords1 = coords1[:-1]

    # Create DataFrame
    df = pd.DataFrame({
        'x': coords1[:,0],
        'y': coords1[:,1],
        'direction': np.arctan2(dy, dx),
        'length': np.sqrt(dx**2 + dy**2),
        'segment_type': [str(SegmentType.NONE.value)] * len(coords1),
        'color': ['orange'] * len(coords1),
        'swath_id': np.zeros(len(coords1)),
        'headland_id': np.zeros(len(coords1)),
        'headland1_id': np.zeros(len(coords1)),
        'headland2_id': np.zeros(len(coords1))
    })

    # Compute dx, dy for the new segment (from the second-to-last point to the last)
    dx_last = last_point[0] - coords1[-1, 0]
    dy_last = last_point[1] - coords1[-1, 1]
    # Create a new row as a DataFrame
    last_row = pd.DataFrame({
        'x': [last_point[0]],
        'y': [last_point[1]],
        'direction': [np.arctan2(dy_last, dx_last)],
        'length': [0],
        'segment_type': [str(SegmentType.NONE.value)],
        'color': ['orange'],
        'swath_id': [0],
        'headland_id': [0],
        'headland1_id': [0],
        'headland2_id': [0]
    })

    # Append it to df
    df = pd.concat([df, last_row], ignore_index=True)

    # Get the top two directions, these dominant directions represent the directions of the swath
    top_n = 2  # There are two dominant directions as there are two swaths
    df_temp = df.copy()
    df_temp['direction'] = df_temp['direction'].round(5)  # Bound to a minimum
    df_avg_lengths = df_temp.groupby('direction', as_index=False)['length'].mean()
    dominant_directions = df_avg_lengths.nlargest(top_n, 'length')['direction'].to_numpy()
    df.loc[np.isclose(df['direction'], dominant_directions[0],
                      atol=tol) & (df['length'] > 1.0), 'segment_type'] = SegmentType.SWATH1.value
    df.loc[np.isclose(df['direction'], dominant_directions[1],
                      atol=tol) & (df['length'] > 1.0), 'segment_type'] = SegmentType.SWATH2.value
    df.loc[df['segment_type'] == SegmentType.SWATH1.value, 'color'] = 'red'
    df.loc[df['segment_type'] == SegmentType.SWATH2.value, 'color'] = 'blue'

    # Get a line through the headland
    headland1_line = LineString(df[df['segment_type'] == SegmentType.SWATH1.value][['x', 'y']].to_numpy())
    headland1_line = extend_linestring(headland1_line, start_extension=1, end_extension=1)
    headland2_line = LineString(df[df['segment_type'] == SegmentType.SWATH2.value][['x', 'y']].to_numpy())
    headland2_line = extend_linestring(headland2_line, start_extension=1, end_extension=1)

    # Calculate the distance of every point to the swath headland lines
    df['distance_to_headland1'] = df.apply(lambda row: headland1_line.distance(Point(row['x'], row['y'])), axis=1)
    df['distance_to_headland2'] = df.apply(lambda row: headland2_line.distance(Point(row['x'], row['y'])), axis=1)
    # Assign to HEADLAND1 when closest to headland1_line and to HEADLAND2 when closest to headland2_line
    df.loc[
        (df['distance_to_headland1'] < df['distance_to_headland2']) &
        (~df['segment_type'].isin([SegmentType.SWATH1.value, SegmentType.SWATH2.value])),
        'segment_type'
    ] = SegmentType.HEADLAND1.value
    df.loc[
        (df['distance_to_headland2'] < df['distance_to_headland1']) &
        (~df['segment_type'].isin([SegmentType.SWATH1.value, SegmentType.SWATH2.value])),
        'segment_type'
    ] = SegmentType.HEADLAND2.value

    df.loc[df['segment_type'] == SegmentType.HEADLAND1.value, 'color'] = 'orange'
    df.loc[df['segment_type'] == SegmentType.HEADLAND2.value, 'color'] = 'purple'

    # Numbers the different rows
    idx = 0
    swath_id = 1
    headland_id = 1
    headland1_id = 1
    headland2_id = 1
    segment_type = df.loc[0, 'segment_type']
    previous_segment_type = segment_type
    while idx < len(df):
        current_segment_type = df.loc[idx, 'segment_type']
        if current_segment_type != previous_segment_type:
            if previous_segment_type in [SegmentType.SWATH1.value, SegmentType.SWATH2.value]:
                # First time switching from swath to headland
                df.loc[idx, 'swath_id'] = swath_id # Assign old swath_id
                swath_id += 1  # Increment swath_id
            elif previous_segment_type in [SegmentType.HEADLAND1.value, SegmentType.HEADLAND2.value]:
                # First time switching from headland to swath
                df.loc[idx, 'headland_id'] = headland_id  # Assign old headland_id
                headland_id += 1  # Increment headland_id
                if previous_segment_type == SegmentType.HEADLAND1.value:
                    df.loc[idx, 'headland1_id'] = headland1_id
                    headland1_id += 1
                elif previous_segment_type == SegmentType.HEADLAND2.value:
                    df.loc[idx, 'headland2_id'] = headland2_id
                    headland2_id += 1

        if current_segment_type == SegmentType.HEADLAND1.value:
            # Set headland_id if you ar in a headland
            df.loc[idx, 'headland1_id'] = headland1_id
            df.loc[idx, 'headland_id'] = headland_id
        elif current_segment_type == SegmentType.HEADLAND2.value:
            # Set headland_id if you ar in a headland
            df.loc[idx, 'headland2_id'] = headland2_id
            df.loc[idx, 'headland_id'] = headland_id
        elif current_segment_type in [SegmentType.SWATH1.value, SegmentType.SWATH2.value]:
            # Set swath_id if you ar in a swath
            df.loc[idx, 'swath_id'] = swath_id

        previous_segment_type = df.loc[idx, 'segment_type']
        idx += 1

    return df


class Traject(Shapefile):
    def __init__(self, folder_path):
        super().__init__(folder_path)
        self.props = self.get_props()

    def get_props(self):
        return get_traject_props(self.gdf)

    def get_number_of_rows(self):
        filtered = self.props['segment_type'].loc[
            (self.props['segment_type'] != self.props['segment_type'].shift()) &
            self.props['segment_type'].isin(['headland1', 'headland2'])
            ]
        return len(filtered)

    def reverse(self):
        gdf = self.gdf_mods[-1].copy() if len(self.gdf_mods) > 0 else self.gdf.copy()
        gdf.geometry = gdf.geometry.reverse()
        self.gdf_mods.append(gdf)
        return gdf


    def extend(self, distance: float, headland_side: Union[int, list[int]] = -1, row_number: Union[int, list[int]] = -1):
        df = get_traject_props(self.gdf).copy()

        if isinstance(headland_side, int):
            headlands = ['headland%d' % headland_side]
        elif isinstance(headland_side, list):
            headlands = ['headland%d' % s for s in headland_side]
        else:
            raise ValueError("Side must be an int or a list of ints")

        if isinstance(row_number, int):
            row_number = [row_number]

        swath1 = df[df['segment_type'] == SegmentType.SWATH1.value]
        swath2 = df[df['segment_type'] == SegmentType.SWATH2.value]
        swath1_angle = np.mean(swath1['direction'])
        swath2_angle = np.mean(swath2['direction'])

        if SegmentType.HEADLAND1.value in headlands:
            df.loc[df['segment_type'].isin([SegmentType.HEADLAND1.value, SegmentType.SWATH1.value]) & df['headland1_id'].isin(row_number), 'x'] -= (distance * np.cos(swath1_angle))
            df.loc[df['segment_type'].isin([SegmentType.HEADLAND1.value, SegmentType.SWATH1.value]) & df['headland1_id'].isin(row_number), 'y'] -= (distance * np.sin(swath1_angle))
        if SegmentType.HEADLAND2.value in headlands:
            df.loc[df['segment_type'].isin([SegmentType.HEADLAND2.value, SegmentType.SWATH2.value]) & df['headland2_id'].isin(row_number), 'x'] -= (distance * np.cos(swath2_angle))
            df.loc[df['segment_type'].isin([SegmentType.HEADLAND2.value, SegmentType.SWATH2.value]) & df['headland2_id'].isin(row_number), 'y'] -= (distance * np.sin(swath2_angle))

        gdf = self.gdf_mods[-1].copy() if len(self.gdf_mods) > 0 else self.gdf.copy()
        gdf.geometry = gdf.geometry.apply(lambda geom: LineString(LineString(df[['x', 'y']].to_numpy())))
        self.gdf_mods.append(gdf)
        return gdf


    def shift_swath(self, df, swath_id):
        # Assert when line is not in linestring

        return LineString(df[df['swath_id'] == swath_id][['x', 'y']].to_numpy())