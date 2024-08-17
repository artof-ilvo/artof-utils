from artof_utils.helpers import traject
from tests.visual_support import plot_side_by_side
import pandas as pd


file_name = "files/traject/complex.csv"
distance = 3  # -2, 2, 3
side = 'end'  # 'begin', 'end'

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_name)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Calculate orientation of points
    path = [[xy[0], xy[1]] for xy in zip(df['X'], df['Y'])]
    path_shifted = traject.perform(traject.Operation.ADD, path, distance=distance, side=side)

    plot_side_by_side({"original": path, "add %.2f" % distance: path_shifted})
