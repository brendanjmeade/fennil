import pydeck as pdk

from . import mapbox


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
