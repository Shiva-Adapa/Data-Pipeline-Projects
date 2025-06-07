import dash
from dash import html, dcc, Input, Output, State, callback_context
import requests
import plotly.graph_objs as go
import pandas as pd
import dash_bootstrap_components as dbc
import os
from datetime import datetime, timedelta

# --- City Data ---
CITIES = {
    "NEW YORK": (40.7128, -74.0060),
    "LONDON": (51.5072, -0.1276),
    "TOKYO": (35.6895, 139.6917),
    "BERLIN": (52.5200, 13.4050),
    "SYDNEY": (-33.8688, 151.2093),
    "MUMBAI": (19.0760, 72.8777),
    "SAO PAULO": (-23.5505, -46.6333),
    "CAPE TOWN": (-33.9249, 18.4241),
}

RAW_DATA_DIR = "raw_weather_data"
CLEAN_DATA_DIR = "cleaned_weather_data"
REPORT_DIR = "weather_reports"
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Weather Dashboard"

# --- Layout ---
app.layout = dbc.Container([
    html.H2("🌤️ Be-Weather-Ready 🌤️", className="text-center my-4"),
    html.H5("-with Daily Weather Forecast Board", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Select City"),
            dcc.Dropdown(
                id='city-dropdown',
                options=[{"label": city.title(), "value": city} for city in CITIES],
                value="NEW YORK",
                clearable=False
            ),
            html.Br(),

            html.Label("Select Metrics to Display"),
            dcc.RadioItems(
                id='detailed-feature-radio',
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Temperature", "value": "temperature"},
                    {"label": "Wind Speed", "value": "wind_speed"},
                    {"label": "Humidity", "value": "humidity"},
                    {"label": "Precipitation", "value": "precipitation"},
                ],
                value="all",
                inline=True,
                labelStyle={"display": "inline-block", "margin-right": "18px", "font-weight": "bold", "color": "#2985b9"}
            ),
            html.Br(),

            html.Label("Temperature Unit"),
            dcc.Dropdown(
                id='temp-unit-selector',
                options=[
                    {"label": "Celsius (°C)", "value": "C"},
                    {"label": "Fahrenheit (°F)", "value": "F"}
                ],
                value="C",
                clearable=False,
                style={"width": "100%"}
            ),
            html.Br(),

            html.Label("Thresholds"),
            dbc.Input(id='max-temp', type='number', placeholder="Max Temp °C", size='sm'),
            html.Br(),
            dbc.Input(id='min-temp', type='number', placeholder="Min Temp °C", size='sm'),
            html.Br(),
            dbc.Input(id='max-wind', type='number', placeholder="Max Wind km/h", size='sm'),
            html.Br(),
            dbc.Input(id='min-humidity', type='number', placeholder="Min Humidity %", size='sm'),
            html.Br(),

            dbc.Input(id='precip-threshold', type='number', placeholder="Precip Threshold (mm)", size='sm'),
            html.Br(),

            html.Label("Start Alert After (Hour, 0-23)"),
            dbc.Input(id='alert-start-hour', type='number', min=0, max=23, placeholder="Hour (24h)", size='sm'),
            html.Br(),

            dbc.Row([
                dbc.Col(dbc.Button("Get Forecast", id="submit-button", color="primary", className="w-100"), width=7),
                dbc.Col(dbc.Button("Reset", id="reset-button", color="secondary", className="w-100"), width=5)
            ], className="mb-2"),
            html.H5("Summary - Biggest Change Last Hour:", className="mt-3"),
            html.Div(id="summary-widget", style={"fontWeight": "bold"}),
            html.Br(),
            dbc.Button("Check other days", id="open-calendar-btn", color="info", className="mt-2 w-100"),
            # Modal for calendar
            dbc.Modal(
                [
                    dbc.ModalHeader("Select a Date"),
                    dbc.ModalBody(
                        dcc.DatePickerSingle(
                            id='date-picker',
                            placeholder=str(datetime.today()),
                            min_date_allowed=(datetime.now() - timedelta(days=7)).date(),
                            max_date_allowed=(datetime.now() + timedelta(days=7)).date(),
                            initial_visible_month=datetime.now().date(),
                            display_format='YYYY-MM-DD'
                        )
                    ),
                ],
                id="calendar-modal",
                is_open=False,
                centered=True
            ),
        ], md=4),

        dbc.Col([
            html.Div([
                dbc.RadioItems(
                    id='visual-mode-radio',
                    options=[
                        {"label": "Graph", "value": "graph"},
                        {"label": "Icon Summary", "value": "icons"}
                    ],
                    value="graph",
                    inline=True,
                    labelStyle={"margin-right": "18px", "font-weight": "bold"}
                ),
            ], className="mb-2"),
            html.Div(id="feature-icons"),
            dcc.Graph(id="weather-graph"),
            html.Div(id="forecast-table"),
            dcc.ConfirmDialog(id='alert-popup', message=''),
        ], md=8)
    ])
], fluid=True)

