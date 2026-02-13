from fennil.app.deck.vectors import velocity_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=10,
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    color_key="obs",
    options=None,
    default=False,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    station = ctx.station
    ctx.vector_layers.extend(
        velocity_layers(
            "obs_vel",
            station,
            ctx.x_station,
            ctx.y_station,
            station.east_vel.values,
            station.north_vel.values,
            ctx.colors["obs"],
            ctx.base_width,
            ctx.folder_number,
            ctx.velocity_scale,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
