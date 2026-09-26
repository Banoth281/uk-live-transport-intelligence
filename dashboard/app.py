"""Public transport explorer and clearly labelled engineering pipeline demo."""
import json
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from live_tfl import LINES, LINE_COLOURS, LINE_GROUPS, fetch_arrivals
from train_scene import render_train_scene
from journey import JourneyDisambiguation, search_stations, fetch_journeys, fetch_line_status
from journey_scene import render_journey_scene


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


@st.cache_data(ttl=600)
def find_stations(query):
    return search_stations(query, api_key=TFL_API_KEY)


@st.cache_data(ttl=60)
def plan_journey(from_id, to_id):
    return fetch_journeys(from_id, to_id, api_key=TFL_API_KEY)


@st.cache_data(ttl=60)
def load_line_status(ids):
    return fetch_line_status(ids, api_key=TFL_API_KEY)


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


def request_route(from_id, to_id, from_name, to_name, *, second_try=False):
    try:
        routes, planned_at = plan_journey(from_id, to_id)
        ids = tuple(sorted({leg["line_id"] for route in routes for leg in route["legs"] if leg["line_id"]}))
        try:
            statuses = load_line_status(ids)
            status_available = True
        except (requests.RequestException, ValueError):
            statuses, status_available = {}, False
        st.session_state.pop("disambiguation", None)
        st.session_state["planned_routes"] = {
            "routes": routes, "retrieved": planned_at,
            "statuses": statuses, "status_available": status_available,
            "from": from_name, "to": to_name,
        }
    except JourneyDisambiguation as exc:
        st.session_state.pop("planned_routes", None)
        if second_try:
            st.session_state.pop("disambiguation", None)
            st.warning("TfL still needs a more precise location. Try another station match.")
        else:
            def ranked(options, name):
                term = name.casefold()
                return sorted(options, key=lambda option: (
                    not option["name"].casefold().startswith(term),
                    "station" not in option["name"].casefold(),
                    option["name"].casefold(),
                ))[:40]
            st.session_state["disambiguation"] = {
                "from_options": ranked(exc.from_options, from_name),
                "to_options": ranked(exc.to_options, to_name),
                "from_id": from_id, "to_id": to_id,
                "from_name": from_name, "to_name": to_name,
            }
    except ValueError as exc:
        st.session_state.pop("planned_routes", None)
        st.warning(str(exc))
    except (requests.RequestException, KeyError):
        st.session_state.pop("planned_routes", None)
        st.error("TfL could not plan this journey right now. Try different stations or retry later.")


st.title("🚇 London Transport Intelligence")
st.write(
    "Plan a TfL rail journey, explore current arrival predictions, then inspect the separate "
    "Kafka → PostgreSQL → dbt → FastAPI analytics project."
)
journey_tab, live_tab, pipeline_tab = st.tabs(["Plan a journey", "Live TfL arrivals", "Data pipeline analytics"])

