CREATE TABLE IF NOT EXISTS arrivals (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50),
    line_id VARCHAR(100) NOT NULL,
    line_name VARCHAR(100),
    station_id VARCHAR(100),
    station_name VARCHAR(255) NOT NULL,
    destination_name VARCHAR(255),
    direction VARCHAR(50),
    time_to_station INTEGER,
    expected_arrival TIMESTAMPTZ,
    event_timestamp TIMESTAMPTZ,
    mode_name VARCHAR(50),
    platform_name VARCHAR(255),
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_arrivals_station
ON arrivals(station_id);

CREATE INDEX IF NOT EXISTS idx_arrivals_line
ON arrivals(line_id);

CREATE INDEX IF NOT EXISTS idx_arrivals_expected
ON arrivals(expected_arrival);