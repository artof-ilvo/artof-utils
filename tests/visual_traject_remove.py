from artof_utils.helpers import traject
from tests.visual_support import plot_side_by_side
import pandas as pd


file_name = "files/traject/complex.csv"
row_number = [2, 3]  # 1, 2, [0, 1], [0, 2]

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_name)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Calculate orientation of points
    path = [[xy[0], xy[1]] for xy in zip(df['X'], df['Y'])]
    path_shifted = traject.perform(traject.Operation.REMOVE, path, row_number=row_number)

    plot_side_by_side({"original": path, "remove": path_shifted})
