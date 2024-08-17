from artof_utils.helpers import array
from artof_utils.helpers import shape as shp
from shapely.geometry import Point
from copy import deepcopy
from typing import Union
import numpy as np
from enum import Enum


# Helper Classes
class TrajectPoint:
    coordinate: Point
    orientation: float

    def __init__(self, coordinate: Union[Point, list, np.ndarray], orientation: float):
        self.coordinate = coordinate
        self.orientation = orientation

    @property
    def coordinate_as_list(self):
        if isinstance(self.coordinate, Point):
            return [self.coordinate.x, self.coordinate.y]
        else:
            return self.coordinate

    def move_parallel(self, distance: float):
        dx = distance * np.cos(self.orientation)
        dy = distance * np.sin(self.orientation)
        if isinstance(self.coordinate, Point):
            self.coordinate = Point(self.coordinate.x + dx, self.coordinate.y + dy)
        elif isinstance(self.coordinate, np.ndarray) or isinstance(self.coordinate, list):
            self.coordinate = [self.coordinate[0] + dx, self.coordinate[1] + dy]

    def move_perpendicular(self, distance: float):
        perpendicular_orientation = self.orientation + np.pi / 2
        dx = distance * np.cos(perpendicular_orientation)
        dy = distance * np.sin(perpendicular_orientation)
        if isinstance(self.coordinate, Point):
            self.coordinate = Point(self.coordinate.x + dx, self.coordinate.y + dy)
        elif isinstance(self.coordinate, np.ndarray) or isinstance(self.coordinate, list):
            self.coordinate = [self.coordinate[0] + dx, self.coordinate[1] + dy]


class Operation(Enum):
    REVERSE = 'reverse'
    FLIP = 'flip'
    EXTEND = 'extend'
    SHIFT = 'shift'
    SHIFT_ALTERNATE = 'shift_alternate'
    ADD = 'add'
    REMOVE = 'remove'

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


# Helper Functions

def __parse_data(data):
    depth = array.get_depth(data)
    if depth == 3:
        return data[0]
    elif depth == 2:
        return data
    else:
        raise ValueError("Data must be 2D or 3D")


def __extend_row(row, side: str, length: float):
    if side == 'begin':
        first_point: TrajectPoint = row[0]
        first_point.move_parallel(-length)
    elif side == 'end':
        last_point: TrajectPoint = row[-1]
        last_point.move_parallel(length)
    elif side == 'both':
        __extend_row(row, 'begin', length)
        __extend_row(row, 'end', length)


def __shift_row(row, distance: float):
    for traject_point in row:
        traject_point.move_perpendicular(distance)


def __extract_rows(points: list[Point], threshold_degrees=45):
    threshold_radians = threshold_degrees * np.pi / 180
    rows: list[list[TrajectPoint]] = [[]]

    for i, point in enumerate(points):
        last_row = rows[-1]

        if i < len(points) - 1:
            orientation = shp.get_orientation(point, points[i + 1], degrees=False)
            d_orientation = orientation - (last_row[-1].orientation if len(last_row) > 0 else orientation)

            if abs(d_orientation) > threshold_radians:
                p_orientation = last_row[-1].orientation
                last_row.append(TrajectPoint(point, p_orientation))
                # Append new row
                rows.append([])
            else:
                last_row.append(TrajectPoint(point, orientation))
        else:
            # Last point
            if len(last_row) > 0:
                p_orientation = last_row[-1].orientation
                rows[-1].append(TrajectPoint(point, p_orientation))

    return rows


def get_rows(data):
    rows = __extract_rows(__parse_data(data))
    rows = [[traject_point.coordinate_as_list for traject_point in row] for row in rows]
    return rows


