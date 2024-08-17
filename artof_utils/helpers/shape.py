import numpy as np
from pyproj import Transformer
from shapely.geometry import Point
import math
from artof_utils.helpers import array


# CRS
def transform_crs(input_crs: str, output_crs: str, coordinates):
    depth = array.get_depth(coordinates)

    if input_crs == output_crs:
        return coordinates

    # Recursively calculate the transformed matrices
    if depth > 1:
        return [transform_crs(input_crs, output_crs, coords) for coords in coordinates]
    else:
        # Create a transformer from the input CRS to the output CRS
        transformer = Transformer.from_crs(input_crs, output_crs)
        # Process single coordinate
        x, y = coordinates
        return list(transformer.transform(x, y))


# Shapes
def get_orientation(point1, point2, degrees=True) -> float:
    # Calculate the difference in x and y coordinates
    if isinstance(point1, Point) and isinstance(point2, Point):
        delta_x = point2.x - point1.x
        delta_y = point2.y - point1.y
    elif isinstance(point1, list) and isinstance(point2, list):
        delta_x = point2[0] - point1[0]
        delta_y = point2[1] - point1[1]
    else:
        return 0

    # Calculate the angle (in radians) between the line segment and the x-axis
    angle_rad = math.atan2(delta_y, delta_x)

    # Convert angle to degrees, and offset by 90 degrees for this application
    if degrees:
        angle_deg = math.degrees(angle_rad) - 90.0

        # Ensure the angle is within [0, 360] degrees
        if angle_deg < 0:
            angle_deg += 360

        return angle_deg
    else:
        return angle_rad
