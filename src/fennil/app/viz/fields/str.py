from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.vectors import velocity_layers

SPEC = FieldSpec(
    priority=16,
    label="Str",
    icon="mdi-vector-line",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(0, 128, 128, 0.78)",
        "colors": [
            (0, 128, 128, 200),
            (0, 102, 102, 200),
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
                "str_vel",
                dataset.data.station,
                dataset.data.x_station,
                dataset.data.y_station,
                dataset.data.station.model_east_vel_block_strain_rate.values,
                dataset.data.station.model_north_vel_block_strain_rate.values,
                ctx.specs[name]["styles"]["colors"][idx],
                ctx.specs[name]["styles"]["line_width"][idx],
                dataset.name,
                ctx.velocity_scale,
            )
        )


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
