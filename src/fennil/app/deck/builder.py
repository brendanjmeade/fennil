from ..state import FolderState
from ..utils import Dataset
from .faults import (
    REQUIRED_SEG_COLS,
    fault_line_layers,
    fault_projection_layers,
    segment_color_layers,
)
from .stations import station_layers
from .styles import LINE_WIDTHS, TYPE_COLORS
from .tde import tde_mesh_layers, tde_perimeter_layers
from .vectors import velocity_layers


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

    if folder_state["show_locs"]:
        layers.extend(station_layers(folder_number, station, colors["loc"]))

    if vis["show_obs"]:
        vector_layers.extend(
            velocity_layers(
                "obs_vel",
                station,
                x_station,
                y_station,
                station.east_vel.values,
                station.north_vel.values,
                colors["obs"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_mod"]:
        vector_layers.extend(
            velocity_layers(
                "mod_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel.values,
                station.model_north_vel.values,
                colors["mod"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_res"]:
        vector_layers.extend(
            velocity_layers(
                "res_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_residual.values,
                station.model_north_vel_residual.values,
                colors["res"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_rot"]:
        vector_layers.extend(
            velocity_layers(
                "rot_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_rotation.values,
                station.model_north_vel_rotation.values,
                colors["rot"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_seg"]:
        vector_layers.extend(
            velocity_layers(
                "seg_vel",
                station,
                x_station,
                y_station,
                station.model_east_elastic_segment.values,
                station.model_north_elastic_segment.values,
                colors["seg"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_tri"]:
        vector_layers.extend(
            velocity_layers(
                "tde_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_tde.values,
                station.model_north_vel_tde.values,
                colors["tde"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_str"]:
        vector_layers.extend(
            velocity_layers(
                "str_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_block_strain_rate.values,
                station.model_north_vel_block_strain_rate.values,
                colors["str"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if vis["show_mog"]:
        vector_layers.extend(
            velocity_layers(
                "mog_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_mogi.values,
                station.model_north_vel_mogi.values,
                colors["mog"],
                base_width,
                folder_number,
                state.velocity_scale,
            )
        )

    if folder_state["show_tde"]:
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
                tde_layers.extend(tde_mesh_layers(folder_number, tde_df, slip_values))

            tde_layers.extend(tde_perimeter_layers(folder_number, data.tde_perim_df))

    seg_tooltip_enabled = folder_number == 1

    fault_layers, fault_lines_df = fault_line_layers(
        folder_number, data.segment, seg_tooltip_enabled
    )
    layers.extend(fault_layers)

    if folder_state["show_seg_color"]:
        if not REQUIRED_SEG_COLS.issubset(data.segment.columns):
            folder_state["show_seg_color"] = False
            return tde_layers, layers, vector_layers

        seg_slip_type = folder_state["seg_slip_type"]
        layers.extend(
            segment_color_layers(
                folder_number,
                data.segment,
                seg_slip_type,
                seg_tooltip_enabled,
                fault_lines_df,
            )
        )

    if folder_state["show_fault_proj"]:
        if not data.fault_proj_available:
            folder_state["show_fault_proj"] = False
        else:
            layers.extend(fault_projection_layers(folder_number, data.fault_proj_df))

    return tde_layers, layers, vector_layers
