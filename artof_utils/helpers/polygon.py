from enum import Enum
import numpy as np
from shapely.geometry import Polygon
from artof_utils.helpers import array


class Operation(Enum):
    BUFFER = 'buffer'

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


def create(transform: np.array, width: float = 0, height: float = 0, up: float = 0, down: float = 0):
    assert width != 0, 'Width must be positive'
    assert height != 0 or up != 0 or down != 0, 'Height must set or up and down must be set'

    if height != 0:
        up = height / 2
        down = - height / 2

    # Create polygon
    point_ll = [- (width / 2), down, 0, 1.0]
    point_lr = [+ (width / 2), down, 0, 1.0]
    point_ur = [+ (width / 2), up, 0, 1.0]
    point_ul = [- (width / 2), up, 0, 1.0]
    points = np.array([point_ll, point_lr, point_ur, point_ul, point_ll])

    co_xyzw = np.dot(points, transform.T)
    return [[p[0], p[1]] for p in co_xyzw]


# Operations
def perform(operation: Operation, data, **kwargs):
    if operation == Operation.BUFFER:
        return buffer(data, **kwargs)
    return data


def buffer(data: list, distance: float) -> list:
    depth = array.get_depth(data)

    if depth > 2:
        return [buffer(polygon, distance) for polygon in data]
    else:
        # Make sure we have a closed polygon
        if np.all(np.isclose(data[0], data[-1], atol=1e-4)):
            data[-1] = data[0]
        else:
            data.append(data[0])

        polygon = Polygon(data)
        polygon_buffered = polygon.buffer(distance, cap_style=3, join_style=2)

        return list(polygon_buffered.exterior.coords)
