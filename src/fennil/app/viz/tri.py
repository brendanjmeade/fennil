from fennil.app.deck.vectors import velocity_layers
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=15,
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    color_key="tde",
    options=None,
    default=False,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    station = ctx.station
    ctx.vector_layers.extend(
        velocity_layers(
            "tde_vel",
            station,
            ctx.x_station,
            ctx.y_station,
            station.model_east_vel_tde.values,
            station.model_north_vel_tde.values,
            ctx.colors["tde"],
            ctx.base_width,
            ctx.folder_number,
            ctx.velocity_scale,
        )
    )
