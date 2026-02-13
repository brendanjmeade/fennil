from fennil.app.deck.faults import (
    REQUIRED_SEG_COLS,
    fault_line_layers,
    segment_color_layers,
)
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

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
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    for idx, dataset in ctx.enabled_datasets(name):
        folder_number = idx + 1
        seg_tooltip_enabled = not idx  # show tooltip only for first dataset

        # FIXME should we always add fault_layers ?
        fault_layers, fault_lines_df = fault_line_layers(
            folder_number, dataset.data.segment, seg_tooltip_enabled
        )
        ctx.layers.extend(fault_layers)
        ctx.layers.extend(
            segment_color_layers(
                folder_number,
                dataset.data.segment,
                dataset.fields[name],
                seg_tooltip_enabled,
                fault_lines_df,
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None and REQUIRED_SEG_COLS.issubset(dataset.segment.columns)
