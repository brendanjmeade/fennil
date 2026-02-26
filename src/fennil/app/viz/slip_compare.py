import numpy as np
import pandas as pd

from fennil.app.deck.primitives import line_layers

from .styles import (
    FAULT_PROJ_LINE_WIDTH,
    SLIP_COMPARE_FASTER_COLOR,
    SLIP_COMPARE_MATCH_TOL_DEG,
    SLIP_COMPARE_NEUTRAL_COLOR,
    SLIP_COMPARE_SLOWER_COLOR,
    SLIP_COMPARE_WIDTH_MIN_PIXELS,
    SLIP_COMPARE_WIDTH_SCALE,
)

REQUIRED_SLIP_COMPARE_COLS = {
    "lon1",
    "lat1",
    "lon2",
    "lat2",
    "model_strike_slip_rate",
    "model_dip_slip_rate",
    "model_tensile_slip_rate",
}


def slip_compare_layers(right_dataset, left_dataset, slip_type, velocity_scale):
    velocity_scale = 1.0 if velocity_scale is None else float(velocity_scale)

    right_df = _segment_slip_frame(right_dataset.segment, slip_type)
    left_df = _segment_slip_frame(left_dataset.segment, slip_type)

    shared = right_df.merge(left_df, on="segment_key", suffixes=("_right", "_left"))
    shared_keys = set(shared["segment_key"])

    layers = []

    if not shared.empty:
        diff = (
            shared["slip_rate_left"].to_numpy() - shared["slip_rate_right"].to_numpy()
        )
        shared_df = pd.DataFrame(
            {
                "start_lon": shared["start_lon_right"].to_numpy(),
                "start_lat": shared["start_lat_right"].to_numpy(),
                "end_lon": shared["end_lon_right"].to_numpy(),
                "end_lat": shared["end_lat_right"].to_numpy(),
                "line_width": np.abs(diff),
                "color": [_diff_color(value) for value in diff],
            }
        )
        shared_df["tooltip"] = [
            _shared_tooltip(name_left, name_right, left_rate, right_rate, diff_rate)
            for name_left, name_right, left_rate, right_rate, diff_rate in zip(
                shared["name_left"].to_numpy(),
                shared["name_right"].to_numpy(),
                shared["slip_rate_left"].to_numpy(),
                shared["slip_rate_right"].to_numpy(),
                diff,
                strict=False,
            )
        ]
        layers.extend(
            line_layers(
                "slip_compare_shared",
                shared_df,
                "color",
                "line_width",
                "compare",
                width_min_pixels=SLIP_COMPARE_WIDTH_MIN_PIXELS,
                width_scale=SLIP_COMPARE_WIDTH_SCALE * velocity_scale,
                width_units="pixels",
                pickable=True,
            )
        )

    unmatched_right = _unmatched_segments_df(right_df, shared_keys, "right")
    unmatched_left = _unmatched_segments_df(left_df, shared_keys, "left")
    unmatched_df = pd.concat((unmatched_right, unmatched_left), ignore_index=True)
    if not unmatched_df.empty:
        layers.extend(
            line_layers(
                "slip_compare_unmatched",
                unmatched_df,
                "color",
                "line_width",
                "compare",
                width_min_pixels=FAULT_PROJ_LINE_WIDTH,
                width_scale=1,
                width_units="pixels",
                pickable=True,
            )
        )

    return layers


def _segment_slip_frame(segment, slip_type):
    frame = _build_segment_rows(segment, slip_type)
    frame = _finite_segment_rows(frame)
    if frame.empty:
        frame["segment_key"] = pd.Series(dtype=str)
        return frame

    frame = _with_unordered_segment_keys(frame)
    return frame.groupby("segment_key", as_index=False).agg(
        start_lon=("start_lon", "first"),
        start_lat=("start_lat", "first"),
        end_lon=("end_lon", "first"),
        end_lat=("end_lat", "first"),
        slip_rate=("slip_rate", "mean"),
        name=("name", "first"),
    )


def _build_segment_rows(segment, slip_type):
    return pd.DataFrame(
        {
            "start_lon": segment["lon1"].to_numpy(dtype=float),
            "start_lat": segment["lat1"].to_numpy(dtype=float),
            "end_lon": segment["lon2"].to_numpy(dtype=float),
            "end_lat": segment["lat2"].to_numpy(dtype=float),
            "slip_rate": _segment_slip_values(segment, slip_type),
            "name": (
                segment["name"].fillna("").astype(str).to_numpy()
                if "name" in segment.columns
                else np.array([""] * len(segment), dtype=object)
            ),
        }
    )


