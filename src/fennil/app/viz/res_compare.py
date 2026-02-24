from urllib.parse import quote

import numpy as np
import pandas as pd

from fennil.app.deck.primitives import icon_layers

from .styles import (
    RDBU_11,
    RES_COMPARE_DIFF_MAX,
    RES_COMPARE_DIFF_MIN,
    RES_COMPARE_SIZE_SCALE,
    RES_COMPARE_UNIQUE_COLOR,
    RES_COMPARE_UNIQUE_SIZE_PIXELS,
)

CIRCLE_ICON = {
    "url": "data:image/svg+xml;utf8,"
    + quote(
        "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>"
        "<circle cx='32' cy='32' r='28' fill='black'/>"
        "</svg>"
    ),
    "width": 64,
    "height": 64,
    "anchorX": 32,
    "anchorY": 32,
    "mask": True,
}


def _map_residual_diff_colors(values):
    colors = []
    span = RES_COMPARE_DIFF_MAX - RES_COMPARE_DIFF_MIN
    for raw_value in values:
        value = raw_value if np.isfinite(raw_value) else 0.0
        value = float(np.clip(value, RES_COMPARE_DIFF_MIN, RES_COMPARE_DIFF_MAX))
        position = (value - RES_COMPARE_DIFF_MIN) / span
        color_index = int(np.floor(position * len(RDBU_11)))
        color_index = max(0, min(len(RDBU_11) - 1, color_index))
        r, g, b = RDBU_11[color_index]
        colors.append([r, g, b, 220])
    return colors


def _residual_station_data(dataset):
    return pd.DataFrame(
        {
            "lon": dataset.station.lon.to_numpy(),
            "lat": dataset.station.lat.to_numpy(),
            "res_mag": dataset.resmag,
        }
    )


def residual_compare_layers(right_dataset, left_dataset, velocity_scale):
    right = _residual_station_data(right_dataset)
    left = _residual_station_data(left_dataset)

    common = right.merge(
        left,
        how="inner",
        on=["lon", "lat"],
        suffixes=("_1", "_2"),
    )
    unique = (
        pd.concat(
            (
                right[["lon", "lat"]],
                left[["lon", "lat"]],
            ),
            ignore_index=True,
        )
        .drop_duplicates(keep=False, ignore_index=True)
        .reset_index(drop=True)
    )

    layers = []

    if not common.empty:
        res_mag_diff = common["res_mag_2"].to_numpy() - common["res_mag_1"].to_numpy()
        sized_res_mag_diff = (
            np.abs(res_mag_diff) * RES_COMPARE_SIZE_SCALE * velocity_scale
        )

        common_df = pd.DataFrame(
            {
                "lon": common["lon"].to_numpy(),
                "lat": common["lat"].to_numpy(),
                "res_mag_diff": res_mag_diff,
                "size": sized_res_mag_diff,
                "color": _map_residual_diff_colors(res_mag_diff),
                "icon": [CIRCLE_ICON] * len(common),
            }
        )
        common_df["tooltip"] = [
            f"<b>Resid. diff</b>: {value:.4f} mm/yr" for value in res_mag_diff
        ]

        layers.extend(
            icon_layers(
                "res_compare_common",
                common_df,
                get_position=["lon", "lat"],
                get_icon="icon",
                get_color="color",
                get_size="size",
                folder_number="compare",
                position_lon_key="lon",
                size_min_pixels=0,
                pickable=True,
            )
        )

    if not unique.empty:
        unique_df = unique.copy()
        unique_df["icon"] = [CIRCLE_ICON] * len(unique_df)
        unique_df["tooltip"] = [
            "<b>Unique station</b>: present in only one dataset"
        ] * len(unique_df)

        layers.extend(
            icon_layers(
                "res_compare_unique",
                unique_df,
                get_position=["lon", "lat"],
                get_icon="icon",
                get_color=RES_COMPARE_UNIQUE_COLOR,
                get_size=RES_COMPARE_UNIQUE_SIZE_PIXELS,
                folder_number="compare",
                position_lon_key="lon",
                pickable=True,
            )
        )

    return layers
