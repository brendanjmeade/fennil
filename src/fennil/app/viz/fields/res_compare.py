from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.colormaps import DEFAULT_N_COLORS, parse_colormap_range
from fennil.app.viz.res_compare import residual_compare_layers
from fennil.app.viz.styles import RES_COMPARE_DIFF_MAX, RES_COMPARE_DIFF_MIN

SPEC = FieldSpec(
    priority=50,
    label="Res compare",
    icon="mdi-circle-multiple",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(205, 0, 205, 0.78)",
        "color_map_range": {
            "palette": "RDBU_11",
            "min": RES_COMPARE_DIFF_MIN,
            "max": RES_COMPARE_DIFF_MAX,
            "n_colors": DEFAULT_N_COLORS,
        },
    },
    multiple=False,
)


def builder(name: str, ctx: LayerContext):
    right = ctx.datasets[0]
    left = ctx.datasets[1]
    if not (right.enabled and left.enabled):
        return
    if right.data is None or left.data is None:
        return
    if not left.fields.get(name):
        return

    styles = ctx.specs[name].get("styles", {})
    colormap = parse_colormap_range(
        styles.get("color_map_range"),
        default_min=RES_COMPARE_DIFF_MIN,
        default_max=RES_COMPARE_DIFF_MAX,
    )

    ctx.layers.extend(
        residual_compare_layers(
            right.data,
            left.data,
            ctx.velocity_scale,
            value_min=colormap["min"],
            value_max=colormap["max"],
            palette_name=colormap["palette"],
            n_colors=colormap["n_colors"],
            invert=colormap["invert"],
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
