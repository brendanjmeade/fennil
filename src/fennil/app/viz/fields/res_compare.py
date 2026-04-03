from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
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
    color_map_range = styles.get("color_map_range", {})
    try:
        value_min = float(color_map_range.get("min", RES_COMPARE_DIFF_MIN))
        value_max = float(color_map_range.get("max", RES_COMPARE_DIFF_MAX))
    except (TypeError, ValueError):
        value_min = RES_COMPARE_DIFF_MIN
        value_max = RES_COMPARE_DIFF_MAX

    ctx.layers.extend(
        residual_compare_layers(
            right.data,
            left.data,
            ctx.velocity_scale,
            value_min=value_min,
            value_max=value_max,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
