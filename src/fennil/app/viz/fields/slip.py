from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.faults import (
    REQUIRED_SEG_COLS,
    fault_line_dataframe,
    segment_slip_layers,
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
        "colors": [
            (0, 0, 255, 255),
            (0, 128, 0, 255),
        ],
        "line_width": (1, 1),
    },
)


def builder(name: str, ctx: LayerContext):
    for idx, dataset in ctx.enabled_datasets(name):
        folder_number = idx + 1
        seg_tooltip_enabled = not idx  # show tooltip only for first dataset
        fault_lines_df = fault_line_dataframe(dataset.data.segment, seg_tooltip_enabled)
        ctx.layers.extend(
            segment_slip_layers(
                folder_number,
                dataset.data.segment,
                dataset.fields[name],
                seg_tooltip_enabled,
                fault_lines_df,
                ctx.velocity_scale,
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and REQUIRED_SEG_COLS.issubset(dataset.segment.columns)
