import os
from pathlib import Path

import numpy as np

# Import pydeck and trame-deckgl
import pydeck as pdk
from trame.app import TrameApp
from trame.decorators import change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_deckgl.widgets import deckgl

from fennil.app.io import load_folder_data

from .components import folder_controls, velocity_scale_controls
from .components.file_browser_origin import FileBrowser
from .deck import build_layers_for_folder
from .state import AppState, FolderState


def _load_mapbox_token():
    token = os.getenv("FENNIL_MAP_BOX_TOKEN")
    if token:
        return token
    # Fallback: read from a local .env if present
    for parent in Path(__file__).resolve().parents:
        env_file = parent / ".env"
        if env_file.is_file():
            for line in env_file.read_text().splitlines():
                if line.strip().startswith("FENNIL_MAP_BOX_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return None


mapbox_access_token = _load_mapbox_token()
HAS_MAPBOX_TOKEN = bool(mapbox_access_token)


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

VELOCITY_SCALE_MIN = 1.0e-6


class FennilApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # --hot-reload arg optional logic
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        # Initialize state variables
        self.app_state = AppState(self.server)
        self.app_state.velocity_scale_display = self._format_velocity_scale(
            self.app_state.velocity_scale
        )

        # Data storage
        self.folder_1_data = None
        self.folder_2_data = None

        # Visibility controls for folders
        self.folder1 = FolderState(self.state, "folder1")
        self.folder2 = FolderState(self.state, "folder2")

        # File browser state
        data_root = Path(__file__).parent.parent.parent.parent / "data"
        self.file_browser = FileBrowser(self.state, data_root=data_root)
        self.file_browser.on_select = self._on_file_browser_select
        self.state.deckgl_tooltip = {
            "html": "{tooltip}",
            "style": {
                "backgroundColor": "rgba(0, 0, 0, 0.85)",
                "color": "white",
                "fontSize": "12px",
            },
        }

        # One-time registration guard
        self._ready_registered = False

        # build ui
        self._build_ui()

        # Initialize file browser listing
        self.file_browser.update_listing()
        self._ignore_velocity_display_change = False

    def _initialize_map(self, **kwargs):  # noqa: ARG002
        """Initialize the map with default view"""
        self.ctrl.deck_update(self._build_deck([]))

    def _on_file_browser_select(self, folder_number, folder_path):
        self._load_data(folder_number, folder_path=folder_path)

    def _load_data(self, folder_number, folder_path=None):
        """Load earthquake data from a folder"""
        if folder_path is None:
            stored = getattr(self.app_state, f"folder_{folder_number}_full_path", "")
            folder_path = Path(stored) if stored else None
        if folder_path is None:
            return
        folder_name = Path(folder_path)

        # Update folder display
        folder_path_var = f"folder_{folder_number}_path"
        setattr(self.app_state, folder_path_var, folder_name.name)
        setattr(
            self.app_state,
            f"folder_{folder_number}_full_path",
            str(folder_name.resolve()),
        )

        data = load_folder_data(folder_name)

        if folder_number == 1:
            self.folder_1_data = data
        else:
            self.folder_2_data = data

        # Update visualization
        self._update_layers()

        print(f"Loaded data from {folder_name}")  # noqa: T201

    @controller.set("load_folder_1")
    def load_folder_1(self):
        """Open file browser for folder 1"""
        existing = self.app_state.folder_1_full_path
        self.file_browser.open(1, existing)

    @controller.set("load_folder_2")
    def load_folder_2(self):
        """Open file browser for folder 2"""
        existing = self.app_state.folder_2_full_path
        self.file_browser.open(2, existing)

    def _update_layers(self):
        """Update DeckGL layers based on loaded data and visibility controls"""
        base_layers = []
        layers = []
        vector_layers = []

        # Process folder 1 data
        if self.folder_1_data is not None:
            tde_layers, folder_layers, folder_vectors = build_layers_for_folder(
                1, self.folder_1_data, self.folder1, self.app_state
            )
            base_layers.extend(tde_layers)
            layers.extend(folder_layers)
            vector_layers.extend(folder_vectors)

        # Process folder 2 data
        if self.folder_2_data is not None:
            tde_layers, folder_layers, folder_vectors = build_layers_for_folder(
                2, self.folder_2_data, self.folder2, self.app_state
            )
            base_layers.extend(tde_layers)
            layers.extend(folder_layers)
            vector_layers.extend(folder_vectors)

        self.ctrl.deck_update(self._build_deck(base_layers + layers + vector_layers))

    def _build_deck(self, layers):
        """Construct a Deck instance with current map settings and provided layers."""
        return pdk.Deck(
            map_provider="mapbox" if HAS_MAPBOX_TOKEN else "carto",
            map_style="mapbox://styles/mapbox/light-v9"
            if HAS_MAPBOX_TOKEN
            else pdk.map_styles.LIGHT,
            initial_view_state=pdk.ViewState(
                latitude=self.app_state.map_latitude,
                longitude=self.app_state.map_longitude,
                zoom=self.app_state.map_zoom,
                pitch=self.app_state.map_pitch,
                bearing=self.app_state.map_bearing,
            ),
            layers=layers,
        )

    @change("velocity_scale_display")
    def on_velocity_scale_display_change(self, velocity_scale_display, **kwargs):  # noqa: ARG002
        """Parse display text and update velocity scale."""
        if self._ignore_velocity_display_change:
            self._ignore_velocity_display_change = False
            return
        if velocity_scale_display in (None, ""):
            return
        try:
            value = float(velocity_scale_display)
        except (TypeError, ValueError):
            return
        if not np.isfinite(value):
            return
        value = max(value, VELOCITY_SCALE_MIN)
        if abs(value - self.app_state.velocity_scale) < 1.0e-12:
            return
        self.app_state.velocity_scale = value
        self._update_layers()

    def _set_velocity_scale(self, value):
        if value is None:
            return
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        if not np.isfinite(value):
            return
        self.app_state.velocity_scale = max(value, VELOCITY_SCALE_MIN)
        self._ignore_velocity_display_change = True
        self.app_state.velocity_scale_display = self._format_velocity_scale(
            self.app_state.velocity_scale
        )
        self._update_layers()

    @staticmethod
    def _format_velocity_scale(value):
        text = f"{value:.6f}"
        text = text.rstrip("0").rstrip(".")
        return text or "0"

    @controller.set("velocity_scale_reset")
    def velocity_scale_reset(self):
        self._set_velocity_scale(1.0)

    @controller.set("velocity_scale_fine_down")
    def velocity_scale_fine_down(self):
        self._set_velocity_scale(self.app_state.velocity_scale * 0.9)

    @controller.set("velocity_scale_fine_up")
    def velocity_scale_fine_up(self):
        self._set_velocity_scale(self.app_state.velocity_scale * 1.1)

    @controller.set("velocity_scale_mag_down")
    def velocity_scale_mag_down(self):
        self._set_velocity_scale(self.app_state.velocity_scale / 2.0)

    @controller.set("velocity_scale_mag_up")
    def velocity_scale_mag_up(self):
        self._set_velocity_scale(self.app_state.velocity_scale * 2.0)

    @change(
        "folder1_show_locs",
        "folder1_show_obs",
        "folder1_show_mod",
        "folder1_show_res",
        "folder1_show_rot",
        "folder1_show_seg",
        "folder1_show_tri",
        "folder1_show_str",
        "folder1_show_mog",
        "folder1_show_seg_color",
        "folder1_seg_slip_type",
        "folder1_show_tde",
        "folder1_tde_slip_type",
        "folder1_show_fault_proj",
        "folder2_show_locs",
        "folder2_show_obs",
        "folder2_show_mod",
        "folder2_show_res",
        "folder2_show_rot",
        "folder2_show_seg",
        "folder2_show_tri",
        "folder2_show_str",
        "folder2_show_mog",
        "folder2_show_seg_color",
        "folder2_seg_slip_type",
        "folder2_show_tde",
        "folder2_tde_slip_type",
        "folder2_show_fault_proj",
    )
    def on_visibility_change(self, **kwargs):  # noqa: ARG002
        """Update visualization when visibility controls change"""
        self._update_layers()

    def _build_ui(self, *args, **kwargs):  # noqa: ARG002
        with SinglePageLayout(self.server) as self.ui:
            # Toolbar
            self.ui.title.set_text("Earthquake Data Viewer")

            # Main content - recreating Panel GridSpec layout
            with self.ui.content:
                with self.app_state.provide_as("app"):
                    with v3.VContainer(
                        fluid=True,
                        classes="pa-0 fill-height",
                        style="max-height: 700px;",
                    ):
                        # Main grid: controls area + large map area
                        with v3.VRow(classes="fill-height", no_gutters=True):
                            # LEFT AREA - Controls (two columns + shared row)
                            with v3.VCol(cols=3, classes="pa-0 d-flex flex-column"):
                                with v3.VRow(classes="flex-grow-1", no_gutters=True):
                                    folder_controls(
                                        "folder1",
                                        self.load_folder_1,
                                        "app.folder_1_path",
                                    )
                                    folder_controls(
                                        "folder2",
                                        self.load_folder_2,
                                        "app.folder_2_path",
                                    )

                                v3.VDivider(classes="my-1")

                                # Shared controls row (full width of controls area)
                                with html.Div(classes="pa-2"):
                                    v3.VCheckbox(
                                        v_model="app.show_res_compare",
                                        label="res compare",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    velocity_scale_controls(
                                        "app.velocity_scale_display",
                                        self.velocity_scale_fine_down,
                                        self.velocity_scale_mag_down,
                                        self.velocity_scale_reset,
                                        self.velocity_scale_mag_up,
                                        self.velocity_scale_fine_up,
                                    )

                            # RIGHT LARGE AREA - Map and Colorbars
                            with v3.VCol(cols=9, classes="pa-0 d-flex flex-column"):
                                # Main map area (rows 0-8)
                                with v3.VCard(
                                    classes="flex-grow-1",
                                    style="min-height: 0; position: relative;",
                                ):
                                    # DeckGL Map
                                    deck_map = deckgl.Deck(
                                        mapbox_api_key=mapbox_access_token
                                        if HAS_MAPBOX_TOKEN
                                        else "",
                                        tooltip=("deckgl_tooltip", None),
                                        style="width: 100%; height: 100%;",
                                        classes="fill-height",
                                    )
                                    self.ctrl.deck_update = deck_map.update

                                    # Initialize map after UI is built
                                    if not self._ready_registered:
                                        self.server.controller.on_server_ready.add(
                                            self._initialize_map
                                        )
                                        self._ready_registered = True

                                # Colorbar area (row 8)
                                with v3.VCard(
                                    classes=(
                                        "pa-2 d-flex justify-space-around align-center"
                                    ),
                                    height="50",
                                    flat=True,
                                ):
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

                self.file_browser.ui()
