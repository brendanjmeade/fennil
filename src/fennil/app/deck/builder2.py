import pydeck as pdk

from . import mapbox
from .faults import (
    REQUIRED_SEG_COLS,
    fault_line_layers,
    fault_projection_layers,
    segment_color_layers,
)
from .stations import station_layers
from .tde import tde_mesh_layers, tde_perimeter_layers
from .vectors import velocity_layers


def build_deck(layers, map_params):
    return pdk.Deck(
        map_provider=mapbox.PROVIDER,
        map_style=mapbox.STYLE,
        initial_view_state=pdk.ViewState(
            latitude=map_params.latitude,
            longitude=map_params.longitude,
            zoom=map_params.zoom,
            pitch=map_params.pitch,
            bearing=map_params.bearing,
        ),
        layers=layers,
    )


def show(fields, name):
    return fields[name]["value"]


def color(fields, name):
    return fields[name]["color"]


def build_layers_dataset(config, ds_index, velocity_scale=1):
    """Create DeckGL layers for a specific folder's data."""
    tde_layers = []
    layers = []
    vector_layers = []

    if not config.enabled:
        return tde_layers, layers, vector_layers

    data = config.data
    folder_number = ds_index + 1
    fields = config.fields

    station = data.station
    x_station = data.x_station
    y_station = data.y_station

    base_width = ds_index + 1

    if show(fields, "locs"):
        layers.extend(station_layers(folder_number, station, color(fields, "locs")))

    if show(fields, "obs"):
        vector_layers.extend(
            velocity_layers(
                "obs_vel",
                station,
                x_station,
                y_station,
                station.east_vel.values,
                station.north_vel.values,
                color(fields, "obs"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "mod"):
        vector_layers.extend(
            velocity_layers(
                "mod_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel.values,
                station.model_north_vel.values,
                color(fields, "mod"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "res"):
        vector_layers.extend(
            velocity_layers(
                "res_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_residual.values,
                station.model_north_vel_residual.values,
                color(fields, "res"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "rot"):
        vector_layers.extend(
            velocity_layers(
                "rot_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_rotation.values,
                station.model_north_vel_rotation.values,
                color(fields, "rot"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "seg"):
        vector_layers.extend(
            velocity_layers(
                "seg_vel",
                station,
                x_station,
                y_station,
                station.model_east_elastic_segment.values,
                station.model_north_elastic_segment.values,
                color(fields, "seg"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "tri"):
        vector_layers.extend(
            velocity_layers(
                "tde_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_tde.values,
                station.model_north_vel_tde.values,
                color(fields, "tde"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "str"):
        vector_layers.extend(
            velocity_layers(
                "str_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_block_strain_rate.values,
                station.model_north_vel_block_strain_rate.values,
                color(fields, "str"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    if show(fields, "mog"):
        vector_layers.extend(
            velocity_layers(
                "mog_vel",
                station,
                x_station,
                y_station,
                station.model_east_vel_mogi.values,
                station.model_north_vel_mogi.values,
                color(fields, "mog"),
                base_width,
                folder_number,
                velocity_scale,
            )
        )

    tde_slip_type = show(fields, "tde")
    if data.tde_available and tde_slip_type:
        tde_df = data.tde_df
        if tde_df is not None and not tde_df.empty:
            if tde_slip_type == "ss":
                slip_values = tde_df["ss_rate"].to_numpy()
            else:
                slip_values = tde_df["ds_rate"].to_numpy()
            tde_layers.extend(tde_mesh_layers(folder_number, tde_df, slip_values))

        tde_layers.extend(tde_perimeter_layers(folder_number, data.tde_perim_df))

    seg_tooltip_enabled = not ds_index

    fault_layers, fault_lines_df = fault_line_layers(
        folder_number, data.segment, seg_tooltip_enabled
    )
    layers.extend(fault_layers)

    slip_type = show(fields, "slip")
    if slip_type and REQUIRED_SEG_COLS.issubset(data.segment.columns):
        layers.extend(
            segment_color_layers(
                folder_number,
                data.segment,
                slip_type,
                seg_tooltip_enabled,
                fault_lines_df,
            )
        )

    if show(fields, "fault proj") and data.fault_proj_available:
        layers.extend(fault_projection_layers(folder_number, data.fault_proj_df))

    return tde_layers, layers, vector_layers
