from artof_utils.helpers import traject
from tests.visual_support import plot_on_top
import pandas as pd


file_name = "files/traject/complex.csv"
row_number = -1  # -1, 0, 1, [0, 1], [0, 2]
distance = -3  # 0.1, -0.2, 0.2

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_name)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Calculate orientation of points
    path = [[xy[0], xy[1]] for xy in zip(df['X'], df['Y'])]
    path_shifted = traject.perform(traject.Operation.SHIFT, path, distance=distance, row_number=row_number)

    plot_on_top({"original": path, "Shift %.2f" % distance: path_shifted})
