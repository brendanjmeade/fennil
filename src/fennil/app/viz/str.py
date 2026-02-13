from fennil.app.deck.vectors import velocity_layers
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=16,
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    color_key="str",
    options=None,
    default=False,
)


def builder(ctx: LayerContext, value):
    if not value:
        return
    station = ctx.station
    ctx.vector_layers.extend(
        velocity_layers(
            "str_vel",
            station,
            ctx.x_station,
            ctx.y_station,
            station.model_east_vel_block_strain_rate.values,
            station.model_north_vel_block_strain_rate.values,
            ctx.colors["str"],
            ctx.base_width,
            ctx.folder_number,
            ctx.velocity_scale,
        )
    )
