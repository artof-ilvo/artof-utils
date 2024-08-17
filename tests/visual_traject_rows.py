from artof_utils.helpers import traject
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

file_name = "files/traject/complex.csv"

if __name__ == '__main__':
    # Example usage:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_name)
    df = df.apply(pd.to_numeric, errors='coerce')
    points = [Point(xy) for xy in zip(df['X'], df['Y'])]

    # Calculate orientation of points
    rows = traject.__extract_rows(points)

    # Plot result
    lw = 2
    colors = ['red', 'orange', 'green', 'blue']
    i = 0
    # Draw orientation vectors
    for row in rows:
        x_values = [traject_point.coordinate.x for traject_point in row]
        y_values = [traject_point.coordinate.y for traject_point in row]
        row_color = colors[i % len(colors)]
        plt.scatter(x_values, y_values, color=row_color, marker=".", label="row %d" % i)

        for traject_point in row:
            dx = np.cos(traject_point.orientation)
            dy = np.sin(traject_point.orientation)
            plt.arrow(traject_point.coordinate.x, traject_point.coordinate.y, dx, dy, head_width=0.2,
                      head_length=0.2, fc=row_color, ec=row_color)
        i += 1

    plt.legend(loc="lower left")
    plt.xlabel("Input")
    plt.ylabel("Response")
    plt.show()
