import io
import base64

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np

from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate

from kinetics import ammonia_production_rate, simulate_ammonia_curve, health_status

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H2("AquaKinetics", className="app-title"),
        html.P("Aquaponic Biofilter Health Calculator", className="app-subtitle"),
    ]),

    html.Div([
        # ── Sidebar ──────────────────────────────────────────────────────────
        html.Div([
            html.Label("Fish Tank Volume (litres)"),
            dcc.Input(id="volume",      type="number", value=600,  min=10,  max=50000, step=10),

            html.Label("Daily Feed Amount (grams)"),
            dcc.Input(id="feed",        type="number", value=80,   min=1,   max=10000, step=5),

            html.Label("Water Temperature (°C)"),
            dcc.Input(id="temperature", type="number", value=25,   min=5,   max=35,    step=0.5),

            html.Label("pH"),
            dcc.Input(id="ph",          type="number", value=7.5,  min=5,   max=9,     step=0.1),

            html.Button("Calculate", id="calculate-btn", n_clicks=0, className="btn-primary"),
        ], className="sidebar"),

        # ── Main panel ────────────────────────────────────────────────────────
        html.Div([
            html.H4("Biofilter Health Status"),
            html.Div(id="status-badge"),
            html.P(id="status-msg"),

            html.Hr(),

            html.H4("72-Hour Ammonia Forecast (mg/L NH₃-N)"),
            html.Img(id="ammonia-plot", style={"width": "100%"}),

            html.Hr(),

            html.Div([
                html.Div([
                    html.H5("Production Rate"),
                    html.Pre(id="prod-rate"),
                ], style={"flex": "1"}),
                html.Div([
                    html.H5("Peak Ammonia (72 hr)"),
                    html.Pre(id="peak-nh3"),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "20px"}),
        ], className="main-panel"),
    ], className="layout"),
])


def _render_plot(curve, color):
    """Render the 72-hr ammonia curve with Matplotlib; return a base64 data URI."""
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor="#f4f7fb")
    ax.set_facecolor("#f4f7fb")

    ax.plot(curve["hour"], curve["nh3_mg_l"],
            color=color, linewidth=2.5, label=r"NH$_3$-N")
    ax.axhline(1.0, linestyle="--", color="#f39c12", linewidth=1.2,
               label="Warning (1 mg/L)")
    ax.axhline(3.0, linestyle="--", color="#e74c3c", linewidth=1.2,
               label="Critical (3 mg/L)")

    ax.set_xlabel("Time (hours)")
    ax.set_ylabel(r"NH$_3$-N  (mg/L)")
    ax.set_ylim(bottom=0, top=max(float(curve["nh3_mg_l"].max()), 3.5) * 1.1)
    ax.legend(loc="upper right", frameon=False, fontsize=8.5)
    ax.grid(color="#d9e3f0", linestyle="-", linewidth=0.8)
    ax.yaxis.set_tick_params(labelleft=True)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"


@app.callback(
    Output("status-badge", "children"),
    Output("status-badge", "style"),
    Output("status-msg",   "children"),
    Output("ammonia-plot", "src"),
    Output("prod-rate",    "children"),
    Output("peak-nh3",     "children"),
    Input("calculate-btn", "n_clicks"),
    State("volume",        "value"),
    State("feed",          "value"),
    State("temperature",   "value"),
    State("ph",            "value"),
)
def update(n_clicks, volume, feed, temperature, ph):
    if any(v is None for v in (volume, feed, temperature, ph)):
        raise PreventUpdate

    curve  = simulate_ammonia_curve(feed, volume, temperature, ph)
    status = health_status(float(curve["nh3_mg_l"][-1]))

    badge_style = {
        "display":         "inline-block",
        "padding":         "10px 24px",
        "borderRadius":    "8px",
        "fontSize":        "1.4em",
        "fontWeight":      "bold",
        "color":           "#fff",
        "backgroundColor": status["color"],
    }

    prod_rate = ammonia_production_rate(feed, volume)
    peak_nh3  = float(curve["nh3_mg_l"].max())
    plot_src  = _render_plot(curve, status["color"])

    return (
        status["status"],
        badge_style,
        status["message"],
        plot_src,
        f"{prod_rate:.4f} mg NH3-N / L / hr",
        f"{peak_nh3:.3f} mg/L",
    )


if __name__ == "__main__":
    app.run(debug=True)
