from .faults import fault_line_layers
from .styles import dataset_float_value, dataset_value, normalize_dataset_values

# Keep base fault colors stable and distinct per dataset.
FAULT_LINES_STYLE_KEY = "fault_lines"
FAULT_LINE_COLORS_DEFAULT = [
    (0, 0, 255, 255),
    (0, 128, 0, 255),
]
FAULT_LINE_WIDTHS_DEFAULT = (1, 1)


def fault_line_style_spec():
    return {
        "priority": 25,
        "label": "Fault lines",
        "icon": "mdi-map-marker-path",
        "type": "VCheckbox",
        "styles": {
            "colors": [list(color) for color in FAULT_LINE_COLORS_DEFAULT],
            "line_width": list(FAULT_LINE_WIDTHS_DEFAULT),
        },
        "options": None,
        "multiple": False,
    }


def build_fault_lines(ctx):
    styles = ctx.specs.get(FAULT_LINES_STYLE_KEY, {}).get("styles", {})
    line_colors = normalize_dataset_values(
        styles.get("colors"), FAULT_LINE_COLORS_DEFAULT
    )
    line_widths = normalize_dataset_values(
        styles.get("line_width"),
        FAULT_LINE_WIDTHS_DEFAULT,
    )

    for idx, dataset in enumerate(ctx.datasets):
        if not dataset.enabled or dataset.data is None:
            continue

        folder_number = idx + 1
        seg_tooltip_enabled = True
        color = dataset_value(line_colors, idx)
        width = dataset_float_value(
            line_widths,
            idx,
            dataset_value(FAULT_LINE_WIDTHS_DEFAULT, idx),
        )
        fault_layers, _ = fault_line_layers(
            folder_number,
            dataset.data.segment,
            seg_tooltip_enabled,
            color,
            width,
        )
        ctx.layers.extend(fault_layers)
