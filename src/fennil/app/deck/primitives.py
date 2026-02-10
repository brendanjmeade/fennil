import pydeck as pdk

from ..utils.geo import shift_longitudes_df, shift_polygon_df


def line_layers(
    layer_id_prefix,
    data_df,
    get_color,
    line_width,
    folder_number,
    width_min_pixels=1,
    pickable=False,
):
    layers = [
        pdk.Layer(
            "LineLayer",
            data=data_df,
            get_source_position=["start_lon", "start_lat"],
            get_target_position=["end_lon", "end_lat"],
            get_color=get_color,
            get_width=line_width,
            width_min_pixels=width_min_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_{folder_number}",
        )
    ]

    shift_df = shift_longitudes_df(data_df, ["start_lon", "end_lon"])
    layers.append(
        pdk.Layer(
            "LineLayer",
            data=shift_df,
            get_source_position=["start_lon", "start_lat"],
            get_target_position=["end_lon", "end_lat"],
            get_color=get_color,
            get_width=line_width,
            width_min_pixels=width_min_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_shift_{folder_number}",
        )
    )
    return layers


def polygon_layers(
    layer_id_prefix,
    data_df,
    fill_color,
    line_color,
    line_width,
    folder_number,
    line_width_min_pixels=1,
    stroked=True,
    pickable=True,
):
    layers = [
        pdk.Layer(
            "PolygonLayer",
            data=data_df,
            get_polygon="polygon",
            get_fill_color=fill_color,
            get_line_color=line_color,
            get_line_width=line_width,
            filled=True,
            stroked=stroked,
            line_width_min_pixels=line_width_min_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_{folder_number}",
        )
    ]

    shift_df = shift_polygon_df(data_df)
    layers.append(
        pdk.Layer(
            "PolygonLayer",
            data=shift_df,
            get_polygon="polygon",
            get_fill_color=fill_color,
            get_line_color=line_color,
            get_line_width=line_width,
            filled=True,
            stroked=stroked,
            line_width_min_pixels=line_width_min_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_shift_{folder_number}",
        )
    )
    return layers


def scatter_layers(
    layer_id_prefix,
    data_df,
    fill_color,
    radius,
    folder_number,
    radius_min_pixels=1,
    radius_max_pixels=10,
    pickable=False,
):
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=data_df,
            get_position=["lon", "lat"],
            get_fill_color=fill_color,
            get_radius=radius,
            radius_min_pixels=radius_min_pixels,
            radius_max_pixels=radius_max_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_{folder_number}",
        )
    ]

    shift_df = shift_longitudes_df(data_df, ["lon"])
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=shift_df,
            get_position=["lon", "lat"],
            get_fill_color=fill_color,
            get_radius=radius,
            radius_min_pixels=radius_min_pixels,
            radius_max_pixels=radius_max_pixels,
            pickable=pickable,
            id=f"{layer_id_prefix}_shift_{folder_number}",
        )
    )
    return layers