# --- Helper Functions ---
def save_raw_data(city_upper, df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RAW_DATA_DIR, f"{city_upper}_raw_{timestamp}.csv")
    df.to_csv(filepath, index=False)

def clean_data(df):
    df_clean = df.drop_duplicates(subset=['Time']).copy()
    df_clean.fillna(method='ffill', inplace=True)
    return df_clean

def save_clean_data(city_upper, df_clean):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(CLEAN_DATA_DIR, f"{city_upper}_cleaned_{timestamp}.csv")
    df_clean.to_csv(filepath, index=False)

def save_daily_report(city_upper, df):
    date_str = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(REPORT_DIR, f"{city_upper}_hourly_report_{date_str}.csv")
    df.to_csv(filepath, index=False)

# --- Callbacks ---

# 1. Calendar Modal Open/Close
@app.callback(
    Output("calendar-modal", "is_open"),
    [Input("open-calendar-btn", "n_clicks"),
     Input("date-picker", "date")],
    [State("calendar-modal", "is_open")]
)
def toggle_calendar_modal(open_clicks, selected_date, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == "open-calendar-btn":
        return True
    elif trigger == "date-picker" and selected_date:
        return False
    return is_open

# 2. Main Forecast Update (Get Forecast or Date Selected)
@app.callback(
    [Output("weather-graph", "figure"),
     Output("weather-graph", "style"),
     Output("feature-icons", "children"),
     Output("alert-popup", "message"),
     Output("alert-popup", "displayed"),
     Output("summary-widget", "children"),
     Output("forecast-table", "children")],
    [Input("submit-button", "n_clicks"),
     Input("date-picker", "date"),
     Input("visual-mode-radio", "value")],
    [State("city-dropdown", "value"),
     State("max-temp", "value"),
     State("min-temp", "value"),
     State("max-wind", "value"),
     State("min-humidity", "value"),
     State("temp-unit-selector", "value"),
     State("precip-threshold", "value"),
     State("detailed-feature-radio", "value"),
     State("alert-start-hour", "value")]
)
def update_forecast(n_clicks, selected_date, visual_mode, city, max_temp, min_temp, max_wind, min_humidity,
                    temp_unit, precip_threshold, detailed_feature, alert_start_hour):
    ctx = callback_context
    if not city:
        return dash.no_update

    city_upper = city.upper()
    lat, lon = CITIES[city_upper]

    # Determine which input triggered the callback
    today = datetime.now().date()
    target_date = today
    if ctx.triggered and any("date-picker" in trig['prop_id'] for trig in ctx.triggered) and selected_date:
        target_date = datetime.strptime(selected_date, "%Y-%m-%d").date()

    # API: Use past_days or forecast_days if not today
    past_days = (today - target_date).days
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation&timezone=auto"
    )
    if past_days > 0:
        url += f"&past_days={past_days}"
    elif past_days < 0:
        url += f"&forecast_days={abs(past_days)}"

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame({
        "Time": pd.to_datetime(data["hourly"]["time"]),
        "temperature": data["hourly"]["temperature_2m"],
        "wind_speed": data["hourly"]["wind_speed_10m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
        "precipitation": data["hourly"]["precipitation"]
    })

    save_raw_data(city_upper, df)
    df_clean = clean_data(df)
    save_clean_data(city_upper, df_clean)

    # Only data for selected date
    df_24h = df_clean[df_clean["Time"].dt.date == target_date].copy()
    df_24h["temperature_F"] = df_24h["temperature"] * 9/5 + 32

    # Filter for hours after alert_start_hour if set
    if alert_start_hour is not None:
        df_24h = df_24h[df_24h["Time"].dt.hour > alert_start_hour]

    # --- ICONS for summary ---
    icon_map = {
        "temperature": "🔥" if df_24h["temperature"].mean() > 30 else "❄️" if df_24h["temperature"].mean() < 10 else "🌡️",
        "wind_speed": "🌬️",
        "humidity": "💧",
        "precipitation": "🌧️" if df_24h["precipitation"].mean() > 1 else "☀️"
    }
    feature_labels = {
        "temperature": "Temperature",
        "wind_speed": "Wind Speed",
        "humidity": "Humidity",
        "precipitation": "Precipitation"
    }

    # Prepare icon cards for all four features
    feature_cards = []
    if detailed_feature == "all":
        features = ["temperature", "wind_speed", "humidity", "precipitation"]
    else:
        features = [detailed_feature]

    for feat in features:
        if feat == "temperature":
            value = df_24h["temperature"].mean() if temp_unit == "C" else (df_24h["temperature"].mean() * 9/5 + 32)
            unit = "°C" if temp_unit == "C" else "°F"
        elif feat == "wind_speed":
            value = df_24h["wind_speed"].mean()
            unit = "km/h"
        elif feat == "humidity":
            value = df_24h["humidity"].mean()
            unit = "%"
        elif feat == "precipitation":
            value = df_24h["precipitation"].sum()
            unit = "mm"
        else:
            value, unit = "", ""
        feature_cards.append(
            dbc.Card(
                dbc.CardBody([
                    html.H2(icon_map[feat], style={"font-size": "3rem"}),
                    html.H4(f"{feature_labels[feat]}", className="card-title"),
                    html.P(f"{value:.1f} {unit}", className="card-text", style={"font-size": "1.5rem", "font-weight": "bold"})
                ]),
                className="m-2 text-center",
                style={"width": "10rem", "display": "inline-block"}
            )
        )

    # --- Choose what to display ---
    if visual_mode == "icons":
        fig = go.Figure()  # Empty figure
        graph_style = {"display": "none"}
        icons_div = html.Div(feature_cards, style={"display": "flex", "justify-content": "center"})
    else:
        # Original plotting code
        fig = go.Figure()
        if "temperature" in features:
            y_data = df_24h["temperature"] if temp_unit == "C" else df_24h["temperature"] * 9/5 + 32
            unit = "°C" if temp_unit == "C" else "°F"
            fig.add_trace(go.Scatter(x=df_24h["Time"], y=y_data, name=f"Temp ({unit})"))
        if "wind_speed" in features:
            fig.add_trace(go.Scatter(x=df_24h["Time"], y=df_24h["wind_speed"], name="Wind Speed (km/h)"))
        if "humidity" in features:
            fig.add_trace(go.Scatter(x=df_24h["Time"], y=df_24h["humidity"], name="Humidity (%)"))
        if "precipitation" in features:
            fig.add_trace(go.Scatter(x=df_24h["Time"], y=df_24h["precipitation"], name="Precipitation (mm)"))
        fig.update_layout(title=f"Hourly Weather Forecast - {city_upper.title()} ({target_date})",
                          xaxis_title="Time", yaxis_title="Values")
        graph_style = {"display": "block"}
        icons_div = html.Div()  # Empty

    # Alerts (only for hours after alert_start_hour)
    alerts = []
    if max_temp is not None:
        exceeded = df_24h[df_24h["temperature"] > max_temp]
        alerts += [f"🔥 Temp {row.temperature}°C at {row.Time}" for row in exceeded.itertuples()]
    if min_temp is not None:
        below = df_24h[df_24h["temperature"] < min_temp]
        alerts += [f"❄️ Temp {row.temperature}°C at {row.Time}" for row in below.itertuples()]
    if max_wind is not None:
        windy = df_24h[df_24h["wind_speed"] > max_wind]
        alerts += [f"🌬️ Wind {row.wind_speed} km/h at {row.Time}" for row in windy.itertuples()]
    if min_humidity is not None:
        dry = df_24h[df_24h["humidity"] < min_humidity]
        alerts += [f"💧 Humidity {row.humidity}% at {row.Time}" for row in dry.itertuples()]
    if precip_threshold is not None:
        precip_exceeded = df_24h[df_24h["precipitation"] > precip_threshold]
        alerts += [f"🌧️ Precip {row.precipitation} mm at {row.Time}" for row in precip_exceeded.itertuples()]

    alert_message = "\n".join(alerts) if alerts else ""
    alert_displayed = bool(alerts)

    # Summary widget
    last_hour = datetime.now() - timedelta(hours=1)
    df_last_hour = df_24h[df_24h["Time"] >= last_hour]
    df_last_hour = df_last_hour.sort_values("Time")
    df_last_hour["temp_diff"] = df_last_hour["temperature"].diff().abs()
    df_last_hour["wind_diff"] = df_last_hour["wind_speed"].diff().abs()
    df_last_hour["humidity_diff"] = df_last_hour["humidity"].diff().abs()

    max_change = df_last_hour[["temp_diff", "wind_diff", "humidity_diff"]].max()
    biggest_change_metric = max_change.idxmax()
    biggest_change_value = max_change.max()

    summary_text = "No significant changes in last hour."
    if biggest_change_value and biggest_change_value > 0:
        if biggest_change_metric == "temp_diff":
            summary_text = f"Temperature changed by {biggest_change_value:.1f} °C in last hour."
        elif biggest_change_metric == "wind_diff":
            summary_text = f"Wind Speed changed by {biggest_change_value:.2f} km/h in last hour."
        elif biggest_change_metric == "humidity_diff":
            summary_text = f"Humidity changed by {biggest_change_value:.2f}% in last hour."

    # Hourly summary table
    df_table = df_24h.copy()
    df_table["Time"] = df_table["Time"].dt.strftime("%Y-%m-%d %H:%M")
    if temp_unit == "C":
        df_table = df_table[["Time", "temperature", "wind_speed", "humidity", "precipitation"]]
        df_table.rename(columns={"temperature": "Temp (°C)", "wind_speed": "Wind (km/h)", "humidity": "Humidity (%)", "precipitation": "Precip (mm)"}, inplace=True)
    else:
        df_table["Temp (°F)"] = df_table["temperature"] * 9/5 + 32
        df_table = df_table[["Time", "Temp (°F)", "wind_speed", "humidity", "precipitation"]]
        df_table.rename(columns={"wind_speed": "Wind (km/h)", "humidity": "Humidity (%)", "precipitation": "Precip (mm)"}, inplace=True)

    save_daily_report(city_upper, df_table)
    table = dbc.Table.from_dataframe(df_table, striped=True, bordered=True, hover=True, class_name="mt-3")

    return fig, graph_style, icons_div, alert_message, alert_displayed, summary_text, table

# 3. Reset Button
@app.callback(
    [Output('city-dropdown', 'value'),
     Output('detailed-feature-radio', 'value'),
     Output('temp-unit-selector', 'value'),
     Output('max-temp', 'value'),
     Output('min-temp', 'value'),
     Output('max-wind', 'value'),
     Output('min-humidity', 'value'),
     Output('precip-threshold', 'value'),
     Output('alert-start-hour', 'value')],
    Input('reset-button', 'n_clicks')
)
def reset_inputs(n):
    if n:
        return "NEW YORK", "all", "C", None, None, None, None, None, None
    return dash.no_update

if __name__ == "__main__":
    app.run(debug=True)
