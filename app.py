"""
Avocado Prices Interactive Dashboard
Dash version for deployment on Render.
"""

from pathlib import Path
import io

import pandas as pd
import plotly.express as px

from dash import Dash, Input, Output, State, callback, dash_table, dcc, html
from flask import send_file


# ============================================================
# Data
# ============================================================

CSV_PATH = Path(__file__).with_name("avocado-updated-2020.csv")

TOTAL_US = "Total U.S."

AGGREGATE_AREAS = {
    "California",
    "Great Lakes",
    "Midsouth",
    "Northeast",
    "Plains",
    "Southeast",
    "South Central",
    "West",
}


def classify_geography(geo):
    if geo == TOTAL_US:
        return "Total U.S."
    if geo in AGGREGATE_AREAS:
        return "Aggregate region"
    return "City / State"


def load_data(path):
    data = pd.read_csv(path)
    data["date"] = pd.to_datetime(data["date"])
    data["month"] = data["date"].dt.to_period("M").dt.to_timestamp()
    data["geo_level"] = data["geography"].apply(classify_geography)
    return data


df = load_data(CSV_PATH)

min_date = df["date"].min()
max_date = df["date"].max()

all_types = sorted(df["type"].dropna().unique())

city_regions = sorted(
    df.loc[df["geo_level"] == "City / State", "geography"].dropna().unique()
)

default_regions = [
    region
    for region in ["Los Angeles", "New York", "Chicago"]
    if region in city_regions
]

if not default_regions:
    default_regions = city_regions[:3]


# ============================================================
# Dash application
# ============================================================

app = Dash(__name__)
server = app.server

app.title = "Avocado Prices Dashboard"


# ============================================================
# Styles
# ============================================================

PAGE_STYLE = {
    "fontFamily": "Arial, sans-serif",
    "backgroundColor": "#f6f8f5",
    "minHeight": "100vh",
    "margin": "0",
}

SIDEBAR_STYLE = {
    "width": "280px",
    "padding": "25px",
    "backgroundColor": "#ffffff",
    "borderRight": "1px solid #dddddd",
}

CONTENT_STYLE = {
    "flex": "1",
    "padding": "30px",
    "minWidth": "0",
}

CARD_STYLE = {
    "backgroundColor": "white",
    "padding": "20px",
    "borderRadius": "10px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.10)",
    "textAlign": "center",
    "flex": "1",
    "minWidth": "170px",
}

GRAPH_CARD_STYLE = {
    "backgroundColor": "white",
    "padding": "18px",
    "borderRadius": "10px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
    "marginBottom": "20px",
}


