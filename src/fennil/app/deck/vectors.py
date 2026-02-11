import pandas as pd

from fennil.app.geo_projs import normalize_longitude_difference, web_mercator_to_wgs84

from .primitives import line_layers
from .styles import VELOCITY_SCALE


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
    """Build base and -360 shifted velocity line layers."""
    scale = velocity_scale * VELOCITY_SCALE
    x_end = x_station + scale * east_component
    y_end = y_station + scale * north_component
    end_lon, end_lat = web_mercator_to_wgs84(x_end, y_end)
    end_lon = normalize_longitude_difference(station.lon.values, end_lon)

    base_df = pd.DataFrame(
        {
            "start_lon": station.lon.to_numpy(),
            "start_lat": station.lat.to_numpy(),
            "end_lon": end_lon,
            "end_lat": end_lat,
        }
    )

    return line_layers(
        layer_id_prefix,
        base_df,
        base_color,
        line_width,
        folder_number,
        width_min_pixels=1,
        pickable=False,
    )
