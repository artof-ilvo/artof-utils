import numpy as np
import matplotlib.pyplot as plt

VISUALS = True

def plot_traject_props(df, ax=None, swath_numbers=False, headland_numbers=False):
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    # Plot the trajectory line
    lw = 1
    ax.plot(df['x'], df['y'], color='green', linestyle='dashed', linewidth=lw)

    # Plot all segment directions as small vectors
    arrow_scale = 1.0
    # Origin points for arrows (first point of each segment)
    dx = arrow_scale * np.cos(df['direction'])
    dy = arrow_scale * np.sin(df['direction'])
    ax.quiver(df['x'], df['y'], dx, dy,
              angles='xy', scale_units='xy', scale=1,
              color=df['color'], width=0.005, alpha=0.8)

    # Plot the swath IDs
    if swath_numbers:
        df_filtered = df[df['swath_id'] != 0]
        df_swath_id = df_filtered.groupby('swath_id')[['x', 'y']].mean().reset_index()
        for _, row in df_swath_id.iterrows():
            ax.text(
                row['x'],
                row['y'],
                str(int(row['swath_id'])),  # convert swath_id to string
                fontsize=12,
                ha='center',
                va='center',
                color='red'
            )
    if headland_numbers:
        df_filtered = df[df['headland_id'] != 0]
        df_headland_id = df_filtered.groupby('headland_id')[['x', 'y']].mean().reset_index()
        for _, row in df_headland_id.iterrows():
            ax.text(
                row['x'],
                row['y'],
                str(int(row['headland_id'])),  # convert swath_id to string
                fontsize=12,
                ha='center',
                va='center',
                color='blue'
            )


    # Enforce equal axes
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    # ax.legend()
    ax.set_title("Trajectory Split by Curvature with Segment Directions")
    plt.tight_layout()

def plot_geofence(gdf, ax=None, color='green'):
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    lw = 1
    x, y = gdf.loc[0,'geometry'].exterior.xy
    ax.plot(x, y, color=color, linewidth=lw)

    # Enforce equal axes
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    # ax.legend()
    ax.set_title("Trajectory Split by Curvature with Segment Directions")
    plt.tight_layout()