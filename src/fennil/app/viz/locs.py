from fennil.app.deck.stations import station_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=0,
    icon="mdi-circle-medium",
    ui_type="VCheckbox",
    color_key="loc",
    options=None,
    default=False,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    ctx.layers.extend(station_layers(ctx.folder_number, ctx.station, ctx.colors["loc"]))


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
