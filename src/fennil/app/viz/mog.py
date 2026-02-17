from fennil.app.deck.stations import station_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=16,
    label="Mog",
    icon="mdi-circle-medium",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(128, 128, 128, 0.78)",
        "colors": [
            (128, 128, 128, 200),
            (102, 102, 102, 200),
        ],
        "line_width": (1, 2),
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    for idx, dataset in ctx.enabled_datasets(name):
        ctx.layers.extend(
            station_layers(
                dataset.name,
                dataset.data.station,
                ctx.specs[name]["styles"]["colors"][idx],
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
