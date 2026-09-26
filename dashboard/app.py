"""Public transport explorer and clearly labelled engineering pipeline demo."""
import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from live_tfl import LINES, fetch_arrivals
from train_scene import render_train_scene


API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
TFL_API_KEY = os.getenv("TFL_API_KEY")
DEMO_DATA_PATH = Path(__file__).with_name("demo_data.json")

st.set_page_config(page_title="London Transport Intelligence", page_icon="🚇", layout="wide")


@st.cache_data
def load_demo_data():
    with DEMO_DATA_PATH.open(encoding="utf-8") as demo_file:
        return json.load(demo_file)


@st.cache_data(ttl=30)
def load_live_line(line_id):
    return fetch_arrivals(line_id, api_key=TFL_API_KEY)


@st.cache_data(ttl=20)
def get_json(endpoint):
    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
    response.raise_for_status()
    return response.json()


def load_pipeline_data():
    if API_BASE_URL:
        try:
            return (
                get_json("/lines/victoria/performance"),
                get_json("/stations/performance?limit=16"),
                get_json("/arrivals/recent?limit=20"),
                True,
            )
        except (requests.RequestException, ValueError, KeyError):
            st.warning("The pipeline API is unavailable. Showing the saved demonstration snapshot.")
    sample = load_demo_data()
    return (
        sample["line_performance"],
        sample["station_performance"],
        sample["recent_arrivals"],
        False,
    )


st.title("🚇 London Transport Intelligence")
st.write(
    "Explore current TfL arrival predictions, then inspect the separate "
    "Kafka → PostgreSQL → dbt → FastAPI analytics project."
)
live_tab, pipeline_tab = st.tabs(["Live TfL arrivals", "Data pipeline analytics"])

with live_tab:
    st.subheader("Next predicted arrivals")
    st.caption(
        "Direct TfL Unified API feed. Times are predictions as of the displayed retrieval time, "
        "not actual arrivals; they may change. Expired predictions are removed."
    )
    controls, refresh = st.columns([3, 1])
    with controls:
        line_name = st.selectbox("Tube line", list(LINES))
    with refresh:
        if st.button("Refresh TfL feed"):
            load_live_line.clear()

    try:
        predictions, retrieved_at = load_live_line(LINES[line_name])
    except (requests.RequestException, ValueError) as exc:
        st.error("Live TfL predictions are unavailable right now. Please retry later.")
        st.caption(f"Feed error: {type(exc).__name__}. No saved sample is presented as live.")
    else:
        st.success(f"TfL response retrieved at {retrieved_at:%d %b %Y, %H:%M:%S} UTC")
        if not predictions:
            st.info("TfL returned no usable predictions for this line at this time.")
        else:
            station_names = sorted({row["station"] for row in predictions})
            station = st.selectbox("Station", station_names)
            station_rows = [row for row in predictions if row["station"] == station]
            station_rows.sort(key=lambda row: row["minutes"])
            st.metric("Next predicted train at retrieval", f'{station_rows[0]["minutes"]:.1f} min')
            st.caption(f"{len(station_rows)} predictions currently returned for {station}. "
                       "Vehicles can appear more than once across stations.")
            st.subheader("3D train approach")
            st.caption("Select a predicted train in the scene. Its animated approach represents the countdown, not its real position.")
            components.html(render_train_scene(line_name, station, station_rows, retrieved_at), height=565, scrolling=False)
            st.subheader("Arrival details")
            table = pd.DataFrame(station_rows)[
                ["destination", "minutes", "platform", "expected_arrival"]
            ].rename(columns={
                "destination": "Destination",
                "minutes": "Minutes",
                "platform": "Platform",
                "expected_arrival": "TfL expected arrival (UTC)",
            })
            st.dataframe(table, width="stretch", hide_index=True)
    st.markdown("[TfL Unified API and open data](https://tfl.gov.uk/info-for/open-data-users/unified-api)")

with pipeline_tab:
    st.subheader("Streaming pipeline analysis")
    st.caption("TfL → Python → Redpanda/Kafka → PostgreSQL → dbt → FastAPI")
    line, stations, arrivals, is_live = load_pipeline_data()
    if is_live:
        st.success("Connected to the configured pipeline API. Metrics reflect stored predictions.")
    else:
        st.info(
            "**Saved portfolio snapshot.** These fixed example metrics are not current "
            "TfL conditions. Run the full pipeline and configure API_BASE_URL for live "
            "pipeline analytics. Use the first tab for direct live predictions."
        )

    a, b, c, d = st.columns(4)
    a.metric("Stored predictions" if is_live else "Sample predictions", f'{line["prediction_count"]:,}')
    b.metric("Unique vehicles in dataset", line["unique_vehicles"])
    c.metric("Average predicted wait", f'{line["avg_wait_minutes"]} min')
    d.metric("Predictions ≤ 3 min", line["arrivals_within_3_minutes"])
    st.caption(
        "Pipeline metrics describe the stored dataset or saved sample, not the number "
        "of trains operating across London now."
    )

    stations_df = pd.DataFrame(stations)
    if not stations_df.empty:
        st.subheader("Station performance")
        st.bar_chart(stations_df.set_index("station_name")["avg_wait_minutes"])
        cols = ["station_name", "avg_wait_minutes", "unique_vehicles",
                "arrivals_within_3_minutes"]
        left, right = st.columns(2)
        with left:
            st.markdown("**Shortest average predicted waits**")
            st.dataframe(stations_df[cols].sort_values("avg_wait_minutes").head(8),
                         width="stretch", hide_index=True)
        with right:
            st.markdown("**Highest average predicted waits**")
            st.dataframe(stations_df[cols].sort_values("avg_wait_minutes", ascending=False).head(8),
                         width="stretch", hide_index=True)

    arrivals_df = pd.DataFrame(arrivals)
    if not arrivals_df.empty:
        st.subheader("Recent stored predictions" if is_live else "Example predictions")
        cols = ["line_name", "station_name", "destination_name", "direction",
                "minutes_to_station", "platform_name", "wait_band"]
        st.dataframe(arrivals_df[cols], width="stretch", hide_index=True)
