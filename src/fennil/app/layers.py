import numpy as np
import pandas as pd
import pydeck as pdk

from .state import FolderState
from .utils import Dataset
from .utils.geo import (
    normalize_longitude_difference,
    shift_longitudes_df,
    shift_polygon_df,
    web_mercator_to_wgs84,
)

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


def build_layers_for_folder(
    folder_number, data: Dataset, folder_state: FolderState, state
):
    """Create DeckGL layers for a specific folder's data."""
    tde_layers = []
    layers = []
    vector_layers = []
    station = data.station
    x_station = data.x_station
    y_station = data.y_station

    vis_keys = (
        "show_locs",
        "show_obs",
        "show_mod",
        "show_res",
        "show_rot",
        "show_seg",
        "show_tri",
        "show_str",
        "show_mog",
    )
    vis = {k: folder_state[k] for k in vis_keys}

    colors = TYPE_COLORS[folder_number]
    base_width = LINE_WIDTHS[folder_number]

    def add_velocity_layer(
        layer_id_prefix, east_component, north_component, base_color, line_width
    ):
        """Add base and -360 shifted velocity line layers using the same color."""
        velocity_scale = state.velocity_scale * VELOCITY_SCALE
        x_end = x_station + velocity_scale * east_component
        y_end = y_station + velocity_scale * north_component
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

        add_line_layer(
            layer_id_prefix,
            base_df,
            base_color,
            line_width,
            width_min_pixels=1,
            pickable=False,
            layer_list=vector_layers,
        )

    def add_line_layer(
        layer_id_prefix,
        data_df,
        get_color,
        line_width,
        width_min_pixels=1,
        pickable=False,
        layer_list=None,
    ):
        """Add base and -360 shifted line layers."""
        target_layers = layer_list if layer_list is not None else layers
        target_layers.append(
            pdk.Layer(
                "LineLayer",
                data=data_df,
                get_source_position=["start_lon", "start_lat"],
                get_target_position=["end_lon", "end_lat"],
                get_color=get_color,
                get_width=line_width,
                width_min_pixels=width_min_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_{folder_number}",
            )
        )

        shift_df = shift_longitudes_df(data_df, ["start_lon", "end_lon"])
        target_layers.append(
            pdk.Layer(
                "LineLayer",
                data=shift_df,
                get_source_position=["start_lon", "start_lat"],
                get_target_position=["end_lon", "end_lat"],
                get_color=get_color,
                get_width=line_width,
                width_min_pixels=width_min_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_shift_{folder_number}",
            )
        )

    def add_polygon_layer(
        layer_id_prefix,
        data_df,
        fill_color,
        line_color,
        line_width,
        line_width_min_pixels=1,
        stroked=True,
        pickable=True,
        layer_list=None,
    ):
        """Add base and -360 shifted polygon layers."""
        target_layers = layer_list if layer_list is not None else layers
        target_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=data_df,
                get_polygon="polygon",
                get_fill_color=fill_color,
                get_line_color=line_color,
                get_line_width=line_width,
                filled=True,
                stroked=stroked,
                line_width_min_pixels=line_width_min_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_{folder_number}",
            )
        )

        shift_df = shift_polygon_df(data_df)
        target_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=shift_df,
                get_polygon="polygon",
                get_fill_color=fill_color,
                get_line_color=line_color,
                get_line_width=line_width,
                filled=True,
                stroked=stroked,
                line_width_min_pixels=line_width_min_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_shift_{folder_number}",
            )
        )

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

    def add_scatter_layer(
        layer_id_prefix,
        data_df,
        fill_color,
        radius,
        radius_min_pixels=1,
        radius_max_pixels=10,
        pickable=False,
    ):
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=data_df,
                get_position=["lon", "lat"],
                get_fill_color=fill_color,
                get_radius=radius,
                radius_min_pixels=radius_min_pixels,
                radius_max_pixels=radius_max_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_{folder_number}",
            )
        )
        shift_df = shift_longitudes_df(data_df, ["lon"])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=shift_df,
                get_position=["lon", "lat"],
                get_fill_color=fill_color,
                get_radius=radius,
                radius_min_pixels=radius_min_pixels,
                radius_max_pixels=radius_max_pixels,
                pickable=pickable,
                id=f"{layer_id_prefix}_shift_{folder_number}",
            )
        )

    def format_number(value, precision=4):
        try:
            if not np.isfinite(value):
                return "n/a"
        except TypeError:
            return "n/a"
        return f"{value:.{precision}f}"

    def format_segment_tooltip(name, lon1, lat1, lon2, lat2, ss_rate, ds_rate, ts_rate):
        return (
            f"<b>Name</b>: {name}<br/>"
            f"<b>Start</b>: ({format_number(lon1)}, {format_number(lat1)})<br/>"
            f"<b>End</b>: ({format_number(lon2)}, {format_number(lat2)})<br/>"
            f"<b>Strike-Slip Rate</b>: {format_number(ss_rate)}<br/>"
            f"<b>Dip-Slip Rate</b>: {format_number(ds_rate)}<br/>"
            f"<b>Tensile-Slip Rate</b>: {format_number(ts_rate)}"
        )

    if folder_state["show_locs"]:
        station_df = pd.DataFrame(
            {
                "lon": station.lon.to_numpy(),
                "lat": station.lat.to_numpy(),
                "name": station.name.to_numpy(),
            }
        )
        station_df["tooltip"] = [f"<b>Name</b>: {name}" for name in station_df["name"]]

        add_scatter_layer(
            "stations",
            station_df,
            colors["loc"],
            3000,
            radius_min_pixels=2,
            radius_max_pixels=5,
            pickable=True,
        )

    if vis["show_obs"]:
        add_velocity_layer(
            "obs_vel",
            station.east_vel.values,
            station.north_vel.values,
            colors["obs"],
            base_width,
        )

    if vis["show_mod"]:
        add_velocity_layer(
            "mod_vel",
            station.model_east_vel.values,
            station.model_north_vel.values,
            colors["mod"],
            base_width,
        )

    if vis["show_res"]:
        add_velocity_layer(
            "res_vel",
            station.model_east_vel_residual.values,
            station.model_north_vel_residual.values,
            colors["res"],
            base_width,
        )

    if vis["show_rot"]:
        add_velocity_layer(
            "rot_vel",
            station.model_east_vel_rotation.values,
            station.model_north_vel_rotation.values,
            colors["rot"],
            base_width,
        )

    if vis["show_seg"]:
        add_velocity_layer(
            "seg_vel",
            station.model_east_elastic_segment.values,
            station.model_north_elastic_segment.values,
            colors["seg"],
            base_width,
        )

    if vis["show_tri"]:
        add_velocity_layer(
            "tde_vel",
            station.model_east_vel_tde.values,
            station.model_north_vel_tde.values,
            colors["tde"],
            base_width,
        )

    if vis["show_str"]:
        add_velocity_layer(
            "str_vel",
            station.model_east_vel_block_strain_rate.values,
            station.model_north_vel_block_strain_rate.values,
            colors["str"],
            base_width,
        )

    if vis["show_mog"]:
        add_velocity_layer(
            "mog_vel",
            station.model_east_vel_mogi.values,
            station.model_north_vel_mogi.values,
            colors["mog"],
            base_width,
        )

    show_tde = folder_state["show_tde"]
    if show_tde:
        if not data.tde_available:
            folder_state["show_tde"] = False
        else:
            tde_df = data.tde_df
            if tde_df is not None and not tde_df.empty:
                tde_slip_type = folder_state["tde_slip_type"]
                if tde_slip_type == "ss":
                    slip_values = tde_df["ss_rate"].to_numpy()
                else:
                    slip_values = tde_df["ds_rate"].to_numpy()
                tde_df = tde_df.copy()
                tde_df["color"] = map_slip_colors(slip_values)
                add_polygon_layer(
                    "tde",
                    tde_df,
                    "color",
                    [0, 0, 0, 0],
                    0,
                    line_width_min_pixels=0,
                    stroked=False,
                    pickable=False,
                    layer_list=tde_layers,
                )

            tde_perim_df = data.tde_perim_df
            if tde_perim_df is not None and not tde_perim_df.empty:
                tde_perim_df = tde_perim_df.copy()
                tde_perim_df["color"] = [
                    RED if int(flag) == 1 else BLACK
                    for flag in tde_perim_df["proj_col"]
                ]
                add_line_layer(
                    "tde_perim",
                    tde_perim_df,
                    "color",
                    1,
                    width_min_pixels=1,
                    pickable=False,
                    layer_list=tde_layers,
                )

    seg_tooltip_enabled = folder_number == 1

    segment = data.segment
    fault_lines_df = pd.DataFrame(
        {
            "start_lon": segment.lon1.to_numpy(),
            "start_lat": segment.lat1.to_numpy(),
            "end_lon": segment.lon2.to_numpy(),
            "end_lat": segment.lat2.to_numpy(),
        }
    )
    if seg_tooltip_enabled and {
        "model_strike_slip_rate",
        "model_dip_slip_rate",
        "model_tensile_slip_rate",
    }.issubset(segment.columns):
        fault_lines_df["tooltip"] = [
            format_segment_tooltip(
                name,
                lon1,
                lat1,
                lon2,
                lat2,
                ss_rate,
                ds_rate,
                ts_rate,
            )
            for name, lon1, lat1, lon2, lat2, ss_rate, ds_rate, ts_rate in zip(
                segment.name.to_numpy(),
                segment.lon1.to_numpy(),
                segment.lat1.to_numpy(),
                segment.lon2.to_numpy(),
                segment.lat2.to_numpy(),
                segment.model_strike_slip_rate.to_numpy(),
                segment.model_dip_slip_rate.to_numpy(),
                segment.model_tensile_slip_rate.to_numpy(),
            )
        ]

    add_line_layer(
        "fault",
        fault_lines_df,
        FAULT_LINE_STYLE[folder_number]["color"],
        FAULT_LINE_STYLE[folder_number]["width"],
        width_min_pixels=1,
        pickable=seg_tooltip_enabled,
    )

    show_seg_color = folder_state["show_seg_color"]
    if show_seg_color:
        seg_slip_type = folder_state["seg_slip_type"]

        required_cols = {
            "model_strike_slip_rate",
            "model_dip_slip_rate",
            "model_tensile_slip_rate",
        }
        if not required_cols.issubset(segment.columns):
            if folder_state["show_seg_color"]:
                folder_state["show_seg_color"] = False
            return tde_layers, layers, vector_layers

        if seg_slip_type == "ss":
            slip_values = segment.model_strike_slip_rate.to_numpy()
        else:
            slip_values = (
                segment.model_dip_slip_rate.to_numpy()
                - segment.model_tensile_slip_rate.to_numpy()
            )

        seg_lines_df = pd.DataFrame(
            {
                "start_lon": segment.lon1.to_numpy(),
                "start_lat": segment.lat1.to_numpy(),
                "end_lon": segment.lon2.to_numpy(),
                "end_lat": segment.lat2.to_numpy(),
                "slip_rate": slip_values,
            }
        )

        colors_array = map_slip_colors(slip_values)
        seg_lines_df["color"] = colors_array
        if seg_tooltip_enabled and "tooltip" in fault_lines_df.columns:
            seg_lines_df["tooltip"] = fault_lines_df["tooltip"].to_numpy()

        add_line_layer(
            "segments",
            seg_lines_df,
            "color",
            SEGMENT_LINE_WIDTH,
            width_min_pixels=2,
            pickable=seg_tooltip_enabled,
        )

    show_fault_proj = folder_state["show_fault_proj"]
    if show_fault_proj:
        if not data.fault_proj_available:
            folder_state["show_fault_proj"] = False
        else:
            fault_proj_df = data.fault_proj_df
            if fault_proj_df is not None and not fault_proj_df.empty:
                style = FAULT_PROJ_STYLE[folder_number]
                add_polygon_layer(
                    "fault_proj",
                    fault_proj_df,
                    style["fill"],
                    style["line"],
                    FAULT_PROJ_LINE_WIDTH,
                    pickable=False,
                )

    return tde_layers, layers, vector_layers