# ============================================================
# Layout
# ============================================================

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[
        html.Div(
            style={"display": "flex"},
            children=[

                # ---------------- Sidebar ----------------
                html.Div(
                    style=SIDEBAR_STYLE,
                    children=[
                        html.H2("🥑 Filters"),

                        html.Label("Date range"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=min_date.date(),
                            max_date_allowed=max_date.date(),
                            start_date=min_date.date(),
                            end_date=max_date.date(),
                            display_format="YYYY-MM-DD",
                            style={"marginBottom": "20px"},
                        ),

                        html.Br(),
                        html.Br(),

                        html.Label("Avocado type"),
                        dcc.Dropdown(
                            id="avocado-type",
                            options=[
                                {"label": value, "value": value}
                                for value in all_types
                            ],
                            value=all_types,
                            multi=True,
                            clearable=False,
                        ),

                        html.Br(),

                        html.Label("Geography level"),
                        dcc.RadioItems(
                            id="geo-level",
                            options=[
                                {
                                    "label": "City / State only",
                                    "value": "City / State only",
                                },
                                {
                                    "label": "Aggregate regions only",
                                    "value": "Aggregate regions only",
                                },
                                {
                                    "label": "Total U.S. only",
                                    "value": "Total U.S. only",
                                },
                                {
                                    "label": "Custom (pick any)",
                                    "value": "Custom (pick any)",
                                },
                            ],
                            value="City / State only",
                            labelStyle={
                                "display": "block",
                                "margin": "8px 0",
                            },
                        ),

                        html.Br(),

                        html.Label("Region(s)"),
                        dcc.Dropdown(
                            id="regions",
                            options=[
                                {"label": r, "value": r}
                                for r in city_regions
                            ],
                            value=default_regions,
                            multi=True,
                        ),

                        html.Div(
                            id="geo-warning",
                            style={
                                "marginTop": "15px",
                                "fontSize": "13px",
                                "color": "#9a6700",
                            },
                        ),

                        html.Hr(),

                        html.P(
                            "Data: Avocado Prices 2020",
                            style={
                                "fontSize": "12px",
                                "color": "#666",
                            },
                        ),
                    ],
                ),

                # ---------------- Main content ----------------
                html.Div(
                    style=CONTENT_STYLE,
                    children=[
                        html.H1("🥑 Avocado Prices Dashboard"),

                        html.P(
                            id="summary-text",
                            style={"color": "#666"},
                        ),

                        # KPI cards
                        html.Div(
                            style={
                                "display": "flex",
                                "gap": "15px",
                                "flexWrap": "wrap",
                                "margin": "25px 0",
                            },
                            children=[
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        html.H4("Avg. Price"),
                                        html.H2(id="kpi-price"),
                                    ],
                                ),
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        html.H4("Total Volume"),
                                        html.H2(id="kpi-volume"),
                                    ],
                                ),
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        html.H4("Total Bags Sold"),
                                        html.H2(id="kpi-bags"),
                                    ],
                                ),
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        html.H4("Price Change"),
                                        html.H2(id="kpi-change"),
                                    ],
                                ),
                            ],
                        ),

                        # Tabs
                        dcc.Tabs(
                            id="tabs",
                            value="price-trends",
                            children=[
                                dcc.Tab(
                                    label="📈 Price Trends",
                                    value="price-trends",
                                ),
                                dcc.Tab(
                                    label="🌎 Regional Comparison",
                                    value="regional",
                                ),
                                dcc.Tab(
                                    label="📦 Volume & Bag Mix",
                                    value="volume",
                                ),
                                dcc.Tab(
                                    label="🔍 Raw Data",
                                    value="raw",
                                ),
                            ],
                        ),

                        html.Div(
                            id="tab-content",
                            style={"marginTop": "25px"},
                        ),
                    ],
                ),
            ],
        )
    ],
)


# ============================================================
# Geography dropdown callback
# ============================================================

@callback(
    Output("regions", "options"),
    Output("regions", "value"),
    Output("geo-warning", "children"),
    Input("geo-level", "value"),
)
def update_region_options(level_choice):

    if level_choice == "City / State only":
        pool = sorted(
            df.loc[
                df["geo_level"] == "City / State",
                "geography",
            ].unique()
        )

    elif level_choice == "Aggregate regions only":
        pool = sorted(
            df.loc[
                df["geo_level"] == "Aggregate region",
                "geography",
            ].unique()
        )

    elif level_choice == "Total U.S. only":
        pool = [TOTAL_US]

    else:
        pool = sorted(df["geography"].unique())

    defaults = [
        r
        for r in ["Los Angeles", "New York", "Chicago", TOTAL_US]
        if r in pool
    ]

    if not defaults:
        defaults = pool[:3]

    options = [{"label": r, "value": r} for r in pool]

    warning = ""

    if level_choice == "Custom (pick any)":
        warning = (
            "Note: selecting geography levels that overlap can "
            "double-count volume and bag totals."
        )

    return options, defaults, warning


# ============================================================
# Main dashboard callback
# ============================================================

