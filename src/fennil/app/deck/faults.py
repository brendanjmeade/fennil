import numpy as np
import pandas as pd

from .primitives import line_layers, polygon_layers
from .styles import (
    FAULT_PROJ_LINE_WIDTH,
    SLIP_NEGATIVE_COLOR,
    SLIP_NEGATIVE_EXTREME_COLOR,
    SLIP_POSITIVE_COLOR,
    SLIP_POSITIVE_EXTREME_COLOR,
    SLIP_WIDTH_CAP_MM_PER_YR,
    SLIP_WIDTH_MIN_PIXELS,
    SLIP_WIDTH_SCALE,
)
from .tooltips import format_segment_tooltip

REQUIRED_SEG_COLS = {
    "model_strike_slip_rate",
    "model_dip_slip_rate",
    "model_tensile_slip_rate",
}


def fault_line_dataframe(segment, seg_tooltip_enabled):
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

    return fault_lines_df


def fault_line_layers(folder_number, segment, seg_tooltip_enabled, color, line_width):
    fault_lines_df = fault_line_dataframe(segment, seg_tooltip_enabled)

    layers = line_layers(
        "fault",
        fault_lines_df,
        color,
        line_width,
        folder_number,
        width_min_pixels=1,
        pickable=seg_tooltip_enabled,
    )
    return layers, fault_lines_df


def segment_slip_layers(
    folder_number,
    segment,
    seg_slip_type,
    seg_tooltip_enabled,
    fault_lines_df,
    velocity_scale=1.0,
):
    velocity_scale = 1.0 if velocity_scale is None else float(velocity_scale)

    if seg_slip_type == "ss":
        slip_values = segment.model_strike_slip_rate.to_numpy()
    else:
        slip_values = (
            segment.model_dip_slip_rate.to_numpy()
            - segment.model_tensile_slip_rate.to_numpy()
        )

    slip_values = np.asarray(slip_values)
    slip_values = np.nan_to_num(slip_values, nan=0.0, posinf=0.0, neginf=0.0)

    seg_lines_df = pd.DataFrame(
        {
            "start_lon": segment.lon1.to_numpy(),
            "start_lat": segment.lat1.to_numpy(),
            "end_lon": segment.lon2.to_numpy(),
            "end_lat": segment.lat2.to_numpy(),
            "slip_rate": slip_values,
            "line_width": np.clip(np.abs(slip_values), 0.0, SLIP_WIDTH_CAP_MM_PER_YR),
        }
    )

    def _slip_color(value):
        if value < -SLIP_WIDTH_CAP_MM_PER_YR:
            return SLIP_NEGATIVE_EXTREME_COLOR
        if value > SLIP_WIDTH_CAP_MM_PER_YR:
            return SLIP_POSITIVE_EXTREME_COLOR
        if value < 0:
            return SLIP_NEGATIVE_COLOR
        return SLIP_POSITIVE_COLOR

    seg_lines_df["color"] = [_slip_color(value) for value in slip_values]
    if seg_tooltip_enabled and "tooltip" in fault_lines_df.columns:
        seg_lines_df["tooltip"] = fault_lines_df["tooltip"].to_numpy()

    return line_layers(
        "segments",
        seg_lines_df,
        "color",
        "line_width",
        folder_number,
        width_min_pixels=SLIP_WIDTH_MIN_PIXELS,
        width_scale=SLIP_WIDTH_SCALE * velocity_scale,
        width_units="pixels",
        pickable=seg_tooltip_enabled,
    )


def fault_projection_layers(name, fault_proj_df, fill, line):
    if fault_proj_df is None or fault_proj_df.empty:
        return []
    return polygon_layers(
        "fault_proj",
        fault_proj_df,
        fill,
        line,
        FAULT_PROJ_LINE_WIDTH,
        name,
        pickable=False,
    )
