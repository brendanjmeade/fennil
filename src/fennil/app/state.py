from typing import ClassVar


class FolderState:
    DEFAULTS: ClassVar[dict[str, object]] = {
        "show_locs": False,
        "show_obs": False,
        "show_mod": False,
        "show_res": False,
        "show_rot": False,
        "show_seg": False,
        "show_tri": False,
        "show_str": False,
        "show_mog": False,
        "show_res_mag": False,
        "show_seg_color": False,
        "seg_slip_type": "ss",
        "show_tde": False,
        "tde_slip_type": "ss",
        "show_fault_proj": False,
    }

    def __init__(self, state, prefix):
        self._state = state
        self._prefix = prefix
        for key, value in self.DEFAULTS.items():
            self._state.setdefault(self.key(key), value)

    def key(self, name):
        return f"{self._prefix}_{name}"

    def get(self, name, default=None):
        return self._state.get(self.key(name), default)

    def __getitem__(self, name):
        return self._state[self.key(name)]

    def __setitem__(self, name, value):
        self._state[self.key(name)] = value
