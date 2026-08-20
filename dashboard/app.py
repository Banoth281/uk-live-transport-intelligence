import time

import pandas as pd
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="UK Live Transport Intelligence",
    page_icon="🚇",
    layout="wide",
)

st.title("🚇 UK Live Transport Intelligence")
st.caption("Real-time TfL transport analytics powered by Kafka, PostgreSQL, dbt and FastAPI.")

refresh_seconds = st.sidebar.selectbox(
    "Auto refresh",
    [10, 30, 60],
    index=1,
)

st.sidebar.markdown("### Data Platform")
st.sidebar.write("TfL API → Redpanda → PostgreSQL → dbt → FastAPI")


def get_json(endpoint):
    response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
    response.raise_for_status()
    return response.json()


try:
    line = get_json("/lines/victoria/performance")
    stations = get_json("/stations/performance?limit=16")
    arrivals = get_json("/arrivals/recent?limit=20")

except Exception as exc:
    st.error(f"Unable to load transport data: {exc}")
    st.stop()


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Predictions",
    line["prediction_count"],
)

col2.metric(
    "Active Vehicles",
    line["unique_vehicles"],
)

col3.metric(
    "Average Wait",
    f'{line["avg_wait_minutes"]} min',
)

col4.metric(
    "Arrivals ≤ 3 min",
    line["arrivals_within_3_minutes"],
)

st.divider()

stations_df = pd.DataFrame(stations)

st.subheader("Station Performance")

chart_df = stations_df[
    ["station_name", "avg_wait_minutes"]
].set_index("station_name")

st.bar_chart(chart_df)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Shortest Average Waits")

    shortest = stations_df[
        [
            "station_name",
            "avg_wait_minutes",
            "unique_vehicles",
            "arrivals_within_3_minutes",
        ]
    ].sort_values("avg_wait_minutes").head(8)

    st.dataframe(
        shortest,
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.subheader("Highest Average Waits")

    longest = stations_df[
        [
            "station_name",
            "avg_wait_minutes",
            "unique_vehicles",
            "arrivals_within_3_minutes",
        ]
    ].sort_values("avg_wait_minutes", ascending=False).head(8)

    st.dataframe(
        longest,
        use_container_width=True,
        hide_index=True,
    )

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

st.dataframe(
    arrivals_df[display_columns],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    f"Dashboard refreshes every {refresh_seconds} seconds."
)

time.sleep(refresh_seconds)
st.rerun()