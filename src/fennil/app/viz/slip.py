from fennil.app.deck.faults import (
    REQUIRED_SEG_COLS,
    segment_color_layers,
)
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=20,
    icon="mdi-chart-line-variant",
    ui_type="VBtnToggle",
    color_key="tde",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    data = ctx.config.data
    if not REQUIRED_SEG_COLS.issubset(data.segment.columns):
        return
    ctx.layers.extend(
        segment_color_layers(
            ctx.folder_number,
            data.segment,
            value,
            ctx.seg_tooltip_enabled,
            ctx.fault_lines_df,
        )
    )
