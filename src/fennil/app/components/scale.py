from trame.widgets import vuetify3 as v3

v3.enable_lab()


class Scale(v3.VCol):
    def __init__(self, name="scale", **kwargs):
        self._name = name
        super().__init__(**kwargs)

        with self:
            with v3.VRow(dense=True, no_gutter=True):
                with v3.VCol():
                    v3.VBtn(
                        "50%",
                        click=(self.scale, "[0.5]"),
                        size="small",
                        variant="outlined",
                        block=True,
                    )
                with v3.VCol():
                    v3.VBtn(
                        "90%",
                        click=(self.scale, "[0.9]"),
                        size="small",
                        variant="outlined",
                        block=True,
                    )
                with v3.VCol():
                    v3.VBtn(
                        "110%",
                        click=(self.scale, "[1.1]"),
                        size="small",
                        variant="outlined",
                        block=True,
                    )
                with v3.VCol():
                    v3.VBtn(
                        "200%",
                        click=(self.scale, "[2]"),
                        size="small",
                        variant="outlined",
                        block=True,
                    )
            with v3.VRow():
                with v3.VCol(classes="pt-0"):
                    v3.VNumberInput(
                        click_prepend=self.reset,
                        prepend_icon="mdi-vector-line",
                        v_model=(name, 1),
                        precision=6,
                        min=[0.0001],
                        max=[10000],
                        step=[0.01],
                        density="compact",
                        hide_details=True,
                        variant="outlined",
                        control_variant="split",
                    )

    def scale(self, value):
        self.state[self._name] *= value

    def reset(self):
        self.state[self._name] = 1
