from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.colormaps import DEFAULT_N_COLORS, parse_colormap_range
from fennil.app.viz.styles import SLIP_RATE_MAX, SLIP_RATE_MIN
from fennil.app.viz.tde import tde_mesh_layers, tde_perimeter_layers

SPEC = FieldSpec(
    priority=21,
    label="TDE",
    icon="mdi-texture-box",
    ui_type="VBtnToggle",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
    styles={
        "icon_color": "rgba(14, 0, 214, 1)",
        "color_map_range": {
            "palette": "RDBU_11",
            "min": SLIP_RATE_MIN,
            "max": SLIP_RATE_MAX,
            "n_colors": DEFAULT_N_COLORS,
        },
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    styles = ctx.specs[name].get("styles", {})
    colormap = parse_colormap_range(
        styles.get("color_map_range"),
        default_min=SLIP_RATE_MIN,
        default_max=SLIP_RATE_MAX,
    )

    for idx, dataset in ctx.enabled_datasets(name):
        folder_number = idx + 1
        value = dataset.fields[name]
        tde_df = dataset.data.tde_df
        tde_perim_df = dataset.data.tde_perim_df
        if tde_df is not None and not tde_df.empty:
            slip_values = (
                tde_df["ss_rate"].to_numpy()
                if value == "ss"
                else tde_df["ds_rate"].to_numpy()
            )
            ctx.tde_layers.extend(
                tde_mesh_layers(
                    folder_number,
                    tde_df,
                    slip_values,
                    colormap["min"],
                    colormap["max"],
                    palette_name=colormap["palette"],
                    n_colors=colormap["n_colors"],
                    invert=colormap["invert"],
                )
            )
        ctx.tde_layers.extend(tde_perimeter_layers(folder_number, tde_perim_df))


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and dataset.tde_available
