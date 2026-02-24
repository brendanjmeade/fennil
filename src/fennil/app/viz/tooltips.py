import numpy as np


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
