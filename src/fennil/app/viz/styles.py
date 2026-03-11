import numpy as np

VELOCITY_SCALE = 1000
VECTOR_ARROW_SIZE_FACTOR = 6
VECTOR_ARROW_MIN_PIXELS = 8
VECTOR_ARROW_MAX_PIXELS = 28

RES_COMPARE_SIZE_SCALE = VELOCITY_SCALE / 400.0
RES_COMPARE_DIFF_MIN = -5.0
RES_COMPARE_DIFF_MAX = 5.0
RES_COMPARE_UNIQUE_SIZE_PIXELS = 15.0
RES_COMPARE_UNIQUE_COLOR = [0, 0, 0, 220]

FAULT_PROJ_LINE_WIDTH = 1
SLIP_WIDTH_SCALE = 0.05
SLIP_WIDTH_MIN_PIXELS = 1
SLIP_WIDTH_CAP_MM_PER_YR = 400.0
SLIP_NEGATIVE_COLOR = [31, 119, 180, 220]  # tab:blue
SLIP_POSITIVE_COLOR = [255, 127, 14, 220]  # tab:orange
SLIP_NEGATIVE_EXTREME_COLOR = [25, 230, 255, 220]  # bright blue
SLIP_POSITIVE_EXTREME_COLOR = [255, 40, 40, 220]  # bright red

SLIP_COMPARE_MATCH_TOL_DEG = 1.0e-4
SLIP_COMPARE_WIDTH_SCALE = SLIP_WIDTH_SCALE * 128
SLIP_COMPARE_WIDTH_MIN_PIXELS = 1
SLIP_COMPARE_FASTER_COLOR = [44, 160, 44, 220]  # green
SLIP_COMPARE_SLOWER_COLOR = [214, 39, 40, 220]  # red
SLIP_COMPARE_NEUTRAL_COLOR = [140, 140, 140, 220]


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
RED = [255, 0, 0, 255]
BLACK = [0, 0, 0, 255]

SLIP_RATE_MIN = -100.0
SLIP_RATE_MAX = 100.0
COUPLING_MIN = -1.0
COUPLING_MAX = 1.0


def map_discrete_colors(values, value_min, value_max, palette):
    colors_array = []
    span = value_max - value_min
    if span <= 0:
        span = 1.0
    for raw_value in values:
        value = raw_value
        if not np.isfinite(value):
            value = 0.0
        value = float(np.clip(value, value_min, value_max))
        position = (value - value_min) / span
        index = int(np.floor(position * len(palette)))
        index = max(0, min(len(palette) - 1, index))
        r, g, b = palette[index]
        colors_array.append([r, g, b, 255])
    return colors_array


def map_slip_colors(values):
    return map_discrete_colors(values, SLIP_RATE_MIN, SLIP_RATE_MAX, RDBU_11)


def map_coupling_colors(values):
    return map_discrete_colors(values, COUPLING_MIN, COUPLING_MAX, RDBU_11)
