from fennil.app.io import Dataset
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=50,
    label="Res",
    icon="mdi-vector-difference",
    ui_type="VCheckbox",
    options=None,
    default=False,
    styles={
        "icon_color": "rgba(205, 0, 205, 0.78)",
        "colors": [
            (205, 0, 205, 200),
            (205, 0, 205, 200),
        ],
        "line_width": (1, 2),
    },
    multiple=False,
)


def builder(name: str, ctx: LayerContext): ...


def can_render(dataset: Dataset) -> bool:
    return dataset is not None
