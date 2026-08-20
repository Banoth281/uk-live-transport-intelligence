import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://transport:transport@localhost:5432/transport",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

app = FastAPI(
    title="UK Live Transport Intelligence API",
    description="Real-time TfL transport analytics powered by Kafka, PostgreSQL and dbt.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "service": "UK Live Transport Intelligence API",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {exc}",
        )


@app.get("/lines")
def get_lines():
    query = text(
        """
        SELECT
            line_id,
            line_name,
            prediction_count,
            station_count,
            unique_vehicles,
            avg_wait_minutes,
            min_wait_minutes,
            max_wait_minutes,
            arrivals_within_3_minutes,
            last_updated
        FROM analytics.line_performance
        ORDER BY line_name
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return [dict(row) for row in rows]


@app.get("/lines/{line_id}/performance")
def get_line_performance(line_id: str):
    query = text(
        """
        SELECT
            line_id,
            line_name,
            prediction_count,
            station_count,
            unique_vehicles,
            avg_wait_minutes,
            min_wait_minutes,
            max_wait_minutes,
            arrivals_within_3_minutes,
            last_updated
        FROM analytics.line_performance
        WHERE line_id = :line_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"line_id": line_id.lower()},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Line not found",
        )

    return dict(row)


@app.get("/stations/performance")
def get_station_performance(limit: int = 20):
    limit = max(1, min(limit, 100))

    query = text(
        """
        SELECT
            line_id,
            line_name,
            station_id,
            station_name,
            prediction_count,
            unique_vehicles,
            avg_wait_minutes,
            min_wait_minutes,
            max_wait_minutes,
            inbound_predictions,
            outbound_predictions,
            arrivals_within_3_minutes,
            last_updated
        FROM analytics.station_performance
        ORDER BY avg_wait_minutes ASC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"limit": limit},
        ).mappings().all()

    return [dict(row) for row in rows]


@app.get("/stations/{station_id}")
def get_station(station_id: str):
    query = text(
        """
        SELECT
            line_id,
            line_name,
            station_id,
            station_name,
            prediction_count,
            unique_vehicles,
            avg_wait_minutes,
            min_wait_minutes,
            max_wait_minutes,
            inbound_predictions,
            outbound_predictions,
            arrivals_within_3_minutes,
            last_updated
        FROM analytics.station_performance
        WHERE station_id = :station_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"station_id": station_id},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Station not found",
        )

    return dict(row)


@app.get("/arrivals/recent")
def recent_arrivals(limit: int = 20):
    limit = max(1, min(limit, 100))

    query = text(
        """
        SELECT
            arrival_id,
            vehicle_id,
            line_name,
            station_name,
            destination_name,
            direction,
            time_to_station,
            minutes_to_station,
            expected_arrival,
            platform_name,
            wait_band
        FROM analytics.fact_arrivals
        ORDER BY event_timestamp DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"limit": limit},
        ).mappings().all()

    return [dict(row) for row in rows]