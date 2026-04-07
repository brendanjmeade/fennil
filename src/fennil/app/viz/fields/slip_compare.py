from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.slip_compare import REQUIRED_SLIP_COMPARE_COLS, slip_compare_layers
from fennil.app.viz.styles import (
    SLIP_COMPARE_FASTER_COLOR,
    SLIP_COMPARE_SLOWER_COLOR,
    nonnegative_float,
    normalize_dataset_values,
)

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
        "colors": [list(SLIP_COMPARE_SLOWER_COLOR), list(SLIP_COMPARE_FASTER_COLOR)],
        "pair_labels": ["Negative", "Positive"],
        "segment_scale": 1.0,
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

    slip_type = left.fields.get(name)
    if slip_type not in {"ss", "ds"}:
        return

    styles = ctx.specs[name].get("styles", {})
    color_pair = normalize_dataset_values(
        styles.get("colors"),
        [SLIP_COMPARE_SLOWER_COLOR, SLIP_COMPARE_FASTER_COLOR],
    )
    negative_color = list(color_pair[0])
    positive_color = list(color_pair[1])
    segment_scale = nonnegative_float(styles.get("segment_scale"))

    ctx.layers.extend(
        slip_compare_layers(
            right.data,
            left.data,
            slip_type,
            ctx.velocity_scale,
            positive_color=positive_color,
            negative_color=negative_color,
            segment_scale=segment_scale,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and REQUIRED_SLIP_COMPARE_COLS.issubset(
        dataset.segment.columns
    )
