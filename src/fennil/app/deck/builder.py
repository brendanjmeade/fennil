import pydeck as pdk

from fennil.app.registry import FIELD_REGISTRY, LayerContext

from . import mapbox
from .faults import fault_line_layers


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


def build_layers_dataset(config, ds_index, velocity_scale=1):
    """Create DeckGL layers for a specific folder's data."""
    tde_layers = []
    layers = []
    vector_layers = []

    if not config.enabled:
        return tde_layers, layers, vector_layers

    data = config.data
    folder_number = ds_index + 1

    station = data.station
    x_station = data.x_station
    y_station = data.y_station

    base_width = ds_index + 1
    seg_tooltip_enabled = not ds_index

    fault_layers, fault_lines_df = fault_line_layers(
        folder_number, data.segment, seg_tooltip_enabled
    )
    layers.extend(fault_layers)

    ctx = LayerContext(
        config=config,
        ds_index=ds_index,
        folder_number=folder_number,
        station=station,
        x_station=x_station,
        y_station=y_station,
        velocity_scale=velocity_scale,
        colors=config.colors,
        base_width=base_width,
        tde_layers=tde_layers,
        layers=layers,
        vector_layers=vector_layers,
        fault_lines_df=fault_lines_df,
        seg_tooltip_enabled=seg_tooltip_enabled,
    )
    for field_name in config.available_fields:
        FIELD_REGISTRY.build_layers(field_name, ctx)

    return tde_layers, layers, vector_layers
