from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import deckgl, html
from trame.widgets import vuetify3 as v3
from trame_dataclass.core import get_instance

from fennil.app.io import load_folder_data

from .components import FileBrowser, Scale
from .deck import build_deck, build_layers_dataset, mapbox
from .deck.styles import TYPE_COLORS
from .registry import FIELD_REGISTRY
from .state import DatasetVisualization, MapSettings
from .viz import load_all_viz


class FennilApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # --hot-reload for dev UI faster
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        # Load all available viz
        load_all_viz()

        # Only 2 datasets max
        self._datasets = [
            DatasetVisualization(self.server),
            DatasetVisualization(self.server),
        ]
        self.map_params = MapSettings(self.server)
        for viz_config in self._datasets:
            viz_config.watch(["fields", "enabled"], self._update_layers)
        self.state.field_specs = FIELD_REGISTRY.export_specs()

        # build ui
        self._build_ui()

    @change("scale")
    def _update_layers(self, *_, **__):
        """Update DeckGL layers based on loaded data and visibility controls"""
        base_layers = []
        all_layers = []
        vector_layers = []

        # Process all datasets
        for ds_idx, dataset_config in enumerate(self._datasets):
            tde, layers, vectors = build_layers_dataset(
                dataset_config, ds_idx, self.state.scale
            )
            base_layers.extend(tde)
            all_layers.extend(layers)
            vector_layers.extend(vectors)

        with self.state:
            self.ctrl.deck_update(
                build_deck(base_layers + all_layers + vector_layers, self.map_params)
            )

    def load_dataset(self, directory_path):
        self.state.compact_drawer = False  # Always open when new data
        dataset = load_folder_data(directory_path)
        if self._datasets[0].enabled:
            self._datasets[1].attach_data(directory_path, dataset, TYPE_COLORS[2])
        else:
            self._datasets[0].attach_data(directory_path, dataset, TYPE_COLORS[1])

    def reset_dataset(self, index):
        self._datasets[index].clear()

    def update_dataset_config(self, id, name, value):
        """Keep server in sync with client reactive nested structure"""
        state = get_instance(id)
        state.fields = {**state.fields, name: value}

    def _build_ui(self, **_):
        self.state.trame__title = "Earthquake Data Viewer"
        with VAppLayout(self.server, fill_height=True) as self.ui:
            # -----------------------------------------------------------------
            # Dialogs
            # -----------------------------------------------------------------

            FileBrowser(ctx_name="file_browser", on_open=self.load_dataset)

            # -----------------------------------------------------------------
            # Drawer
            # -----------------------------------------------------------------

            with v3.VNavigationDrawer(
                permanent=True,
                rail=("compact_drawer", False),
                width=300,
            ):
                with v3.Template(v_slot_prepend=True):
                    with v3.VListItem(
                        title=["compact_drawer ? null : 'Earthquake Viewer'"],
                        click="compact_drawer = !compact_drawer",
                        prepend_icon="mdi-map",
                    ):
                        v3.VProgressCircular(
                            color="primary",
                            indeterminate=True,
                            v_show="trame__busy",
                            v_if="compact_drawer",
                            style="position: absolute !important;left: 50%;top: 50%; transform: translate(-50%, -50%);",
                        )
                        v3.VProgressLinear(
                            v_else=True,
                            color="primary",
                            indeterminate=True,
                            v_show="trame__busy",
                            absolute=True,
                            style="top:90%;width:100%;",
                        )
                    v3.VListItem(
                        title=["compact_drawer ? null : 'Load Dataset'"],
                        click=self.ctx.file_browser.open,
                        prepend_icon="mdi-database-plus",
                    )

                    with self._datasets[0].provide_as("first"):
                        with self._datasets[1].provide_as("second"):
                            with v3.VTable(
                                v_if="!compact_drawer && first.enabled",
                                density="compact",
                                striped="even",
                                fixed_header=True,
                                height="calc(100vh - 104px - 40px - 40px)",
                            ):
                                with html.Thead():
                                    with html.Tr():
                                        html.Th("Field", classes="text-center")
                                        with html.Th():
                                            with html.Div(
                                                classes="d-flex align-center"
                                            ):
                                                v3.VBtn(
                                                    icon="mdi-trash-can-outline",
                                                    density="compact",
                                                    hide_details=True,
                                                    size="small",
                                                    variant="plain",
                                                    click=(self.reset_dataset, "[0]"),
                                                )
                                                html.Div("{{ first.name }}")
                                        with html.Th(v_if="second.enabled"):
                                            with html.Div(
                                                classes="d-flex align-center"
                                            ):
                                                v3.VBtn(
                                                    icon="mdi-trash-can-outline",
                                                    density="compact",
                                                    hide_details=True,
                                                    size="small",
                                                    variant="plain",
                                                    click=(self.reset_dataset, "[1]"),
                                                )
                                                html.Div("{{ second.name }}")
                                with html.Tbody():
                                    with html.Tr(
                                        v_for="name, i in first.available_fields",
                                        key="i",
                                    ):
                                        with html.Td():
                                            with html.Div(
                                                classes="d-flex align-center",
                                                v_if="field_specs[name]",
                                            ):
                                                v3.VIcon(
                                                    classes="mr-1",
                                                    icon=["field_specs[name]?.icon"],
                                                    color=[
                                                        "`rgba(${(field_specs[name].color || first.colors[field_specs[name].color_key])[0]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[1]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[2]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[3] / 255})`"
                                                    ],
                                                )
                                                v3.VLabel(
                                                    "{{ name }}",
                                                    classes="text-capitalize",
                                                )
                                        with html.Td(
                                            v_for="data, i in [first, second]",
                                            key="i",
                                            v_show="data.enabled",
                                        ):
                                            with html.Div(
                                                classes="d-flex align-center justify-center",
                                                v_if="data.enabled",
                                            ):
                                                v3.VCheckbox(
                                                    v_if="field_specs[name]?.type === 'VCheckbox'",
                                                    v_model="data.fields[name]",
                                                    hide_details=True,
                                                    density="compact",
                                                    update_modelValue=(
                                                        self.update_dataset_config,
                                                        "[data._id, name, data.fields[name]]",
                                                    ),
                                                )
                                                with v3.VBtnToggle(
                                                    v_if="field_specs[name]?.type === 'VBtnToggle'",
                                                    v_model="data.fields[name]",
                                                    hide_details=True,
                                                    density="compact",
                                                    rounded="md",
                                                    border=True,
                                                    divided=True,
                                                    style="height: 24px;",
                                                    update_modelValue=(
                                                        self.update_dataset_config,
                                                        "[data._id, name, data.fields[name]]",
                                                    ),
                                                ):
                                                    v3.VBtn(
                                                        v_for="props, i in field_specs[name].options",
                                                        key="i",
                                                        size=24,
                                                        density="compact",
                                                        hide_details=True,
                                                        v_bind="props",
                                                    )

                            with html.Div(
                                v_if="compact_drawer && first.enabled",
                                classes="pa-0 d-flex flex-column align-center",
                            ):
                                v3.VChip(
                                    "{{name}} {{ typeof first.fields[name] === 'string' ? first.fields[name].toUpperCase() : null }}",
                                    label=True,
                                    classes="text-capitalize my-1",
                                    v_for="name, i in first.available_fields",
                                    key="i",
                                    v_show="first.fields[name]",
                                    size="x-small",
                                    color=[
                                        "`rgba(${(field_specs[name].color || first.colors[field_specs[name].color_key])[0]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[1]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[2]}, ${(field_specs[name].color || first.colors[field_specs[name].color_key])[3] / 255})`"
                                    ],
                                )

                with v3.Template(v_slot_append=True):
                    Scale(v_if="!compact_drawer")
                    html.Div(
                        "x {{ scale }}",
                        v_else=True,
                        classes="text-center text-caption",
                    )

            # -----------------------------------------------------------------
            # Map
            # -----------------------------------------------------------------

            with v3.VMain():
                deck_map = deckgl.Deck(
                    mapbox_api_key=mapbox.TOKEN,
                    tooltip=(
                        "deckgl_tooltip",
                        {
                            "html": "{tooltip}",
                            "style": {
                                "backgroundColor": "rgba(0, 0, 0, 0.85)",
                                "color": "white",
                                "fontSize": "12px",
                            },
                        },
                    ),
                    style="width: 100%; height: 100%;",
                    classes="fill-height",
                )
                self.ctrl.deck_update = deck_map.update
                self.ctrl.deck_update(build_deck([], self.map_params))

            # -----------------------------------------------------------------
            # Footer
            # -----------------------------------------------------------------

            with v3.VFooter(app=True, height=35):
                # Slip rate colorbar placeholder
                html.Div(
                    "Slip rate (mm/yr): -100 ←→ +100",
                    style="font-size: 0.75rem; color: #666;",
                )
                # Residual magnitude colorbar placeholder
                html.Div(
                    "Resid. mag. (mm/yr): 0 → 5",
                    style="font-size: 0.75rem; color: #666;",
                )
                # Residual diff colorbar placeholder
                html.Div(
                    "Resid. diff. (mm/yr): -5 ←→ +5",
                    style="font-size: 0.75rem; color: #666;",
                )
                if self.server.hot_reload:
                    v3.VSpacer()
                    v3.VBtn(
                        icon="mdi-refresh",
                        click=self.ctrl.on_server_reload,
                        density="compact",
                        classes="rounded",
                        flat=True,
                    )
