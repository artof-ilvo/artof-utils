from artof_utils.helpers import polygon
from tests.visual_support import plot_on_top


distance = 0.1  # -2, 2, 3

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    multipolygon_shape = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], [[2, 2], [3, 2], [3, 3], [2, 3]]]

    # Calculate orientation of points
    multipolygon_buffer = polygon.buffer(multipolygon_shape, distance)

    plot_data = dict()
    for i, polygon_original in enumerate(multipolygon_shape):
        plot_data["original %d" % i] = polygon_original
    for i, polygon_buffer in enumerate(multipolygon_buffer):
        plot_data["buffer %d" % i] = polygon_buffer

    plot_on_top(plot_data)
