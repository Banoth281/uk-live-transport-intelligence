import json
import os

from confluent_kafka import Consumer
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from src.processing.models import ArrivalEvent

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:19092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transport.arrivals")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://transport:transport@localhost:5432/transport",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

INSERT_SQL = text(
    """
    INSERT INTO arrivals (
        event_key,
        vehicle_id,
        line_id,
        line_name,
        station_id,
        station_name,
        destination_name,
        direction,
        time_to_station,
        expected_arrival,
        event_timestamp,
        mode_name,
        platform_name
    )
    VALUES (
        :event_key,
        :vehicle_id,
        :line_id,
        :line_name,
        :station_id,
        :station_name,
        :destination_name,
        :direction,
        :time_to_station,
        :expected_arrival,
        :event_timestamp,
        :mode_name,
        :platform_name
    )
    ON CONFLICT (event_key)
    DO NOTHING
    """
)


def save_arrival(event: ArrivalEvent, event_key: str):
    payload = event.model_dump()

    payload["event_timestamp"] = payload.pop("timestamp")
    payload["event_key"] = event_key

    with engine.begin() as connection:
        result = connection.execute(
            INSERT_SQL,
            payload,
        )

    return result.rowcount


def consume():
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": "transport-postgres-consumer-live",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    consumer.subscribe([KAFKA_TOPIC])

    print(f"\nListening to Kafka topic: {KAFKA_TOPIC}\n")

    stored = 0
    duplicates = 0
    failed = 0

    try:
        while True:
            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                print(f"Kafka error: {message.error()}")
                continue

            try:
                raw = json.loads(
                    message.value().decode("utf-8")
                )

                event_key = raw.pop("event_key", None)

                if not event_key:
                    print("Skipping old event without event_key")
                    consumer.commit(
                        message=message,
                        asynchronous=False,
                    )
                    continue

                event = ArrivalEvent.model_validate(raw)

                inserted = save_arrival(
                    event,
                    event_key,
                )

                consumer.commit(
                    message=message,
                    asynchronous=False,
                )

                if inserted:
                    stored += 1

                    print(
                        f"Stored #{stored} | "
                        f"{event.line_name} | "
                        f"{event.station_name} | "
                        f"{event.time_to_station}s"
                    )

                else:
                    duplicates += 1

                    print(
                        f"Duplicate skipped | "
                        f"{event.station_name}"
                    )

            except Exception as exc:
                failed += 1
                print(f"Failed event: {exc}")

    except KeyboardInterrupt:
        print("\nConsumer stopped.")

    finally:
        consumer.close()

        print("\n--- Consumer Summary ---")
        print(f"Stored: {stored}")
        print(f"Duplicates: {duplicates}")
        print(f"Failed: {failed}")


if __name__ == "__main__":
    consume()