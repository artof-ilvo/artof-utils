from artof_utils.helpers import polygon
from tests.visual_support import plot_on_top
import numpy as np


distance = -0.1  # -2, 2, 3

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    polygon_shape = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]

    # Calculate orientation of points
    commands = {'distance': distance}
    polygon_buffer = polygon.perform(polygon.Operation('buffer'), polygon_shape, **commands)

    plot_on_top({"original": polygon_shape, "buffer": polygon_buffer})
