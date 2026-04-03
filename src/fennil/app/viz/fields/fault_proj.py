from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext
from fennil.app.viz.faults import fault_projection_layers
from fennil.app.viz.styles import dataset_value, normalize_dataset_values

FAULT_PROJ_FILL_DEFAULT = [
    (173, 216, 230, 77),
    (144, 238, 144, 77),
]
FAULT_PROJ_LINE_DEFAULT = [
    (0, 0, 255, 255),
    (0, 128, 0, 255),
]

SPEC = FieldSpec(
    priority=30,
    label="Fault Proj",
    icon="mdi-bandage",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "fill": FAULT_PROJ_FILL_DEFAULT,
    },
)


def builder(name: str, ctx: LayerContext):
    if ctx.skip(name):
        return

    styles = ctx.specs[name].get("styles", {})
    fill_values = normalize_dataset_values(styles.get("fill"), FAULT_PROJ_FILL_DEFAULT)
    line_values = normalize_dataset_values(styles.get("line"), FAULT_PROJ_LINE_DEFAULT)

    for idx, dataset in ctx.enabled_datasets(name):
        ctx.layers.extend(
            fault_projection_layers(
                dataset.name,
                dataset.data.fault_proj_df,
                dataset_value(fill_values, idx),
                dataset_value(line_values, idx),
            )
        )


def can_render(dataset: Dataset) -> bool:
    if dataset is None:
        return False

    return dataset.fault_proj_available
