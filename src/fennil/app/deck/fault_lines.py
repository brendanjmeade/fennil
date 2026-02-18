from fennil.app.deck.faults import fault_line_layers

# Keep base fault colors stable and distinct per dataset.
FAULT_LINE_COLORS = [
    (0, 0, 255, 255),
    (0, 128, 0, 255),
]
FAULT_LINE_WIDTHS = (1, 1)


def build_fault_lines(ctx):
    for idx, dataset in enumerate(ctx.datasets):
        if not dataset.enabled or dataset.data is None:
            continue

        folder_number = idx + 1
        seg_tooltip_enabled = not idx
        fault_layers, _ = fault_line_layers(
            folder_number,
            dataset.data.segment,
            seg_tooltip_enabled,
            FAULT_LINE_COLORS[idx],
            FAULT_LINE_WIDTHS[idx],
        )
        ctx.layers.extend(fault_layers)
