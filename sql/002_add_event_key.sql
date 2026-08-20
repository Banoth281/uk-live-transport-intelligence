ALTER TABLE arrivals
ADD COLUMN IF NOT EXISTS event_key VARCHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS uq_arrivals_event_key
ON arrivals(event_key);