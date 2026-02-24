from urllib.parse import quote

import numpy as np
import pandas as pd

from fennil.app.deck.primitives import icon_layers, line_layers
from fennil.app.geo_projs import normalize_longitude_difference, web_mercator_to_wgs84

from .styles import (
    VECTOR_ARROW_MAX_PIXELS,
    VECTOR_ARROW_MIN_PIXELS,
    VECTOR_ARROW_SIZE_FACTOR,
    VELOCITY_SCALE,
)

ARROW_ICON = {
    "url": "data:image/svg+xml;utf8,"
    + quote(
        "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>"
        "<polygon fill='black' points='32,4 60,60 4,60'/>"
        "</svg>"
    ),
    "width": 64,
    "height": 64,
    "anchorY": 64,
    "mask": True,
}


def velocity_layers(
    layer_id_prefix,
    station,
    x_station,
    y_station,
    east_component,
    north_component,
    base_color,
    line_width,
    folder_number,
    velocity_scale,
):
    """Build velocity lines and matching arrowhead tips (including -360 duplicates)."""
    x_station = np.asarray(x_station)
    y_station = np.asarray(y_station)
    east_component = np.asarray(east_component)
    north_component = np.asarray(north_component)

    start_lon = station.lon.to_numpy()
    start_lat = station.lat.to_numpy()

    scale = velocity_scale * VELOCITY_SCALE
    x_end = x_station + scale * east_component
    y_end = y_station + scale * north_component
    end_lon, end_lat = web_mercator_to_wgs84(x_end, y_end)
    end_lon = normalize_longitude_difference(start_lon, end_lon)

    base_df = pd.DataFrame(
        {
            "start_lon": start_lon,
            "start_lat": start_lat,
            "end_lon": end_lon,
            "end_lat": end_lat,
        }
    )
    layers = line_layers(
        layer_id_prefix,
        base_df,
        base_color,
        line_width,
        folder_number,
        width_min_pixels=1,
        pickable=False,
    )

    vector_magnitude = np.hypot(east_component, north_component)
    arrow_mask = np.isfinite(vector_magnitude) & (vector_magnitude > 0)
    if not np.any(arrow_mask):
        return layers

    # IconLayer rotation is counter-clockwise; convert from clockwise bearing.
    angle = -np.degrees(np.arctan2(east_component, north_component)) % 360.0
    arrow_count = int(np.count_nonzero(arrow_mask))

    arrow_df = pd.DataFrame(
        {
            "lon": end_lon[arrow_mask],
            "lat": end_lat[arrow_mask],
            "angle": angle[arrow_mask],
            "icon": [ARROW_ICON] * arrow_count,
        }
    )
    arrow_size = float(
        np.clip(
            line_width * VECTOR_ARROW_SIZE_FACTOR,
            VECTOR_ARROW_MIN_PIXELS,
            VECTOR_ARROW_MAX_PIXELS,
        )
    )
    layers.extend(
        icon_layers(
            f"{layer_id_prefix}_arrow",
            arrow_df,
            get_position=["lon", "lat"],
            get_icon="icon",
            get_color=base_color,
            get_size=arrow_size,
            get_angle="angle",
            folder_number=folder_number,
            position_lon_key="lon",
            size_min_pixels=VECTOR_ARROW_MIN_PIXELS,
            size_max_pixels=VECTOR_ARROW_MAX_PIXELS,
            billboard=False,
            pickable=False,
        )
    )

    return layers
