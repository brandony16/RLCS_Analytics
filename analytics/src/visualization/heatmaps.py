from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from typing import List
import numpy as np
from scipy.ndimage import gaussian_filter
from src.visualization.overlays import draw_rl_pitch, playable_area_mask
from constants import (
    FIELD_X,
    FIELD_Y,
    GOAL_DEPTH,
)

def show_player_position_heatmaps(player_names: List[str], df: DataFrame):
    if not player_names:
        return

    fig, axes = plt.subplots(
        1,
        len(player_names),
        figsize=(6 * len(player_names), 7),
        squeeze=False,
        facecolor="#111111",
    )
    axes = axes[0]

    x_range = [-FIELD_X - 200, FIELD_X + 200]
    y_range = [-FIELD_Y - GOAL_DEPTH - 200, FIELD_Y + GOAL_DEPTH + 200]

    for ax, player in zip(axes, player_names):
        player_df = df[df["player_name"] == player]

        heatmap, xedges, yedges = np.histogram2d(
            player_df["loc_x"],
            player_df["loc_y"],
            bins=75,
            range=[
                [-FIELD_X, FIELD_X],
                [-FIELD_Y - GOAL_DEPTH, FIELD_Y + GOAL_DEPTH],
            ],
        )

        heatmap = gaussian_filter(heatmap, sigma=1)
        heatmap = np.ma.masked_where(
            ~playable_area_mask(xedges, yedges), heatmap
        )

        ax.imshow(
            heatmap.T,
            origin="lower",
            extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
            aspect="equal",
            cmap="inferno",
            norm=PowerNorm(gamma=0.5, vmin=0, vmax=max(heatmap.max(), 1)),
            alpha=0.85,
            zorder=1,
        )

        # Draw overlay on top of heatmap
        draw_rl_pitch(ax, line_color="white", lw=1.2, alpha=0.9)

        # Tighten view limits around the pitch including goals
        ax.set_xlim(x_range)
        ax.set_ylim(y_range)
        ax.axis("off")
        ax.set_title(player, color="white", fontsize=14, pad=10)

    plt.tight_layout()
    plt.show()
