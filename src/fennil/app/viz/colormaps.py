import math

import numpy as np

DEFAULT_COLORMAP_NAME = "RDBU_11"
DEFAULT_N_COLORS = 11
MIN_N_COLORS = 2
MAX_N_COLORS = 255


def _hex_to_rgb(value):
    text = str(value).strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        return 0, 0, 0
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


PALETTES = {
    "RDBU_11": [
        (5, 48, 97),
        (33, 102, 172),
        (67, 147, 195),
        (146, 197, 222),
        (209, 229, 240),
        (247, 247, 247),
        (253, 219, 199),
        (244, 165, 130),
        (214, 96, 77),
        (178, 24, 43),
        (103, 0, 31),
    ],
    "RDYLBLU_11": [
        _hex_to_rgb("#a50026"),
        _hex_to_rgb("#d73027"),
        _hex_to_rgb("#f46d43"),
        _hex_to_rgb("#fdae61"),
        _hex_to_rgb("#fee090"),
        _hex_to_rgb("#ffffbf"),
        _hex_to_rgb("#e0f3f8"),
        _hex_to_rgb("#abd9e9"),
        _hex_to_rgb("#74add1"),
        _hex_to_rgb("#4575b4"),
        _hex_to_rgb("#313695"),
    ],
    "SPECTRAL_11": [
        _hex_to_rgb("#9e0142"),
        _hex_to_rgb("#d53e4f"),
        _hex_to_rgb("#f46d43"),
        _hex_to_rgb("#fdae61"),
        _hex_to_rgb("#fee08b"),
        _hex_to_rgb("#ffffbf"),
        _hex_to_rgb("#e6f598"),
        _hex_to_rgb("#abdda4"),
        _hex_to_rgb("#66c2a5"),
        _hex_to_rgb("#3288bd"),
        _hex_to_rgb("#5e4fa2"),
    ],
    "VIRIDIS_11": [
        _hex_to_rgb("#440154"),
        _hex_to_rgb("#482475"),
        _hex_to_rgb("#414487"),
        _hex_to_rgb("#355f8d"),
        _hex_to_rgb("#2a788e"),
        _hex_to_rgb("#21918c"),
        _hex_to_rgb("#22a884"),
        _hex_to_rgb("#44bf70"),
        _hex_to_rgb("#7ad151"),
        _hex_to_rgb("#bddf26"),
        _hex_to_rgb("#fde725"),
    ],
    "PLASMA_11": [
        _hex_to_rgb("#0d0887"),
        _hex_to_rgb("#41049d"),
        _hex_to_rgb("#6a00a8"),
        _hex_to_rgb("#8f0da4"),
        _hex_to_rgb("#b12a90"),
        _hex_to_rgb("#cc4778"),
        _hex_to_rgb("#e16462"),
        _hex_to_rgb("#f2844b"),
        _hex_to_rgb("#fca636"),
        _hex_to_rgb("#fcce25"),
        _hex_to_rgb("#f0f921"),
    ],
    "CIVIDIS_11": [
        _hex_to_rgb("#00224e"),
        _hex_to_rgb("#123570"),
        _hex_to_rgb("#3b496c"),
        _hex_to_rgb("#575d6d"),
        _hex_to_rgb("#707173"),
        _hex_to_rgb("#8a8678"),
        _hex_to_rgb("#a59c74"),
        _hex_to_rgb("#c3b369"),
        _hex_to_rgb("#e1cc55"),
        _hex_to_rgb("#f4e65a"),
        _hex_to_rgb("#ffffe0"),
    ],
    "COOLWARM_11": [
        _hex_to_rgb("#3b4cc0"),
        _hex_to_rgb("#5977e3"),
        _hex_to_rgb("#7b9ff9"),
        _hex_to_rgb("#9ebeff"),
        _hex_to_rgb("#c0d4f5"),
        _hex_to_rgb("#dddcdc"),
        _hex_to_rgb("#f2cbb7"),
        _hex_to_rgb("#f7ac8e"),
        _hex_to_rgb("#ee8468"),
        _hex_to_rgb("#d65244"),
        _hex_to_rgb("#b40426"),
    ],
}


def palette_names():
    return sorted(PALETTES.keys(), key=str.lower)


