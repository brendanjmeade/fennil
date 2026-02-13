from fennil.app.deck.vectors import velocity_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=14,
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    color_key="seg",
    options=None,
    default=False,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    station = ctx.station
    ctx.vector_layers.extend(
        velocity_layers(
            "seg_vel",
            station,
            ctx.x_station,
            ctx.y_station,
            station.model_east_elastic_segment.values,
            station.model_north_elastic_segment.values,
            ctx.colors["seg"],
            ctx.base_width,
            ctx.folder_number,
            ctx.velocity_scale,
        )
    )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
