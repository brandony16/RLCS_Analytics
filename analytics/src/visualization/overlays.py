import numpy as np
from constants import (
    FIELD_X,
    FIELD_Y,
    CORNER_OFFSET,
    GOAL_WIDTH,
    GOAL_DEPTH,
    BIG_BOOST_COORDS,
    SMALL_PAD_COORDS,
)
import matplotlib.patches as patches
from matplotlib.path import Path


def draw_rl_pitch(ax, line_color="white", lw=1.5, alpha=0.7):
    """Draws Rocket League arena boundary, goals, and center markings."""
    # Main outer arena with corner chamfers
    pitch_contour = np.array(
        [
            [-FIELD_X + CORNER_OFFSET, -FIELD_Y],
            [FIELD_X - CORNER_OFFSET, -FIELD_Y],
            [FIELD_X, -FIELD_Y + CORNER_OFFSET],
            [FIELD_X, FIELD_Y - CORNER_OFFSET],
            [FIELD_X - CORNER_OFFSET, FIELD_Y],
            [-FIELD_X + CORNER_OFFSET, FIELD_Y],
            [-FIELD_X, FIELD_Y - CORNER_OFFSET],
            [-FIELD_X, -FIELD_Y + CORNER_OFFSET],
        ]
    )
    poly = patches.Polygon(
        pitch_contour,
        closed=True,
        fill=False,
        edgecolor=line_color,
        linewidth=lw,
        alpha=alpha,
    )
    ax.add_patch(poly)

    # Center line and center circle
    ax.axhline(
        0,
        xmin=0.15,
        xmax=0.85,
        color=line_color,
        linewidth=lw * 0.8,
        linestyle="--",
        alpha=alpha * 0.7,
    )
    center_circle = patches.Circle(
        (0, 0),
        radius=1000,
        fill=False,
        edgecolor=line_color,
        linewidth=lw * 0.8,
        linestyle="--",
        alpha=alpha * 0.7,
    )
    ax.add_patch(center_circle)

    # Orange & Blue Goals
    blue_goal = patches.Rectangle(
        (-GOAL_WIDTH, -FIELD_Y - GOAL_DEPTH),
        2 * GOAL_WIDTH,
        GOAL_DEPTH,
        fill=False,
        edgecolor=line_color,
        linewidth=lw,
        alpha=alpha,
    )
    orange_goal = patches.Rectangle(
        (-GOAL_WIDTH, FIELD_Y),
        2 * GOAL_WIDTH,
        GOAL_DEPTH,
        fill=False,
        edgecolor=line_color,
        linewidth=lw,
        alpha=alpha,
    )
    ax.add_patch(blue_goal)
    ax.add_patch(orange_goal)

    # Big Boost Pads
    for coord in BIG_BOOST_COORDS:
        pad = patches.Circle(
            (coord[0], coord[1]),
            radius=200,
            fill=False,
            edgecolor=line_color,
            linewidth=lw * 0.8,
            alpha=alpha * 0.7,
        )
        ax.add_patch(pad)

    # Small Boost Pads
    for coord in SMALL_PAD_COORDS:
        pad = patches.Circle(
            (coord[0], coord[1]),
            radius=100,
            fill=False,
            edgecolor=line_color,
            linewidth=lw * 0.8,
            alpha=alpha * 0.7,
        )
        ax.add_patch(pad)


def playable_area_mask(xedges, yedges):
    """Return a mask for the chamfered arena and its two goal rectangles."""
    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2
    x_grid, y_grid = np.meshgrid(x_centers, y_centers, indexing="ij")

    pitch_contour = np.array(
        [
            [-FIELD_X + CORNER_OFFSET, -FIELD_Y],
            [FIELD_X - CORNER_OFFSET, -FIELD_Y],
            [FIELD_X, -FIELD_Y + CORNER_OFFSET],
            [FIELD_X, FIELD_Y - CORNER_OFFSET],
            [FIELD_X - CORNER_OFFSET, FIELD_Y],
            [-FIELD_X + CORNER_OFFSET, FIELD_Y],
            [-FIELD_X, FIELD_Y - CORNER_OFFSET],
            [-FIELD_X, -FIELD_Y + CORNER_OFFSET],
        ]
    )

    points = np.column_stack((x_grid.ravel(), y_grid.ravel()))
    pitch_mask = Path(pitch_contour).contains_points(points).reshape(x_grid.shape)
    goal_mask = (np.abs(x_grid) <= GOAL_WIDTH) & (
        (y_grid >= FIELD_Y) | (y_grid <= -FIELD_Y)
    )
    return pitch_mask | goal_mask
