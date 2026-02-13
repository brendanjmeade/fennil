from fennil.app.deck.faults import fault_projection_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=30,
    icon="mdi-bandage",
    ui_type="VCheckbox",
    color_key=None,
    options=None,
    default=False,
    color=[128, 128, 128, 255],
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    data = ctx.config.data
    if not data.fault_proj_available:
        return
    ctx.layers.extend(fault_projection_layers(ctx.folder_number, data.fault_proj_df))


def can_render(dataset: Dataset) -> bool:
    if dataset is None:
        return False

    return dataset.fault_proj_available
