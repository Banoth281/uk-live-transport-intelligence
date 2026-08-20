import hashlib
import json
import os
import time

from confluent_kafka import Producer
from dotenv import load_dotenv

from src.ingestion.tfl_client import get_line_arrivals
from src.processing.transform import transform_arrival

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:19092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transport.arrivals")

POLL_INTERVAL_SECONDS = int(
    os.getenv("POLL_INTERVAL_SECONDS", "30")
)


def create_event_key(event) -> str:
    """
    Deterministic key used to avoid storing the exact
    same TfL prediction more than once.
    """

    identity = "|".join(
        [
            event.vehicle_id or "",
            event.line_id or "",
            event.station_id or "",
            str(event.expected_arrival or ""),
            event.direction or "",
        ]
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def publish_snapshot(producer, line_id: str):
    raw_arrivals = get_line_arrivals(line_id)

    produced = 0
    rejected = 0

    for raw in raw_arrivals:
        try:
            event = transform_arrival(raw)

            payload = event.model_dump(
                mode="json",
                exclude_none=True,
            )

            event_key = create_event_key(event)
            payload["event_key"] = event_key

            producer.produce(
                topic=KAFKA_TOPIC,
                key=event_key.encode("utf-8"),
                value=json.dumps(payload).encode("utf-8"),
                callback=delivery_report,
            )

            producer.poll(0)

            produced += 1

        except Exception as exc:
            rejected += 1
            print(f"Rejected event: {exc}")

    producer.flush()

    return produced, rejected


def run_forever(line_id: str = "victoria"):
    producer = Producer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "client.id": "tfl-live-arrival-producer",
        }
    )

    print("UK Live Transport producer started")
    print(f"Line: {line_id}")
    print(f"Interval: {POLL_INTERVAL_SECONDS}s")
    print(f"Topic: {KAFKA_TOPIC}\n")

    try:
        while True:

            started = time.time()

            try:
                produced, rejected = publish_snapshot(
                    producer,
                    line_id,
                )

                print(
                    f"Snapshot complete | "
                    f"Produced: {produced} | "
                    f"Rejected: {rejected}"
                )

            except Exception as exc:
                print(f"Snapshot failed: {exc}")

            elapsed = time.time() - started

            sleep_for = max(
                1,
                POLL_INTERVAL_SECONDS - elapsed,
            )

            print(
                f"Next TfL poll in "
                f"{sleep_for:.0f}s\n"
            )

            time.sleep(sleep_for)

    except KeyboardInterrupt:
        print("\nProducer stopped.")


if __name__ == "__main__":
    run_forever()