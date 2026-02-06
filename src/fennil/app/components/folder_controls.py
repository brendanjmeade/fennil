from trame.widgets import html, vuetify3


def folder_controls(prefix, load_callback, folder_path_key):
    with vuetify3.VCol(
        cols=6,
        classes="pa-2 d-flex flex-column",
        style="overflow-y: auto;",
    ):
        vuetify3.VBtn(
            "load",
            click=load_callback,
            color="success",
            block=True,
            size="small",
        )
        html.Div(
            f"{{{{ {folder_path_key} }}}}",
            classes="text-caption mt-1 mb-2",
            style="font-size: 0.7rem;",
        )

        for key, label in [
            ("show_locs", "locs"),
            ("show_obs", "obs"),
            ("show_mod", "mod"),
            ("show_res", "res"),
            ("show_rot", "rot"),
            ("show_seg", "seg"),
            ("show_tri", "tri"),
            ("show_str", "str"),
            ("show_mog", "mog"),
            ("show_res_mag", "res mag"),
        ]:
            vuetify3.VCheckbox(
                v_model=f"{prefix}_{key}",
                label=label,
                hide_details=True,
                density="compact",
            )

        vuetify3.VDivider(classes="my-2")

        vuetify3.VCheckbox(
            v_model=f"{prefix}_show_seg_color",
            label="slip",
            hide_details=True,
            density="compact",
        )
        with vuetify3.VBtnToggle(
            v_model=f"{prefix}_seg_slip_type",
            mandatory=True,
            density="compact",
            divided=True,
        ):
            vuetify3.VBtn("ss", value="ss", size="x-small")
            vuetify3.VBtn("ds", value="ds", size="x-small")

        vuetify3.VCheckbox(
            v_model=f"{prefix}_show_tde",
            label="tde",
            hide_details=True,
            density="compact",
        )
        with vuetify3.VBtnToggle(
            v_model=f"{prefix}_tde_slip_type",
            mandatory=True,
            density="compact",
            divided=True,
        ):
            vuetify3.VBtn("ss", value="ss", size="x-small")
            vuetify3.VBtn("ds", value="ds", size="x-small")

        vuetify3.VCheckbox(
            v_model=f"{prefix}_show_fault_proj",
            label="fault proj",
            hide_details=True,
            density="compact",
        )