def _finite_segment_rows(frame):
    valid_mask = (
        np.isfinite(frame["start_lon"].to_numpy())
        & np.isfinite(frame["start_lat"].to_numpy())
        & np.isfinite(frame["end_lon"].to_numpy())
        & np.isfinite(frame["end_lat"].to_numpy())
        & np.isfinite(frame["slip_rate"].to_numpy())
    )
    return frame.loc[valid_mask].copy()


def _with_unordered_segment_keys(frame):
    start_lon_q = _quantized(frame["start_lon"].to_numpy())
    start_lat_q = _quantized(frame["start_lat"].to_numpy())
    end_lon_q = _quantized(frame["end_lon"].to_numpy())
    end_lat_q = _quantized(frame["end_lat"].to_numpy())

    endpoint_a = _endpoint_key(start_lon_q, start_lat_q)
    endpoint_b = _endpoint_key(end_lon_q, end_lat_q)
    segment_keys = [
        _unordered_pair_key(a, b) for a, b in zip(endpoint_a, endpoint_b, strict=False)
    ]

    keyed_rows = frame.copy()
    keyed_rows["segment_key"] = segment_keys
    return keyed_rows


def _quantized(values):
    return np.rint(values / SLIP_COMPARE_MATCH_TOL_DEG)


def _endpoint_key(lon_q, lat_q):
    return lon_q.astype(np.int64).astype(str) + ":" + lat_q.astype(np.int64).astype(str)


def _unordered_pair_key(endpoint_a, endpoint_b):
    if endpoint_a <= endpoint_b:
        return f"{endpoint_a}:{endpoint_b}"
    return f"{endpoint_b}:{endpoint_a}"


def _unmatched_segments_df(source_df, shared_keys, model_name):
    if source_df.empty:
        return pd.DataFrame()

    unmatched = source_df[~source_df["segment_key"].isin(shared_keys)].copy()
    if unmatched.empty:
        return pd.DataFrame()

    unmatched["line_width"] = float(FAULT_PROJ_LINE_WIDTH)
    unmatched["color"] = [SLIP_COMPARE_NEUTRAL_COLOR] * len(unmatched)
    unmatched["tooltip"] = [
        _unmatched_tooltip(model_name, name, slip)
        for name, slip in zip(
            unmatched["name"].to_numpy(),
            unmatched["slip_rate"].to_numpy(),
            strict=False,
        )
    ]
    return unmatched[
        [
            "start_lon",
            "start_lat",
            "end_lon",
            "end_lat",
            "line_width",
            "color",
            "tooltip",
        ]
    ].reset_index(drop=True)


def _segment_slip_values(segment, slip_type):
    if slip_type == "ss":
        values = segment["model_strike_slip_rate"].to_numpy(dtype=float)
    else:
        values = segment["model_dip_slip_rate"].to_numpy(dtype=float) - segment[
            "model_tensile_slip_rate"
        ].to_numpy(dtype=float)
    return np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)


def _diff_color(diff_rate):
    if diff_rate > 0:
        return SLIP_COMPARE_FASTER_COLOR
    if diff_rate < 0:
        return SLIP_COMPARE_SLOWER_COLOR
    return SLIP_COMPARE_NEUTRAL_COLOR


def _shared_tooltip(name_left, name_right, left_rate, right_rate, diff_rate):
    shared_name = name_left or name_right or "n/a"
    return (
        f"<b>Name</b>: {shared_name}<br/>"
        f"<b>Left slip</b>: {left_rate:.4f} mm/yr<br/>"
        f"<b>Right slip</b>: {right_rate:.4f} mm/yr<br/>"
        f"<b>Diff (left-right)</b>: {diff_rate:.4f} mm/yr"
    )


def _unmatched_tooltip(model_name, name, slip):
    return (
        f"<b>Name</b>: {name or 'n/a'}<br/>"
        f"<b>Only in</b>: {model_name} model<br/>"
        f"<b>Slip</b>: {slip:.4f} mm/yr"
    )
