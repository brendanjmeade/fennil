from fennil.app.deck.faults import fault_projection_layers
from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=30,
    label="Fault Proj",
    icon="mdi-bandage",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "colors": [
            (128, 128, 128, 255),
            (128, 128, 128, 255),
        ],
        "line_width": (1, 2),
        "fill": [
            (173, 216, 230, 77),
            (144, 238, 144, 77),
        ],
        "line": [
            (0, 0, 255, 255),
            (0, 128, 0, 255),
        ],
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    for idx, dataset in ctx.enabled_datasets(name):
        ctx.layers.extend(
            fault_projection_layers(
                dataset.name,
                dataset.data.fault_proj_df,
                ctx.specs[name]["styles"]["fill"][idx],
                ctx.specs[name]["styles"]["line"][idx],
            )
        )


def can_render(dataset: Dataset) -> bool:
    if dataset is None:
        return False

    return dataset.fault_proj_available
