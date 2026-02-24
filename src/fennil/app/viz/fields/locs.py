from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.stations import station_layers

SPEC = FieldSpec(
    priority=0,
    label="Locs",
    icon="mdi-circle-medium",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "black",
        "colors": [
            (0, 0, 0, 220),
            (0, 0, 0, 220),
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
