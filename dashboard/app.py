import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
DEMO_DATA_PATH = Path(__file__).with_name("demo_data.json")

st.set_page_config(page_title="UK Live Transport Intelligence", page_icon="🚇", layout="wide")


@st.cache_data
def load_demo_data():
    """Load a representative snapshot for the public portfolio demo."""
    with DEMO_DATA_PATH.open(encoding="utf-8") as demo_file:
        return json.load(demo_file)


@st.cache_data(ttl=20)
def get_json(endpoint):
    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
    response.raise_for_status()
    return response.json()


def load_transport_data():
    """Prefer the live API and fall back safely when it is unavailable."""
    try:
        return (
            get_json("/lines/victoria/performance"),
            get_json("/stations/performance?limit=16"),
            get_json("/arrivals/recent?limit=20"),
            True,
        )
    except (requests.RequestException, ValueError, KeyError):
        demo_data = load_demo_data()
        return (
            demo_data["line_performance"],
            demo_data["station_performance"],
            demo_data["recent_arrivals"],
            False,
        )


st.title("🚇 UK Live Transport Intelligence")
st.caption(
    "TfL arrival analytics powered by Python, Kafka-compatible streaming, "
    "PostgreSQL, dbt and FastAPI."
)

line, stations, arrivals, is_live = load_transport_data()

st.sidebar.markdown("### Data Platform")
st.sidebar.write("TfL API → Redpanda → PostgreSQL → dbt → FastAPI")

if is_live:
    st.sidebar.success("Live API connected")
    refresh_seconds = st.sidebar.selectbox("Auto refresh", [10, 30, 60], index=1)
else:
    st.sidebar.info("Portfolio demo mode")
    st.info(
        "**Portfolio demo:** displaying a representative TfL data snapshot. "
        "Run the complete pipeline locally to enable live streaming data."
    )
    refresh_seconds = None

col1, col2, col3, col4 = st.columns(4)
col1.metric("Predictions", f'{line["prediction_count"]:,}')
col2.metric("Active Vehicles", line["unique_vehicles"])
col3.metric("Average Wait", f'{line["avg_wait_minutes"]} min')
col4.metric("Arrivals ≤ 3 min", line["arrivals_within_3_minutes"])

st.divider()
stations_df = pd.DataFrame(stations)
st.subheader("Station Performance")
chart_df = stations_df[["station_name", "avg_wait_minutes"]].set_index("station_name")
st.bar_chart(chart_df)

st.divider()
left, right = st.columns(2)
station_columns = [
    "station_name",
    "avg_wait_minutes",
    "unique_vehicles",
    "arrivals_within_3_minutes",
]

with left:
    st.subheader("Shortest Average Waits")
    shortest = stations_df[station_columns].sort_values("avg_wait_minutes").head(8)
    st.dataframe(shortest, width="stretch", hide_index=True)

with right:
    st.subheader("Highest Average Waits")
    longest = stations_df[station_columns].sort_values("avg_wait_minutes", ascending=False).head(8)
    st.dataframe(longest, width="stretch", hide_index=True)

st.divider()
st.subheader("Recent Arrival Predictions")
arrivals_df = pd.DataFrame(arrivals)
display_columns = [
    "line_name",
    "station_name",
    "destination_name",
    "direction",
    "minutes_to_station",
    "platform_name",
    "wait_band",
]
st.dataframe(arrivals_df[display_columns], width="stretch", hide_index=True)

if is_live and refresh_seconds:
    st.caption(f"Live dashboard refreshes every {refresh_seconds} seconds.")
    time.sleep(refresh_seconds)
    st.rerun()
else:
    st.caption("Representative portfolio snapshot derived from the live data schema.")