@callback(
    Output("summary-text", "children"),
    Output("kpi-price", "children"),
    Output("kpi-volume", "children"),
    Output("kpi-bags", "children"),
    Output("kpi-change", "children"),
    Output("tab-content", "children"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("avocado-type", "value"),
    Input("regions", "value"),
    Input("tabs", "value"),
)
def update_dashboard(
    start_date,
    end_date,
    avocado_types,
    regions,
    selected_tab,
):

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    if not avocado_types:
        avocado_types = all_types

    if not regions:
        regions = sorted(df["geography"].unique())

    mask = (
        (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["type"].isin(avocado_types))
        & (df["geography"].isin(regions))
    )

    fdf = df.loc[mask].copy()

    if fdf.empty:
        message = "No data matches the current filters."

        return (
            message,
            "—",
            "—",
            "—",
            "—",
            html.Div(
                message,
                style={
                    "padding": "30px",
                    "backgroundColor": "#fff3cd",
                },
            ),
        )

    summary = (
        f"Showing {len(fdf):,} records across "
        f"{fdf['geography'].nunique()} region(s), "
        f"{start_date.date()} to {end_date.date()}."
    )

    avg_price = f"${fdf['average_price'].mean():.2f}"
    total_volume = f"{fdf['total_volume'].sum():,.0f}"
    total_bags = f"{fdf['total_bags'].sum():,.0f}"

    daily_price = (
        fdf.sort_values("date")
        .groupby("date")["average_price"]
        .mean()
    )

    price_delta = daily_price.iloc[-1] - daily_price.iloc[0]
    price_change = f"${price_delta:+.2f}"

    # ========================================================
    # Price Trends tab
    # ========================================================

    if selected_tab == "price-trends":

        trend = (
            fdf.groupby(
                ["date", "type", "geography"]
            )["average_price"]
            .mean()
            .reset_index()
        )

        color_dim = (
            "geography"
            if len(regions) > 1
            else "type"
        )

        fig1 = px.line(
            trend,
            x="date",
            y="average_price",
            color=color_dim,
            line_dash=(
                "type"
                if color_dim == "geography"
                else None
            ),
            labels={
                "average_price": "Avg. Price ($)",
                "date": "Date",
            },
            title="Average Price Over Time",
        )

        fig1.update_layout(
            hovermode="x unified",
        )

        fig2 = px.box(
            fdf,
            x="type",
            y="average_price",
            color="type",
            labels={
                "average_price": "Avg. Price ($)",
                "type": "Type",
            },
            title="Price Distribution by Type",
        )

        tab_content = html.Div(
            [
                html.Div(
                    dcc.Graph(figure=fig1),
                    style=GRAPH_CARD_STYLE,
                ),
                html.Div(
                    dcc.Graph(figure=fig2),
                    style=GRAPH_CARD_STYLE,
                ),
            ]
        )

    # ========================================================
    # Regional Comparison tab
    # ========================================================

    elif selected_tab == "regional":

        rank_level = (
            fdf["geo_level"].iloc[0]
            if fdf["geo_level"].nunique() == 1
            else "City / State"
        )

        ranked_pool = df[
            (df["date"] >= start_date)
            & (df["date"] <= end_date)
            & (df["type"].isin(avocado_types))
            & (df["geo_level"] == rank_level)
        ]

        region_avg = (
            ranked_pool
            .groupby("geography")["average_price"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig3 = px.bar(
            region_avg,
            x="average_price",
            y="geography",
            orientation="h",
            height=max(
                400,
                25 * len(region_avg),
            ),
            labels={
                "average_price": "Avg. Price ($)",
                "geography": "Region",
            },
            color="average_price",
            color_continuous_scale="Greens",
            title="Average Price by Region",
        )

        fig3.update_layout(
            yaxis={
                "categoryorder": "total ascending"
            }
        )

        scatter_df = (
            fdf.groupby("geography")
            .agg(
                avg_price=(
                    "average_price",
                    "mean",
                ),
                total_volume=(
                    "total_volume",
                    "sum",
                ),
            )
            .reset_index()
        )

        fig4 = px.scatter(
            scatter_df,
            x="total_volume",
            y="avg_price",
            text="geography",
            size="total_volume",
            labels={
                "total_volume": "Total Volume",
                "avg_price": "Avg. Price ($)",
            },
            title="Selected Regions: Price vs Volume",
        )

        fig4.update_traces(
            textposition="top center"
        )

        fig4.update_xaxes(type="log")

        tab_content = html.Div(
            [
                html.P(
                    "Regions are ranked within one geography "
                    "level to avoid misleading comparisons."
                ),
                html.Div(
                    dcc.Graph(figure=fig3),
                    style=GRAPH_CARD_STYLE,
                ),
                html.Div(
                    dcc.Graph(figure=fig4),
                    style=GRAPH_CARD_STYLE,
                ),
            ]
        )

    # ========================================================
    # Volume & Bag Mix tab
    # ========================================================

    elif selected_tab == "volume":

        plu = (
            fdf[["4046", "4225", "4770"]]
            .sum()
            .rename(
                {
                    "4046": "Small (4046)",
                    "4225": "Medium (4225)",
                    "4770": "Large (4770)",
                }
            )
        )

        fig5 = px.pie(
            values=plu.values,
            names=plu.index,
            hole=0.4,
            title="Volume by PLU (Avocado Size Code)",
        )

        bags = (
            fdf[
                [
                    "small_bags",
                    "large_bags",
                    "xlarge_bags",
                ]
            ]
            .sum()
            .rename(
                {
                    "small_bags": "Small Bags",
                    "large_bags": "Large Bags",
                    "xlarge_bags": "XLarge Bags",
                }
            )
        )

        fig6 = px.pie(
            values=bags.values,
            names=bags.index,
            hole=0.4,
            title="Bag Size Mix",
        )

        vol_trend = (
            fdf.groupby(
                ["month", "type"]
            )["total_volume"]
            .sum()
            .reset_index()
        )

        fig7 = px.area(
            vol_trend,
            x="month",
            y="total_volume",
            color="type",
            labels={
                "total_volume": "Total Volume",
                "month": "Month",
            },
            title="Total Volume Over Time",
        )

        tab_content = html.Div(
            [
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "20px",
                        "flexWrap": "wrap",
                    },
                    children=[
                        html.Div(
                            dcc.Graph(figure=fig5),
                            style={
                                **GRAPH_CARD_STYLE,
                                "flex": "1",
                                "minWidth": "350px",
                            },
                        ),
                        html.Div(
                            dcc.Graph(figure=fig6),
                            style={
                                **GRAPH_CARD_STYLE,
                                "flex": "1",
                                "minWidth": "350px",
                            },
                        ),
                    ],
                ),
                html.Div(
                    dcc.Graph(figure=fig7),
                    style=GRAPH_CARD_STYLE,
                ),
            ]
        )

    # ========================================================
    # Raw Data tab
    # ========================================================

    else:

        table_df = (
            fdf.sort_values(
                "date",
                ascending=False,
            )
            .copy()
        )

        table_df["date"] = (
            table_df["date"]
            .dt.strftime("%Y-%m-%d")
        )

        if "month" in table_df.columns:
            table_df["month"] = (
                table_df["month"]
                .dt.strftime("%Y-%m")
            )

        tab_content = html.Div(
            [
                html.H3("Filtered Raw Data"),

                html.P(
                    "The geo_level column identifies City / "
                    "State, Aggregate region, or Total U.S."
                ),

                html.Button(
                    "Download filtered data as CSV",
                    id="download-button",
                    n_clicks=0,
                    style={
                        "padding": "10px 16px",
                        "marginBottom": "15px",
                        "cursor": "pointer",
                    },
                ),

                dcc.Download(
                    id="download-data"
                ),

                dash_table.DataTable(
                    data=table_df.to_dict("records"),
                    columns=[
                        {
                            "name": column,
                            "id": column,
                        }
                        for column in table_df.columns
                    ],
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                    style_table={
                        "overflowX": "auto",
                    },
                    style_cell={
                        "textAlign": "left",
                        "padding": "8px",
                        "fontSize": "12px",
                        "minWidth": "100px",
                        "maxWidth": "180px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                    style_header={
                        "fontWeight": "bold",
                        "backgroundColor": "#eeeeee",
                    },
                ),
            ]
        )

    return (
        summary,
        avg_price,
        total_volume,
        total_bags,
        price_change,
        tab_content,
    )


# ============================================================
# Download callback
# ============================================================

@callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("avocado-type", "value"),
    State("regions", "value"),
    prevent_initial_call=True,
)
def download_filtered_data(
    n_clicks,
    start_date,
    end_date,
    avocado_types,
    regions,
):

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    if not avocado_types:
        avocado_types = all_types

    if not regions:
        regions = sorted(
            df["geography"].unique()
        )

    mask = (
        (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["type"].isin(avocado_types))
        & (df["geography"].isin(regions))
    )

    download_df = df.loc[mask].copy()

    return dcc.send_data_frame(
        download_df.to_csv,
        "avocado_filtered.csv",
        index=False,
    )


# ============================================================
# Run locally
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
