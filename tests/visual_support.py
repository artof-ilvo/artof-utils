import matplotlib.pyplot as plt
import numpy as np


def plot_on_top(paths: dict):
    # Plot result
    lw = 1

    # Draw orientation vectors
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['red', 'orange', 'green', 'blue']
    for num, (label, coords) in enumerate(paths.items()):
        color = colors[num % len(colors)]
        np_path = np.array(coords)
        x_path = np_path[:, 0]
        y_path = np_path[:, 1]
        ax.scatter(x_path, y_path, color=color, marker=".", label=label)
        ax.plot(x_path, y_path, color=color, linestyle='dashed', linewidth=lw)
        for i, txt in enumerate(range(len(x_path))):
            ax.annotate("%d" % i, (float(x_path[i]), float(y_path[i])),
                        textcoords="offset points", xytext=(0, 10), ha='center')

        ax.legend(loc="lower left")

    plt.show()


def plot_side_by_side(paths: dict):
    # Plot result
    lw = 1

    # Draw orientation vectors
    fig, axs = plt.subplots(1, len(paths.keys()), figsize=(10, 5))

    num = 0
    for num, (title, coords) in enumerate(paths.items()):
        np_path = np.array(coords)
        x_path = np_path[:, 0]
        y_path = np_path[:, 1]
        axs[num].scatter(x_path, y_path, color='green', marker=".")
        axs[num].plot(x_path, y_path, color='green', linestyle='dashed', linewidth=lw)
        for i, txt in enumerate(range(len(x_path))):
            axs[num].annotate(txt, (float(x_path[i]), float(y_path[i])),
                              textcoords="offset points", xytext=(0, 10), ha='center')

        axs[num].set_title(title)

        num += 1

    plt.show()
