from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.res_compare import residual_compare_layers

SPEC = FieldSpec(
    priority=50,
    label="Res compare",
    icon="mdi-circle-multiple",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(205, 0, 205, 0.78)",
        "colors": [
            (205, 0, 205, 200),
            (205, 0, 205, 200),
        ],
        "line_width": (1, 2),
    },
    multiple=False,
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    right = ctx.datasets[0]
    left = ctx.datasets[1]
    if not (right.enabled and left.enabled):
        return
    if right.data is None or left.data is None:
        return

    ctx.layers.extend(
        residual_compare_layers(
            right.data,
            left.data,
            ctx.velocity_scale,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