# Operations
def perform(operation: Operation, data, **kwargs):
    if operation == Operation.REVERSE:
        return reverse(data)
    elif operation == Operation.FLIP:
        return flip(data)
    elif operation == Operation.EXTEND:
        return extend(data, **kwargs)
    elif operation == Operation.SHIFT:
        return shift(data, **kwargs)
    elif operation == Operation.SHIFT_ALTERNATE:
        return shift_alternate(data, **kwargs)
    elif operation == Operation.ADD:
        return add(data, **kwargs)
    elif operation == Operation.REMOVE:
        return remove(data, **kwargs)
    return data


def merge_rows(rows):
    merged_rows = []
    for row in rows:
        merged_rows += [traject_point.coordinate_as_list for traject_point in row]
    return merged_rows


def reverse(data):
    depth = array.get_depth(data)
    traject_data = deepcopy(data)

    if depth == 2:
        if isinstance(traject_data, np.ndarray):
            traject_data = np.flip(traject_data)
        elif isinstance(traject_data, list):
            traject_data.reverse()
    if depth == 3:
        if isinstance(traject_data, np.ndarray):
            traject_data = [np.flip(points) for points in traject_data]
        elif isinstance(traject_data, list):
            [points.reverse() for points in traject_data]

    return traject_data


def flip(data):
    rows = __extract_rows(__parse_data(data))
    rows_reversed = reverse(rows)
    traject_data = merge_rows(rows_reversed)

    return traject_data


def extend(data, side: str, length: float, row_number: Union[int, list[int]] = -1):
    rows = __extract_rows(__parse_data(data))
    row_numbers = __filter_row_numbers(rows, row_number)

    if side == 'begin':
        side_order = ['begin', 'end']
        for i in row_numbers:
            __extend_row(rows[i], side_order[i % 2], length)
    elif side == 'end':
        side_order = ['end', 'begin']
        for i in row_numbers:
            __extend_row(rows[i], side_order[i % 2], length)
    elif side == 'both':
        for i in row_numbers:
            __extend_row(rows[i], 'both', length)

    traject_data = merge_rows(rows)

    return traject_data


def __filter_row_numbers(rows, row_number: Union[int, list[int]] = -1):
    row_numbers = []
    if isinstance(row_number, int):
        row_numbers = range(len(rows)) if row_number < 0 else [row_number]
    if isinstance(row_number, list):
        row_numbers = row_number

    # Filter out rows that do not exist
    return [num for num in row_numbers if 0 <= num < len(rows)]


def shift_alternate(data, distance: float, row_number: Union[int, list[int]] = -1):
    rows = __extract_rows(__parse_data(data))
    row_numbers = __filter_row_numbers(rows, row_number)

    for i in row_numbers:
        __shift_row(rows[i], distance)

    traject_data = merge_rows(rows)

    return traject_data


def shift(data, distance: float, row_number: Union[int, list[int]] = -1):
    rows = __extract_rows(__parse_data(data))
    row_numbers = __filter_row_numbers(rows, row_number)

    for i in row_numbers:
        __shift_row(rows[i], distance * (-1 if i % 2 == 0 else 1))

    traject_data = merge_rows(rows)

    return traject_data


def add(data, distance: float, side: str = 'begin', number: int = 1):
    rows = __extract_rows(__parse_data(data))

    index = 0 if side == 'begin' else -1
    for i in range(number):
        if side == 'begin':
            rows = [reverse(deepcopy(rows[index]))] + rows
        else:
            rows = rows + [reverse(deepcopy(rows[index]))]
        __shift_row(rows[index], distance)

    traject_data = merge_rows(rows)

    return traject_data


def remove(data, row_number: Union[int, list[int]] = None):
    rows = __extract_rows(__parse_data(data))
    row_numbers = __filter_row_numbers(rows, row_number)

    if len(row_numbers) == len(rows):
        return data

    for x, row_number in enumerate(row_numbers):
        # Remove row
        del rows[row_number]
        # Reverse all other rows
        for i in range(row_number, len(rows)):
            rows[i] = reverse(rows[i])
        # Substract 1 from the remaining row numbers
        for i in range(x + 1, len(row_numbers)):
            row_numbers[i] = row_numbers[i] - 1

    traject_data = merge_rows(rows)

    return traject_data
