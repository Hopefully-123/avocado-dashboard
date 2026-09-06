"""
Avocado Prices Interactive Dashboard
=====================================
Dataset: Avocado Prices 2020 (Kaggle - timmate/avocado-prices-2020)

Run locally with:
    pip install streamlit pandas plotly
    streamlit run app.py

Make sure `avocado-updated-2020.csv` is in the same folder as this script
(or update the CSV_PATH variable below).
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Avocado Prices Dashboard",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = Path(__file__).with_name("avocado-updated-2020.csv")

# The HAB's `geography` column mixes three different levels of granularity:
#   - "Total U.S."       -> the whole country
#   - 8 broad areas       -> California, Great Lakes, Midsouth, Northeast,
#                            Plains, Southeast, South Central, West
#   - individual cities/metros/states -> everything else (San Francisco,
#                                          Chicago, South Carolina, etc.)
# Per the dataset notes, Total U.S. is NOT simply the sum of the 8 areas,
# and the 8 areas are themselves aggregates of the cities within them.
# Summing across mixed levels (e.g. "Total U.S." + "California" + "Los
# Angeles") double- or triple-counts volume, so we tag each row with its
# level and warn the user if they select a mix.
TOTAL_US = "Total U.S."
AGGREGATE_AREAS = {
    "California", "Great Lakes", "Midsouth", "Northeast",
    "Plains", "Southeast", "South Central", "West",
}


def classify_geography(geo: str) -> str:
    if geo == TOTAL_US:
        return "Total U.S."
    if geo in AGGREGATE_AREAS:
        return "Aggregate region"
    return "City / State"


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["geo_level"] = df["geography"].apply(classify_geography)
    return df


df = load_data(CSV_PATH)

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.title("🥑 Filters")

min_date, max_date = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = min_date, max_date

avocado_type = st.sidebar.multiselect(
    "Avocado type",
    options=sorted(df["type"].unique()),
    default=sorted(df["type"].unique()),
)

st.sidebar.markdown("**Geography level**")
level_choice = st.sidebar.radio(
    "Which level of geography to show",
    options=["City / State only", "Aggregate regions only", "Total U.S. only", "Custom (pick any)"],
    index=0,
    label_visibility="collapsed",
)

if level_choice == "City / State only":
    region_pool = sorted(df.loc[df["geo_level"] == "City / State", "geography"].unique())
elif level_choice == "Aggregate regions only":
    region_pool = sorted(df.loc[df["geo_level"] == "Aggregate region", "geography"].unique())
elif level_choice == "Total U.S. only":
    region_pool = [TOTAL_US]
else:
    region_pool = sorted(df["geography"].unique())

default_regions = [r for r in ["Los Angeles", "New York", "Chicago", TOTAL_US] if r in region_pool]
if not default_regions:
    default_regions = region_pool[:3]

regions = st.sidebar.multiselect(
    "Region(s)",
    options=region_pool,
    default=default_regions,
)

# Warn if the user picked a "Custom" mix that spans levels, since summed
# metrics (volume, bags) would double-count across Total U.S. / area / city.
if level_choice == "Custom (pick any)" and regions:
    levels_selected = {classify_geography(r) for r in regions}
    if len(levels_selected) > 1:
        st.sidebar.warning(
            "You've selected regions from different levels (e.g. a city and "
            "its parent area, or Total U.S.). Per the HAB's own data notes, "
            "these don't sum cleanly — summed metrics (volume, bags) will "
            "double-count. Price averages are still fine to compare."
        )

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: [Avocado Prices 2020, Kaggle](https://www.kaggle.com/datasets/timmate/avocado-prices-2020/data)"
)

# --------------------------------------------------------------------------
# Filtered data
# --------------------------------------------------------------------------
mask = (
    (df["date"] >= start_date)
    & (df["date"] <= end_date)
    & (df["type"].isin(avocado_type))
    & (df["geography"].isin(regions if regions else region_pool))
)
fdf = df.loc[mask].copy()

st.title("🥑 Avocado Prices Dashboard")
st.caption(
    f"Showing {len(fdf):,} records across {fdf['geography'].nunique()} region(s), "
    f"{start_date.date()} to {end_date.date()}."
)

if fdf.empty:
    st.warning("No data matches the current filters. Adjust the filters in the sidebar.")
    st.stop()

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Avg. Price", f"${fdf['average_price'].mean():.2f}")
with col2:
    st.metric("Total Volume", f"{fdf['total_volume'].sum():,.0f}")
with col3:
    st.metric("Total Bags Sold", f"{fdf['total_bags'].sum():,.0f}")
with col4:
    price_delta = (
        fdf.sort_values("date").groupby("date")["average_price"].mean().iloc[-1]
        - fdf.sort_values("date").groupby("date")["average_price"].mean().iloc[0]
    )
    st.metric("Price Change (period)", f"${price_delta:+.2f}")

st.markdown("---")

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Price Trends", "🌎 Regional Comparison", "📦 Volume & Bag Mix", "🔍 Raw Data"]
)

# --- Tab 1: Price trends over time ----------------------------------------
with tab1:
    st.subheader("Average Price Over Time")

    granularity = st.radio(
        "Granularity", ["Weekly", "Monthly"], horizontal=True, key="gran1"
    )
    time_col = "date" if granularity == "Weekly" else "month"

    trend = (
        fdf.groupby([time_col, "type", "geography"])["average_price"]
        .mean()
        .reset_index()
    )

    color_dim = "geography" if len(regions) > 1 else "type"
    fig = px.line(
        trend,
        x=time_col,
        y="average_price",
        color=color_dim,
        line_dash="type" if color_dim == "geography" else None,
        markers=False,
        labels={"average_price": "Avg. Price ($)", time_col: "Date"},
    )
    fig.update_layout(hovermode="x unified", legend_title_text=color_dim.title())
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Price Distribution by Type")
    fig2 = px.box(
        fdf, x="type", y="average_price", color="type",
        labels={"average_price": "Avg. Price ($)", "type": "Type"},
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Tab 2: Regional comparison --------------------------------------------
with tab2:
    st.subheader("Average Price by Region")
    st.caption(
        "Ranked within one geography level at a time (city/state, aggregate "
        "region, or Total U.S.) so the comparison is apples-to-apples — "
        "price averages are fine to compare across levels, but this chart "
        "keeps it to one level for clarity."
    )

    rank_level = st.selectbox(
        "Rank regions within:",
        options=["City / State", "Aggregate region", "Total U.S."],
        index=0,
    )

    ranked_pool = df[
        (df["date"] >= start_date)
        & (df["date"] <= end_date)
        & (df["type"].isin(avocado_type))
        & (df["geo_level"] == rank_level)
    ]

    region_avg = (
        ranked_pool.groupby("geography")["average_price"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig3 = px.bar(
        region_avg,
        x="average_price",
        y="geography",
        orientation="h",
        height=max(300, 25 * len(region_avg)),
        labels={"average_price": "Avg. Price ($)", "geography": "Region"},
        color="average_price",
        color_continuous_scale="Greens",
    )
    fig3.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Selected Regions: Price vs Volume")
    scatter_df = fdf.groupby("geography").agg(
        avg_price=("average_price", "mean"),
        total_volume=("total_volume", "sum"),
    ).reset_index()
    fig4 = px.scatter(
        scatter_df,
        x="total_volume",
        y="avg_price",
        text="geography",
        size="total_volume",
        labels={"total_volume": "Total Volume", "avg_price": "Avg. Price ($)"},
    )
    fig4.update_traces(textposition="top center")
    fig4.update_xaxes(type="log")
    st.plotly_chart(fig4, use_container_width=True)

# --- Tab 3: Volume & bag mix -------------------------------------------
with tab3:
    st.subheader("Volume by PLU (Avocado Size Code)")
    plu = fdf[["4046", "4225", "4770"]].sum().rename(
        {"4046": "Small (4046)", "4225": "Medium (4225)", "4770": "Large (4770)"}
    )
    fig5 = px.pie(values=plu.values, names=plu.index, hole=0.4)
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Bag Size Mix")
    bags = fdf[["small_bags", "large_bags", "xlarge_bags"]].sum().rename(
        {"small_bags": "Small Bags", "large_bags": "Large Bags", "xlarge_bags": "XLarge Bags"}
    )
    fig6 = px.pie(values=bags.values, names=bags.index, hole=0.4)
    st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Total Volume Over Time")
    vol_trend = fdf.groupby(["month", "type"])["total_volume"].sum().reset_index()
    fig7 = px.area(
        vol_trend, x="month", y="total_volume", color="type",
        labels={"total_volume": "Total Volume", "month": "Month"},
    )
    st.plotly_chart(fig7, use_container_width=True)

# --- Tab 4: Raw data --------------------------------------------------------
with tab4:
    st.subheader("Filtered Raw Data")
    st.caption(
        "The `geo_level` column tags each row as City / State, Aggregate "
        "region, or Total U.S. — useful if you're exporting for further "
        "analysis and want to avoid double-counting."
    )
    st.dataframe(fdf.sort_values("date", ascending=False), use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="avocado_filtered.csv",
        mime="text/csv",
    )
