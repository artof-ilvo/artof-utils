from artof_utils.helpers import traject
from tests.visual_support import plot_side_by_side
import pandas as pd

file_name = "files/traject/simple.csv"

if __name__ == '__main__':
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_name)
    df = df.apply(pd.to_numeric, errors='coerce')

    # Calculate orientation of points
    path = [[xy[0], xy[1]] for xy in zip(df['X'], df['Y'])]
    path_reverse = traject.perform(traject.Operation.REVERSE, path)
    path_flip = traject.perform(traject.Operation.FLIP, path)

    plot_side_by_side({"Original": path, "Reversed": path_reverse, "Flipped": path_flip})
