from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.colormaps import DEFAULT_N_COLORS, parse_colormap_range
from fennil.app.viz.styles import COUPLING_MAX, COUPLING_MIN
from fennil.app.viz.tde import tde_coupling_layers, tde_perimeter_layers

REQUIRED_COUPLING_COLS = {"strike_slip_coupling", "dip_slip_coupling"}

SPEC = FieldSpec(
    priority=22,
    label="Coupling",
    icon="mdi-link-variant",
    ui_type="VBtnToggle",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
    styles={
        "icon_color": "rgba(111, 66, 193, 1)",
        "color_map_range": {
            "palette": "RDBU_11",
            "min": COUPLING_MIN,
            "max": COUPLING_MAX,
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
        default_min=COUPLING_MIN,
        default_max=COUPLING_MAX,
    )

    for idx, dataset in ctx.enabled_datasets(name):
        folder_number = idx + 1
        value = dataset.fields[name]
        tde_df = dataset.data.tde_df
        tde_perim_df = dataset.data.tde_perim_df
        if tde_df is not None and not tde_df.empty:
            if value == "ss" and "ss_coupling" in tde_df.columns:
                coupling_values = tde_df["ss_coupling"].to_numpy()
            elif value == "ds" and "ds_coupling" in tde_df.columns:
                coupling_values = tde_df["ds_coupling"].to_numpy()
            else:
                coupling_values = None

            if coupling_values is not None:
                ctx.tde_layers.extend(
                    tde_coupling_layers(
                        folder_number,
                        tde_df,
                        coupling_values,
                        colormap["min"],
                        colormap["max"],
                        palette_name=colormap["palette"],
                        n_colors=colormap["n_colors"],
                        invert=colormap["invert"],
                    )
                )
                ctx.tde_layers.extend(tde_perimeter_layers(folder_number, tde_perim_df))


def can_render(dataset: Dataset) -> bool:
    if dataset is None or not dataset.tde_available:
        return False
    return REQUIRED_COUPLING_COLS.issubset(dataset.meshes.columns)
