from pathlib import Path

from trame.widgets import dataclass, html
from trame.widgets import vuetify3 as v3
from trame_dataclass.core import StateDataModel

from fennil.app.io import is_valid_data_folder

FILE_BROWSER_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": False},
    {"title": "Type", "align": "start", "key": "type", "sortable": False},
]


class FileBrowserState(StateDataModel):
    show: bool = False
    current: str = "/"
    listing: list
    active: int = -1
    error: str | None
    headers: list = FILE_BROWSER_HEADERS


class FileBrowser(dataclass.Provider):
    def __init__(self, current_directory=None, on_open=None, **kwargs):
        if current_directory is None:
            current_directory = Path.cwd()
        self._on_open = on_open
        self._state = None
        super().__init__(name="browser", **kwargs)
        self._state = FileBrowserState(self.server, current=str(current_directory))
        self.instance = self._state._id
        self.update_listing()

        with (
            self,
            v3.VDialog(
                v_model="browser.show",
                max_width="900",
                persistent=True,
            ),
        ):
            with v3.VCard(title="Select data folder", rounded="lg"):
                with v3.VCardText():
                    with v3.VRow(dense=True, classes="pb-1 align-center"):
                        v3.VBtn(
                            icon="mdi-home",
                            variant="text",
                            size="small",
                            click=self.go_home,
                        )
                        v3.VBtn(
                            icon="mdi-folder-upload-outline",
                            variant="text",
                            size="small",
                            click=self.go_parent,
                        )
                        v3.VTextField(
                            v_model="browser.current",
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            readonly=True,
                            classes="ml-2 flex-grow-1",
                        )
                    with v3.VDataTable(
                        density="compact",
                        fixed_header=True,
                        headers=["browser.header"],
                        items=["browser.listing"],
                        height="50vh",
                        style="user-select: none; cursor: pointer;",
                        items_per_page=-1,
                    ):
                        v3.Template(v_slot_bottom=True)
                        with v3.Template(v_slot_item="{ item }"):
                            with v3.VDataTableRow(
                                item=["item"],
                                click=(self.select_entry, "[item]"),
                                dblclick=(self.open_entry, "[item]"),
                                classes=[
                                    "{ 'bg-grey-lighten-3': item.index === browser.active }"
                                ],
                            ):
                                with v3.Template(raw_attrs=["v-slot:item.name"]):
                                    with html.Div(classes="d-flex align-center"):
                                        v3.VIcon(
                                            "{{ item.icon }}",
                                            size="small",
                                            classes="mr-2",
                                        )
                                        html.Div("{{ item.name }}")
                                with v3.Template(raw_attrs=["v-slot:item.type"]):
                                    html.Div("{{ item.type }}")

                with v3.VCardActions(classes="pa-3"):
                    html.Div(
                        "{{ browser.error }}",
                        v_if="browser.error",
                        classes="text-error text-caption",
                    )
                    v3.VSpacer()
                    v3.VBtn(
                        text="Cancel",
                        variant="flat",
                        click="browser.show = false",
                    )
                    v3.VBtn(
                        text="Select folder",
                        color="primary",
                        variant="flat",
                        click=self.select_folder,
                    )

    def update_listing(self):
        current = Path(self._state.current)
        if not current.exists():
            current = Path.home()
            self._state.current = str(current.resolve())

        entries = []
        for entry in current.iterdir():
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_dir():
                entries.append(
                    {
                        "name": name,
                        "type": "directory",
                        "icon": "mdi-folder",
                    }
                )
            elif entry.is_file():
                entries.append(
                    {
                        "name": name,
                        "type": "file",
                        "icon": "mdi-file-document-outline",
                    }
                )
        entries.sort(key=lambda item: (item["type"] != "directory", item["name"]))
        listing = [{**item, "index": idx} for idx, item in enumerate(entries)]
        self._state.listing = listing
        self._state.active = -1

    def select_entry(self, entry):
        self._state.active = entry.get("index", -1) if entry else -1

    def open_entry(self, entry):
        if not entry or entry.get("type") != "directory":
            return
        current = Path(self._state.current)
        next_path = (current / entry.get("name")).resolve()

        if is_valid_data_folder(next_path):
            self._state.error = None
            self._state.show = False
            if self._on_open:
                self._on_open(next_path)
            return

        self._state.current = str(next_path)
        self.update_listing()

    def go_home(self):
        self._state.current = str(Path.home().resolve())
        self.update_listing()

    def go_parent(self):
        current = Path(self._state.current)
        parent = current.parent if current.parent != current else current
        self._state.current = str(parent.resolve())
        self.update_listing()

    def open(self, existing_path=None):
        if existing_path:
            self._state.current = str(Path(existing_path).resolve())

        self._state.show = True
        self._state.error = None
        self.update_listing()

    def select_folder(self):
        current = Path(self._state.current)
        folder_path = current
        active_idx = self._state.active
        listing = self._state.listing
        if active_idx is not None and active_idx >= 0:
            if active_idx >= len(listing):
                active_idx = -1
            else:
                entry = listing[active_idx]
                if entry.get("type") == "directory":
                    folder_path = (current / entry.get("name")).resolve()
        if not is_valid_data_folder(folder_path):
            self._state.error = "Selected folder is missing required model_*.csv files."
            return
        self._state.error = None
        self._state.show = False
        if self._on_open:
            self._on_open(folder_path)
