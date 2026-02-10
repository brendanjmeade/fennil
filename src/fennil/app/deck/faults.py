import pandas as pd

from .primitives import line_layers, polygon_layers
from .styles import (
    FAULT_LINE_STYLE,
    FAULT_PROJ_LINE_WIDTH,
    FAULT_PROJ_STYLE,
    SEGMENT_LINE_WIDTH,
    map_slip_colors,
)
from .tooltips import format_segment_tooltip

REQUIRED_SEG_COLS = {
    "model_strike_slip_rate",
    "model_dip_slip_rate",
    "model_tensile_slip_rate",
}


def fault_line_layers(folder_number, segment, seg_tooltip_enabled):
    fault_lines_df = pd.DataFrame(
        {
            "start_lon": segment.lon1.to_numpy(),
            "start_lat": segment.lat1.to_numpy(),
            "end_lon": segment.lon2.to_numpy(),
            "end_lat": segment.lat2.to_numpy(),
        }
    )

    if seg_tooltip_enabled and REQUIRED_SEG_COLS.issubset(segment.columns):
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
                strict=False,
            )
        ]

    layers = line_layers(
        "fault",
        fault_lines_df,
        FAULT_LINE_STYLE[folder_number]["color"],
        FAULT_LINE_STYLE[folder_number]["width"],
        folder_number,
        width_min_pixels=1,
        pickable=seg_tooltip_enabled,
    )
    return layers, fault_lines_df


def segment_color_layers(
    folder_number,
    segment,
    seg_slip_type,
    seg_tooltip_enabled,
    fault_lines_df,
):
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

    return line_layers(
        "segments",
        seg_lines_df,
        "color",
        SEGMENT_LINE_WIDTH,
        folder_number,
        width_min_pixels=2,
        pickable=seg_tooltip_enabled,
    )


def fault_projection_layers(folder_number, fault_proj_df):
    if fault_proj_df is None or fault_proj_df.empty:
        return []
    style = FAULT_PROJ_STYLE[folder_number]
    return polygon_layers(
        "fault_proj",
        fault_proj_df,
        style["fill"],
        style["line"],
        FAULT_PROJ_LINE_WIDTH,
        folder_number,
        pickable=False,
    )
