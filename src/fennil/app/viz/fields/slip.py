from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.faults import (
    REQUIRED_SEG_COLS,
    fault_line_dataframe,
    segment_slip_layers,
)
from fennil.app.viz.styles import (
    SLIP_NEGATIVE_COLOR,
    SLIP_POSITIVE_COLOR,
    dataset_value,
    nonnegative_float,
    normalize_dataset_values,
)

SPEC = FieldSpec(
    priority=20,
    label="Slip",
    icon="mdi-chart-line-variant",
    ui_type="VBtnToggle",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
    styles={
        "icon_color": "#1976D2",
        "colors_negative": [list(SLIP_NEGATIVE_COLOR), list(SLIP_NEGATIVE_COLOR)],
        "colors_positive": [list(SLIP_POSITIVE_COLOR), list(SLIP_POSITIVE_COLOR)],
        "segment_scale": 1.0,
    },
)


def builder(name: str, ctx: LayerContext):
    styles = ctx.specs[name].get("styles", {})
    negative_colors = normalize_dataset_values(
        styles.get("colors_negative"),
        [SLIP_NEGATIVE_COLOR, SLIP_NEGATIVE_COLOR],
    )
    positive_colors = normalize_dataset_values(
        styles.get("colors_positive"),
        [SLIP_POSITIVE_COLOR, SLIP_POSITIVE_COLOR],
    )
    segment_scale = nonnegative_float(styles.get("segment_scale"))

    for idx, dataset in ctx.enabled_datasets(name):
        folder_number = idx + 1
        seg_tooltip_enabled = True
        fault_lines_df = fault_line_dataframe(dataset.data.segment, seg_tooltip_enabled)
        negative_color = list(dataset_value(negative_colors, idx))
        positive_color = list(dataset_value(positive_colors, idx))
        ctx.layers.extend(
            segment_slip_layers(
                folder_number,
                dataset.data.segment,
                dataset.fields[name],
                seg_tooltip_enabled,
                fault_lines_df,
                ctx.velocity_scale,
                positive_color=positive_color,
                negative_color=negative_color,
                segment_scale=segment_scale,
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and REQUIRED_SEG_COLS.issubset(dataset.segment.columns)