def resolve_palette_name(value):
    name = str(value)
    if name in PALETTES:
        return name
    return DEFAULT_COLORMAP_NAME


def sanitize_n_colors(value, default=DEFAULT_N_COLORS):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return int(default)
    return max(MIN_N_COLORS, min(MAX_N_COLORS, value))


def _to_finite_float(value, fallback):
    try:
        parsed = float(value)
        if math.isfinite(parsed):
            return parsed
    except (TypeError, ValueError):
        pass
    return float(fallback)


def parse_colormap_range(
    color_map_range,
    *,
    default_min,
    default_max,
    default_palette=DEFAULT_COLORMAP_NAME,
    default_n_colors=DEFAULT_N_COLORS,
):
    payload = color_map_range if isinstance(color_map_range, dict) else {}
    return {
        "min": _to_finite_float(payload.get("min", default_min), default_min),
        "max": _to_finite_float(payload.get("max", default_max), default_max),
        "palette": resolve_palette_name(payload.get("palette", default_palette)),
        "n_colors": sanitize_n_colors(payload.get("n_colors", default_n_colors)),
        "invert": bool(payload.get("invert", False)),
        "use_log_scale": bool(payload.get("use_log_scale", False)),
    }


def _sample_palette_linear(palette, n_colors):
    if n_colors <= 1:
        return [palette[0]]
    if len(palette) == 1:
        return [palette[0]] * n_colors

    max_idx = len(palette) - 1
    sampled = []
    for idx in range(n_colors):
        position = (idx / (n_colors - 1)) * max_idx
        lo = math.floor(position)
        hi = min(max_idx, lo + 1)
        frac = position - lo
        r = round((1 - frac) * palette[lo][0] + frac * palette[hi][0])
        g = round((1 - frac) * palette[lo][1] + frac * palette[hi][1])
        b = round((1 - frac) * palette[lo][2] + frac * palette[hi][2])
        sampled.append((r, g, b))
    return sampled


def sample_palette(
    name,
    n_colors=DEFAULT_N_COLORS,
    invert=False,
):
    palette = PALETTES[resolve_palette_name(name)]
    if invert:
        palette = list(reversed(palette))

    n_colors = sanitize_n_colors(n_colors)
    return _sample_palette_linear(palette, n_colors)


def _log_offset(idx, count):
    if count <= 1:
        return 0.0
    linear = idx / (count - 1)
    return math.log10(1 + 9 * linear) * 100.0


def palette_gradient_css(
    name,
    *,
    n_colors=DEFAULT_N_COLORS,
    invert=False,
    use_log_scale=False,
):
    colors = sample_palette(
        name,
        n_colors=n_colors,
        invert=invert,
    )
    if len(colors) == 1:
        r, g, b = colors[0]
        return f"rgb({r}, {g}, {b})"

    stops = []
    count = len(colors)
    for idx, (r, g, b) in enumerate(colors):
        if use_log_scale:
            start = _log_offset(idx, count + 1)
            end = _log_offset(idx + 1, count + 1)
        else:
            start = (idx / count) * 100.0
            end = ((idx + 1) / count) * 100.0
        stops.append(f"rgb({r}, {g}, {b}) {start:.4f}%")
        stops.append(f"rgb({r}, {g}, {b}) {end:.4f}%")
    return f"linear-gradient(90deg, {', '.join(stops)})"


def palette_entries(*, n_colors=64):
    return [
        {
            "name": name,
            "gradient": palette_gradient_css(name, n_colors=n_colors),
        }
        for name in palette_names()
    ]


def map_discrete_colors(
    values,
    *,
    value_min,
    value_max,
    palette_name=DEFAULT_COLORMAP_NAME,
    n_colors=DEFAULT_N_COLORS,
    alpha=255,
    invert=False,
):
    colors_array = []
    palette = sample_palette(
        palette_name,
        n_colors=n_colors,
        invert=invert,
    )

    span = value_max - value_min
    if span <= 0:
        span = 1.0

    for raw_value in values:
        value = raw_value if np.isfinite(raw_value) else 0.0
        value = float(np.clip(value, value_min, value_max))
        position = (value - value_min) / span
        index = int(np.floor(position * len(palette)))
        index = max(0, min(len(palette) - 1, index))
        r, g, b = palette[index]
        colors_array.append([r, g, b, alpha])

    return colors_array
