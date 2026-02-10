from pathlib import Path

from trame.widgets import html, vuetify3

from ..utils import is_valid_data_folder

FILE_BROWSER_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": False},
    {"title": "Type", "align": "start", "key": "type", "sortable": False},
]


class FileBrowser:
    def __init__(self, state, data_root=None, prefix="file_browser"):
        self._state = state
        self._prefix = prefix
        self._data_root = (
            Path(data_root).resolve() if data_root else Path.home().resolve()
        )
        self.on_select = None

        self._state.setdefault(self.key("show"), False)
        self._state.setdefault(self.key("target"), 1)
        self._state.setdefault(self.key("current"), str(self._data_root))
        self._state.setdefault(self.key("listing"), [])
        self._state.setdefault(self.key("active"), -1)
        self._state.setdefault(self.key("error"), "")
        self._state.setdefault(self.key("headers"), FILE_BROWSER_HEADERS)

    def key(self, name):
        return f"{self._prefix}_{name}"

    def get(self, name):
        return self._state[self.key(name)]

    def set(self, name, value):
        self._state[self.key(name)] = value

    def update_listing(self):
        current = Path(self.get("current"))
        if not current.exists():
            current = Path.home()
            self.set("current", str(current.resolve()))
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
        with self._state:
            self.set("listing", listing)
            self.set("active", -1)

    def select_entry(self, entry):
        self.set("active", entry.get("index", -1) if entry else -1)

    def open_entry(self, entry):
        if not entry or entry.get("type") != "directory":
            return
        current = Path(self.get("current"))
        next_path = (current / entry.get("name")).resolve()
        self.set("current", str(next_path))
        self.update_listing()

    def go_home(self):
        self.set("current", str(Path.home().resolve()))
        self.update_listing()

    def go_parent(self):
        current = Path(self.get("current"))
        parent = current.parent if current.parent != current else current
        self.set("current", str(parent.resolve()))
        self.update_listing()

    def open(self, folder_number, existing_path=""):
        self.set("target", folder_number)
        if existing_path:
            self.set("current", str(Path(existing_path).resolve()))
        self.set("show", True)
        self.set("error", "")
        self.update_listing()

    def select_folder(self):
        current = Path(self.get("current"))
        folder_path = current
        active_idx = self.get("active")
        listing = self.get("listing")
        if active_idx is not None and active_idx >= 0:
            if active_idx >= len(listing):
                active_idx = -1
            else:
                entry = listing[active_idx]
                if entry.get("type") == "directory":
                    folder_path = (current / entry.get("name")).resolve()
        if not is_valid_data_folder(folder_path):
            self.set(
                "error",
                "Selected folder is missing required model_*.csv files.",
            )
            return
        self.set("error", "")
        self.set("show", False)
        target = int(self.get("target"))
        if self.on_select:
            self.on_select(target, folder_path)

    def ui(self):
        with vuetify3.VDialog(
            v_model=(self.key("show"), False),
            max_width="900",
            persistent=True,
        ):
            with vuetify3.VCard(title="Select data folder", rounded="lg"):
                with vuetify3.VCardText():
                    with vuetify3.VRow(dense=True, classes="pb-1 align-center"):
                        vuetify3.VBtn(
                            icon="mdi-home",
                            variant="text",
                            size="small",
                            click=self.go_home,
                        )
                        vuetify3.VBtn(
                            icon="mdi-folder-upload-outline",
                            variant="text",
                            size="small",
                            click=self.go_parent,
                        )
                        vuetify3.VTextField(
                            v_model=(self.key("current"), ""),
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            readonly=True,
                            classes="ml-2 flex-grow-1",
                        )
                    with vuetify3.VDataTable(
                        density="compact",
                        fixed_header=True,
                        headers=(self.key("headers"), FILE_BROWSER_HEADERS),
                        items=(self.key("listing"), []),
                        height="50vh",
                        style="user-select: none; cursor: pointer;",
                        items_per_page=-1,
                    ):
                        vuetify3.Template(raw_attrs=["v-slot:bottom"])
                        with vuetify3.Template(raw_attrs=['v-slot:item="{ item }"']):
                            with vuetify3.VDataTableRow(
                                item=("item",),
                                click=(self.select_entry, "[item]"),
                                dblclick=(self.open_entry, "[item]"),
                                classes=(
                                    f"{{ 'bg-grey-lighten-3': item.index === {self.key('active')} }}",
                                ),
                            ):
                                with vuetify3.Template(raw_attrs=["v-slot:item.name"]):
                                    with html.Div(classes="d-flex align-center"):
                                        vuetify3.VIcon(
                                            "{{ item.icon }}",
                                            size="small",
                                            classes="mr-2",
                                        )
                                        html.Div("{{ item.name }}")
                                with vuetify3.Template(raw_attrs=["v-slot:item.type"]):
                                    html.Div("{{ item.type }}")

                with vuetify3.VCardActions(classes="pa-3"):
                    html.Div(
                        f"{{{{ {self.key('error')} }}}}",
                        v_if=self.key("error"),
                        classes="text-error text-caption",
                    )
                    vuetify3.VSpacer()
                    vuetify3.VBtn(
                        text="Cancel",
                        variant="flat",
                        click=f"{self.key('show')}=false",
                    )
                    vuetify3.VBtn(
                        text="Select folder",
                        color="primary",
                        variant="flat",
                        click=self.select_folder,
                    )
