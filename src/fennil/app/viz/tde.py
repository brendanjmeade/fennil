from fennil.app.deck.primitives import line_layers, polygon_layers

from .styles import BLACK, RED, map_coupling_colors, map_slip_colors


def tde_mesh_layers(folder_number, tde_df, slip_values, value_min, value_max):
    if tde_df is None or tde_df.empty:
        return []
    tde_df = tde_df.copy()
    tde_df["color"] = map_slip_colors(
        slip_values,
        value_min=value_min,
        value_max=value_max,
    )
    return polygon_layers(
        "tde",
        tde_df,
        "color",
        [0, 0, 0, 0],
        0,
        folder_number,
        line_width_min_pixels=0,
        stroked=False,
        pickable=False,
    )


def tde_coupling_layers(folder_number, tde_df, coupling_values, value_min, value_max):
    if tde_df is None or tde_df.empty:
        return []
    tde_df = tde_df.copy()
    tde_df["color"] = map_coupling_colors(
        coupling_values,
        value_min=value_min,
        value_max=value_max,
    )
    return polygon_layers(
        "tde_coupling",
        tde_df,
        "color",
        [0, 0, 0, 0],
        0,
        folder_number,
        line_width_min_pixels=0,
        stroked=False,
        pickable=False,
    )


def tde_perimeter_layers(folder_number, tde_perim_df):
    if tde_perim_df is None or tde_perim_df.empty:
        return []
    tde_perim_df = tde_perim_df.copy()
    tde_perim_df["color"] = [
        RED if int(flag) == 1 else BLACK for flag in tde_perim_df["proj_col"]
    ]
    return line_layers(
        "tde_perim",
        tde_perim_df,
        "color",
        1,
        folder_number,
        width_min_pixels=1,
        pickable=False,
    )
