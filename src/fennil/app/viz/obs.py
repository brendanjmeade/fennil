from fennil.app.deck.vectors import velocity_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=10,
    label="Obs",
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(0, 0, 205, 1)",
        "colors": [
            (0, 0, 205, 255),
            (0, 0, 205, 255),
        ],
        "line_width": (1, 2),
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    for idx, dataset in ctx.enabled_datasets(name):
        ctx.vector_layers.extend(
            velocity_layers(
                "obs_vel",
                dataset.data.station,
                dataset.data.x_station,
                dataset.data.y_station,
                dataset.data.station.east_vel.values,
                dataset.data.station.north_vel.values,
                ctx.specs[name]["styles"]["colors"][idx],
                ctx.specs[name]["styles"]["line_width"][idx],
                dataset.name,
                ctx.velocity_scale,
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
