import numpy as np

VELOCITY_SCALE = 1000
RED = [255, 0, 0, 255]
BLACK = [0, 0, 0, 255]
SEGMENT_LINE_WIDTH = 3
FAULT_PROJ_LINE_WIDTH = 1

# Per-layer colors (RGBA) and per-folder line widths, mirroring the legacy viewer
TYPE_COLORS = {
    1: {
        "obs": [0, 0, 205, 255],
        "mod": [205, 0, 0, 200],
        "res": [205, 0, 205, 200],
        "rot": [0, 205, 0, 200],
        "seg": [0, 205, 205, 200],
        "tde": [205, 133, 0, 200],
        "str": [0, 128, 128, 200],
        "mog": [128, 128, 128, 200],
        "loc": [0, 0, 0, 220],
    },
    2: {
        "obs": [0, 0, 205, 255],
        "mod": [205, 0, 0, 200],
        "res": [205, 0, 205, 200],
        "rot": [0, 205, 0, 200],
        "seg": [0, 205, 205, 200],
        "tde": [205, 133, 0, 200],
        "str": [0, 102, 102, 200],
        "mog": [102, 102, 102, 200],
        "loc": [0, 0, 0, 220],
    },
}

LINE_WIDTHS = {1: 1, 2: 2}

# ColorBrewer RdBu[11] palette for discrete slip-rate coloring
RDBU_11 = [
    (103, 0, 31),
    (178, 24, 43),
    (214, 96, 77),
    (244, 165, 130),
    (253, 219, 199),
    (247, 247, 247),
    (209, 229, 240),
    (146, 197, 222),
    (67, 147, 195),
    (33, 102, 172),
    (5, 48, 97),
]

SLIP_RATE_MIN = -100.0
SLIP_RATE_MAX = 100.0

FAULT_PROJ_STYLE = {
    1: {
        "fill": [173, 216, 230, 77],  # lightblue @ 0.3 alpha
        "line": [0, 0, 255, 255],  # blue
    },
    2: {
        "fill": [144, 238, 144, 77],  # lightgreen @ 0.3 alpha
        "line": [0, 128, 0, 255],  # green
    },
}

FAULT_LINE_STYLE = {
    1: {"color": [0, 0, 255, 255], "width": 1},
    2: {"color": [0, 128, 0, 255], "width": 3},
}


def map_slip_colors(values):
    """Map slip values to discrete RdBu[11] colors."""
    colors_array = []
    span = SLIP_RATE_MAX - SLIP_RATE_MIN
    for raw_value in values:
        value = raw_value
        if not np.isfinite(value):
            value = 0.0
        value = float(np.clip(value, SLIP_RATE_MIN, SLIP_RATE_MAX))
        position = (value - SLIP_RATE_MIN) / span
        index = int(np.floor(position * len(RDBU_11)))
        index = max(0, min(len(RDBU_11) - 1, index))
        r, g, b = RDBU_11[index]
        colors_array.append([r, g, b, 255])
    return colors_array
