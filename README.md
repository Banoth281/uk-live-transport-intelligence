# 🚇 UK Live Transport Intelligence

[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://uk-live-transport-intelligence.streamlit.app)

[![UK Transport Intelligence CI](https://github.com/Banoth281/uk-live-transport-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/Banoth281/uk-live-transport-intelligence/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![dbt](https://img.shields.io/badge/dbt-Analytics-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

A real-time data engineering platform that ingests live Transport for London (TfL) arrival predictions, streams events through Redpanda/Kafka, stores them in PostgreSQL, transforms the data with dbt, exposes analytical endpoints through FastAPI, and presents transport intelligence through an interactive Streamlit dashboard.

> **Public demo:** the **Plan a journey** tab searches TfL stations and shows
> current station-to-station rail itineraries, changes, leg details and service
> messages. The **Live TfL arrivals** tab calls TfL's Unified API directly,
> with a station picker, retrieval time and explicit unavailable state.
> The separate **Data pipeline analytics** tab connects to your configured
> FastAPI service or displays a clearly labelled saved portfolio snapshot.

In **Plan a journey**, enter two rail station names, select individual TfL
station matches, and choose a returned itinerary. The page shows estimated
duration, changes, step-by-step legs, reported issues and current line status.
The animated route story illustrates the selected itinerary; it does not track
an actual train. Journey estimates and service conditions can change. This
independent project is powered by the Transport for London Journey Planner API.

The live tab also includes an interactive **3D train approach**. Select any of
the 11 Underground lines, Elizabeth line, DLR, six named Overground lines or
Tram in one selector. Choose a station and one of its currently predicted
services below the scene to watch its illustrated approach and
countdown. The animation is calculated from TfL's expected arrival time in
your browser, so it is **not a real train location or a route trace**. When a
prediction passes, refresh the TfL feed for updated service information.
The scene is self-contained HTML Canvas and needs no mapping or 3D API key.
Some lines may have no active arrival predictions at certain times; the site
shows an empty state in that case.

---

## 📌 Project Overview

UK Live Transport Intelligence demonstrates an end-to-end streaming data platform built around real public transport data.

The platform continuously collects TfL arrival predictions and converts raw operational events into analytics such as:

- Live arrival predictions
- Active vehicle counts
- Average passenger wait times
- Arrivals within three minutes
- Station-level performance
- Line-level performance
- Vehicle and destination information
- Wait-time bands

The project demonstrates practical skills in streaming ingestion, event-driven architecture, data modelling, analytics engineering, API development, containerisation and CI/CD.

---

## 🏗️ Architecture

```text
                  Transport for London API
                            │
                            ▼
                   Python TfL Ingestion
                            │
                            ▼
                   Redpanda / Kafka
                  transport.arrivals
                            │
                            ▼
                    Python Consumer
                            │
                            ▼
                      PostgreSQL
                      raw arrivals
                            │
                            ▼
                           dbt
                ┌───────────┼────────────┐
                ▼           ▼            ▼
          fact_arrivals   station      line
                         performance  performance
                │
                ▼
             FastAPI
                │
                ▼
        Streamlit Dashboard
```

### Data flow

**TfL API → Python → Redpanda/Kafka → PostgreSQL → dbt → FastAPI → Streamlit**

---

## ⚡ Real-Time Streaming

The producer periodically retrieves live arrival predictions from the TfL API and publishes validated events to the Kafka-compatible topic:

```text
transport.arrivals
```

Each event contains information such as:

```json
{
  "vehicle_id": "203",
  "line_id": "victoria",
  "line_name": "Victoria",
  "station_name": "Pimlico Underground Station",
  "destination_name": "Walthamstow Central Underground Station",
  "direction": "outbound",
  "time_to_station": 120,
  "mode_name": "tube",
  "platform_name": "Northbound - Platform 1"
}
```

The consumer reads the event stream and persists arrival records into PostgreSQL for downstream transformation and analytics.

---

## 🗄️ Analytics Engineering with dbt

The project uses dbt to transform raw transport events into analytics-ready models.

### Staging

`stg_arrivals`

Cleans and standardises raw arrival data.

### Fact Model

`fact_arrivals`

Provides enriched arrival-level records including calculated wait-time information.

### Analytical Marts

`line_performance`

Aggregates metrics including:

- Prediction count
- Station count
- Unique vehicles
- Average wait time
- Minimum and maximum wait
- Arrivals within three minutes

`station_performance`

Provides station-level metrics including:

- Prediction count
- Unique vehicles
- Average wait time
- Short-wait arrivals

---

## 🧪 Data Quality

dbt tests validate critical analytical fields and model integrity.

Current test suite:

```text
PASS=21
WARN=0
ERROR=0
SKIP=0
TOTAL=21
```

Tests include:

- `not_null`
- `unique`
- Arrival ID validation
- Station validation
- Line validation
- Wait-time validation
- Analytical model validation

---

## 📊 Dashboard

The public dashboard has three distinct tabs. **Plan a journey** lets a visitor
search two station names, choose exact TfL results, and request rail journey
options. It shows duration, changes, leg-by-leg instructions, reported journey
disruptions and a separate line status request when available. The illustrated
route story lets visitors inspect each leg and TfL's listed stops. Its animation
is decorative and does not track a train. Journey estimates and status may
change; re-plan before travelling. TfL errors and ambiguous search results are
shown explicitly, and no fixed journey is substituted for a live failure.

**Live TfL arrivals** retrieves
current predictions directly from the TfL Unified API. Pick a Tube line and
station to see upcoming predicted arrivals, destinations and platforms.
Responses are cached for 30 seconds; **Refresh TfL feed** requests an update.
Predictions with expected arrival times before the retrieval time are excluded,
displayed minutes use that expected time when TfL provides it, and identical
station/destination/platform/expected-time predictions are collapsed.
The retrieval time is shown in UTC. If TfL is unavailable, the tab reports
that error instead of displaying an old sample as live data. Predictions can
change and are not actual arrivals. An API key is optional for low-volume
demonstration use and may be configured as `TFL_API_KEY`; TfL applies usage
limits. See [TfL's Unified API](https://tfl.gov.uk/info-for/open-data-users/unified-api).

**Data pipeline analytics** shows metrics from your configured FastAPI service
or a fixed saved snapshot when that service is unavailable. The saved snapshot
has no current-data timestamp and should never be described as live conditions.

### Live Transport Overview

The pipeline analytics tab displays dataset metrics including:

- Total arrival predictions
- Unique vehicles in the stored dataset
- Average predicted wait
- Arrivals within three minutes
- Station-level performance

![UK Live Transport Intelligence Dashboard](docs/images/dashboard.png)

### Station & Arrival Analytics

The platform also provides deeper operational analytics, including:

- Stations with the shortest average waiting times
- Stations with the highest average waiting times
- Unique vehicle counts by station
- Arrivals within three minutes
- Recent arrival predictions
- Destination and direction information
- Platform information
- Wait-time classification

![UK Transport Station and Arrival Analytics](docs/images/transport-analytics.png)
---

## 🔌 FastAPI

FastAPI provides programmatic access to the transformed transport data.

Example endpoint:

```http
GET /arrivals/recent?limit=5
```

Example response:

```json
{
  "line_name": "Victoria",
  "station_name": "Euston Underground Station",
  "destination_name": "Brixton Underground Station",
  "minutes_to_station": 2.27,
  "wait_band": "0-3 min"
}
```

Interactive API documentation is available **only while the FastAPI service is
running locally** at:

```text
http://127.0.0.1:8000/docs
```

`127.0.0.1` is a development address and is not a public recruiter demo.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Ingestion, transformation and streaming |
| TfL Unified API | Live transport arrival data |
| Redpanda / Kafka | Event streaming |
| PostgreSQL | Operational and analytical storage |
| dbt | Data transformation and testing |
| FastAPI | Analytical REST API |
| Streamlit | Interactive dashboard |
| Docker Compose | Local infrastructure orchestration |
| GitHub Actions | Continuous integration |
| Git | Version control |

---

## 📁 Project Structure

```text
uk-live-transport-intelligence/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── dashboard/
│   └── app.py
│
├── dbt/
│   └── transport_analytics/
│       ├── models/
│       │   ├── staging/
│       │   └── marts/
│       └── dbt_project.yml
│
├── docs/
│   └── images/
│       └── dashboard.png
│
├── sql/
│   ├── init.sql
│   └── 002_add_event_key.sql
│
├── src/
│   ├── api/
│   │   └── main.py
│   ├── ingestion/
│   │   └── tfl_client.py
│   ├── processing/
│   │   ├── models.py
│   │   └── transform.py
│   └── streaming/
│       ├── producer.py
│       └── consumer.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🌐 Deploy the Public Recruiter Demo

The public demo does not require Kafka, PostgreSQL, dbt or FastAPI. Its first
tab requests TfL predictions directly. The second tab uses the saved example
in `dashboard/demo_data.json` until a reachable pipeline API is configured.

1. Push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
3. Select **Create app** and enter:
   - Repository: `Banoth281/uk-live-transport-intelligence`
   - Branch: `main`
   - App file: `dashboard/app.py`
   - Python version: `3.12`
4. Choose an available app URL and select **Deploy**.
5. Open the public URL in a private browser window to confirm recruiter access.

Streamlit will use `dashboard/requirements.txt`, keeping the hosted demo small
and independent from the full engineering environment.

The current demo URL is linked at the top of this README.

### Optional live API mode

Set the `API_BASE_URL` environment variable to a publicly hosted FastAPI base
URL. If that service is reachable, the pipeline tab displays stored analytics;
otherwise, it shows the clearly labelled portfolio snapshot. This setting
does not affect the direct TfL arrivals tab. Do not expose API keys in source.

## 🚀 Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Banoth281/uk-live-transport-intelligence.git
cd uk-live-transport-intelligence
```

### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Add the required TfL credentials and local configuration.

**Never commit `.env` or API credentials to GitHub.**

### 5. Start Infrastructure

```powershell
docker compose up -d
```

Check the containers:

```powershell
docker compose ps
```

### 6. Start the Producer

```powershell
python -m src.streaming.producer
```

The producer continuously polls TfL and publishes arrival events to:

```text
transport.arrivals
```

### 7. Start the Consumer

Open another terminal:

```powershell
python -m src.streaming.consumer
```

The consumer reads Kafka events and stores them in PostgreSQL.

### 8. Run dbt

```powershell
cd dbt\transport_analytics
dbt run
dbt test
```

A successful test run should report:

```text
PASS=21
WARN=0
ERROR=0
SKIP=0
TOTAL=21
```

Return to the repository root:

```powershell
cd ..\..
```

### 9. Start FastAPI

```powershell
uvicorn src.api.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 10. Start the Dashboard

Open another terminal from the repository root:

```powershell
streamlit run dashboard/app.py
```

---

## 🔄 Continuous Integration

GitHub Actions automatically runs validation when changes are pushed to the `main` branch or submitted through a pull request.

The CI pipeline validates the Python source code and project dependencies, helping ensure that changes do not break the application.

---

## 🔐 Security

Sensitive credentials are managed through environment variables.

The following files and directories are excluded from Git:

```text
.env
.venv/
__pycache__/
dbt/**/target/
dbt/**/logs/
```

Only `.env.example` is committed as a configuration template.

---

## 🎯 Engineering Skills Demonstrated

This project demonstrates:

- Real-time data ingestion
- Kafka-compatible event streaming
- Producer/consumer architecture
- PostgreSQL data modelling
- SQL analytics
- dbt transformation pipelines
- Automated data-quality testing
- REST API development
- Interactive analytical dashboards
- Docker-based infrastructure
- Environment and secret management
- GitHub Actions CI/CD
- End-to-end data pipeline design

---

## 📈 Future Improvements

Potential extensions include:

- Support for additional TfL lines and transport modes
- Historical trend analysis
- Service disruption ingestion
- Delay and anomaly detection
- Prometheus and Grafana monitoring
- Cloud deployment
- Data warehouse integration
- Automated dbt execution
- Infrastructure health monitoring

---

## 👤 Author

**Santhosh Banoth**

MSc Advanced Computer Science  
University of Liverpool

GitHub: [Banoth281](https://github.com/Banoth281)

---

## 📄 Data Source

Transport data is obtained from the Transport for London Unified API.

This project is intended for educational, portfolio and data-engineering demonstration purposes.
