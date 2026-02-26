from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.slip_compare import REQUIRED_SLIP_COMPARE_COLS, slip_compare_layers

SPEC = FieldSpec(
    priority=51,
    label="Slip compare",
    icon="mdi-align-vertical-center",
    ui_type="VBtnToggle",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
    styles={
        "icon_color": "rgba(44, 160, 44, 0.78)",
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

    slip_type = left.fields.get(name) or right.fields.get(name)
    if slip_type not in {"ss", "ds"}:
        return

    ctx.layers.extend(
        slip_compare_layers(
            right.data,
            left.data,
            slip_type,
            ctx.velocity_scale,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and REQUIRED_SLIP_COMPARE_COLS.issubset(
        dataset.segment.columns
    )