with journey_tab:
    st.subheader("Plan your route")
    st.caption("Search two stations, select the exact TfL matches, then compare current journey options. The route animation is illustrative.")
    with st.form("station_search"):
        from_col, to_col = st.columns(2)
        from_query = from_col.text_input("From station", value="Westminster")
        to_query = to_col.text_input("To station", value="Bank")
        search_clicked = st.form_submit_button("Find stations", type="primary")
    if search_clicked:
        st.session_state.pop("planned_routes", None)
        st.session_state.pop("disambiguation", None)
        try:
            st.session_state["station_matches"] = (find_stations(from_query), find_stations(to_query))
        except ValueError as exc:
            st.session_state.pop("station_matches", None)
            st.error(str(exc))
        except (requests.RequestException, KeyError):
            st.session_state.pop("station_matches", None)
            st.error("TfL station search is unavailable right now. Please retry later.")

    matches = st.session_state.get("station_matches")
    if matches:
        from_matches, to_matches = matches
        if not from_matches or not to_matches:
            st.info("No matching rail stations were found for one or both searches. Try a longer station name.")
        else:
            left, right = st.columns(2)
            from_id = left.selectbox("Choose the start station", [s["id"] for s in from_matches],
                                     format_func=lambda sid: next(s["name"] for s in from_matches if s["id"] == sid))
            to_id = right.selectbox("Choose the destination station", [s["id"] for s in to_matches],
                                    format_func=lambda sid: next(s["name"] for s in to_matches if s["id"] == sid))
            if st.button("Show TfL journeys", type="primary"):
                request_route(from_id, to_id,
                              next(s["name"] for s in from_matches if s["id"] == from_id),
                              next(s["name"] for s in to_matches if s["id"] == to_id))

    ambiguous = st.session_state.get("disambiguation")
    if ambiguous:
        st.warning("TfL found several places with similar names. Confirm the precise stations below.")
        left, right = st.columns(2)
        from_opts, to_opts = ambiguous["from_options"], ambiguous["to_options"]
        from_choice = left.selectbox("Confirm start location", range(len(from_opts)),
                                     format_func=lambda i: f'{from_opts[i]["name"]} · {from_opts[i]["type"]}') if from_opts else None
        to_choice = right.selectbox("Confirm destination location", range(len(to_opts)),
                                    format_func=lambda i: f'{to_opts[i]["name"]} · {to_opts[i]["type"]}') if to_opts else None
        if st.button("Confirm locations and plan"):
            start = from_opts[from_choice] if from_opts else {"value": ambiguous["from_id"], "name": ambiguous["from_name"]}
            end = to_opts[to_choice] if to_opts else {"value": ambiguous["to_id"], "name": ambiguous["to_name"]}
            request_route(start["value"], end["value"], start["name"], end["name"], second_try=True)

    planned = st.session_state.get("planned_routes")
    if planned:
        st.success(f'TfL journey options retrieved at {planned["retrieved"]:%d %b %Y, %H:%M:%S} UTC')
        routes = planned["routes"]
        if not routes:
            st.info("TfL returned no journeys for this station pair right now. Try another route or time.")
        else:
            st.caption(f'{planned["from"]} → {planned["to"]}. TfL estimates and service conditions can change; refresh the plan before travel.')
            selected = st.selectbox("Journey option", range(len(routes)), format_func=lambda i:
                                    f'Option {i+1} · {routes[i]["duration"] if routes[i]["duration"] is not None else "?"} min · {routes[i]["changes"]} changes')
            route = routes[selected]
            a, b, c = st.columns(3)
            a.metric("Estimated duration", f'{route["duration"]} min' if route["duration"] is not None else "Unavailable")
            b.metric("Changes", route["changes"])
            c.metric("Legs", len(route["legs"]))
            st.caption(f'TfL itinerary: {str(route["departure"] or "?")[11:16]} departure · {str(route["arrival"] or "?")[11:16]} arrival (times as returned by TfL).')
            if route["disrupted"]:
                st.warning("TfL flags a disruption or planned work on this option. Read the affected leg below.")
            st.subheader("Illustrated route story")
            components.html(render_journey_scene(route, colours=LINE_COLOURS), height=580, scrolling=False)
            st.subheader("Step-by-step directions")
            for index, leg in enumerate(route["legs"], 1):
                title = f'{index}. {leg["line"] or leg["mode"]}: {leg["from"]} → {leg["to"]}'
                with st.expander(title, expanded=index == 1):
                    st.write(leg["instruction"] or "Follow TfL directions for this leg.")
                    st.caption(f'{leg["duration"] if leg["duration"] is not None else "?"} min · {leg["mode"]}')
                    if leg["stops"]:
                        st.write("Stops listed by TfL: " + " → ".join(leg["stops"]))
                    if leg["disrupted"]:
                        st.warning("TfL reports an issue or planned work for this leg.")
                        for alert in leg["alerts"]:
                            st.write(alert)
                    if leg["line_id"]:
                        status = planned["statuses"].get(leg["line_id"])
                        if status:
                            st.write(f'Line status: {status["status"]}')
                            if status["reason"]:
                                st.write(status["reason"])
            if not planned["status_available"]:
                st.caption("Live line status is unavailable; itinerary alerts above are from the journey response. Check TfL before travel.")
    st.markdown("[TfL Journey Planner and Unified API](https://tfl.gov.uk/info-for/open-data-users/unified-api)")

with live_tab:
    st.subheader("Next predicted arrivals")
    st.caption(
        "Direct TfL Unified API feed. Times are predictions as of the displayed retrieval time, "
        "not actual arrivals; they may change. Expired predictions are removed."
    )
    controls, refresh = st.columns([3, 1])
    with controls:
        line_name = st.selectbox(
            "TfL rail line / route", list(LINES), index=list(LINES).index("Victoria"),
            format_func=lambda name: name if LINE_GROUPS[name] == name else f"{LINE_GROUPS[name]} · {name}",
        )
        st.caption("Underground, Elizabeth line, DLR, six Overground lines and Tram. Select a line to load its current predictions.")
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
            st.info("TfL returned no usable arrival predictions for this line right now. Some routes do not run at all hours or may not publish predictions. Try another line or refresh later.")
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
            components.html(render_train_scene(
                line_name, station, station_rows, retrieved_at,
                mode=LINE_GROUPS[line_name], accent=LINE_COLOURS[line_name],
            ), height=630, scrolling=False)
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
