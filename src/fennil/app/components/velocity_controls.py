from trame.widgets import html, vuetify3


def velocity_scale_controls(
    display_model,
    fine_down,
    mag_down,
    reset,
    mag_up,
    fine_up,
):
    html.Div(
        "vel scale",
        classes="text-caption mt-1",
        style="font-size: 0.7rem;",
    )
    with html.Div(classes="d-flex flex-wrap ga-1 mt-1"):
        vuetify3.VBtn(
            "90%",
            click=fine_down,
            size="x-small",
            variant="outlined",
        )
        vuetify3.VBtn(
            "/2",
            click=mag_down,
            size="x-small",
            variant="outlined",
        )
        vuetify3.VBtn(
            "1:1",
            click=reset,
            size="x-small",
            variant="outlined",
        )
        vuetify3.VBtn(
            "x2",
            click=mag_up,
            size="x-small",
            variant="outlined",
        )
        vuetify3.VBtn(
            "110%",
            click=fine_up,
            size="x-small",
            variant="outlined",
        )
    vuetify3.VTextField(
        v_model=(display_model, "1"),
        label="scale",
        type="text",
        inputmode="decimal",
        density="compact",
        hide_details=True,
        variant="outlined",
        classes="mt-1",
    )
