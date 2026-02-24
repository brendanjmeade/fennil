import pandas as pd

from fennil.app.deck.primitives import scatter_layers


def station_layers(folder_number, station, color):
    station_df = pd.DataFrame(
        {
            "lon": station.lon.to_numpy(),
            "lat": station.lat.to_numpy(),
            "name": station.name.to_numpy(),
        }
    )
    station_df["tooltip"] = [f"<b>Name</b>: {name}" for name in station_df["name"]]

    return scatter_layers(
        "stations",
        station_df,
        color,
        3000,
        folder_number,
        radius_min_pixels=2,
        radius_max_pixels=5,
        pickable=True,
    )
