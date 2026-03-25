"""
Kafka Event Producer — Streams pipeline events for real-time dashboards.

Events published to Redpanda (Kafka-compatible):
  - graphsentinel.pipeline.started
  - graphsentinel.pipeline.alert_created
  - graphsentinel.pipeline.completed
  - graphsentinel.pipeline.error

Events are fire-and-forget — pipeline never blocks on Kafka.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional

try:
    from aiokafka import AIOKafkaProducer

    _HAS_AIOKAFKA = True
except ImportError:
    _HAS_AIOKAFKA = False


_PRODUCER: Optional["AIOKafkaProducer"] = None
_BOOTSTRAP_SERVERS = os.getenv("REDPANDA_BROKERS", "localhost:9092").split(",")


async def _get_producer() -> Optional["AIOKafkaProducer"]:
    global _PRODUCER
    if not _HAS_AIOKAFKA:
        return None
    if _PRODUCER is None:
        _PRODUCER = AIOKafkaProducer(
            bootstrap_servers=_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",
            enable_idempotence=True,
        )
        try:
            await _PRODUCER.start()
        except Exception:
            _PRODUCER = None
            return None
    return _PRODUCER


async def _close_producer():
    global _PRODUCER
    if _PRODUCER:
        await _PRODUCER.stop()
        _PRODUCER = None


async def publish_event(topic_suffix: str, event_data: dict) -> None:
    """Publish an event to the graphsentinel pipeline topic."""
    producer = await _get_producer()
    if not producer:
        return
    topic = f"graphsentinel.{topic_suffix}"
    try:
        await producer.send_and_wait(
            topic,
            value={
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data,
            },
        )
    except Exception:
        pass


def publish_event_sync(topic_suffix: str, event_data: dict) -> None:
    """Synchronous wrapper for publish_event."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(publish_event(topic_suffix, event_data))
        else:
            loop.run_until_complete(publish_event(topic_suffix, event_data))
    except RuntimeError:
        pass


def emit_pipeline_started(batch_id: str, txn_count: int) -> None:
    publish_event_sync(
        "pipeline.started",
        {"batch_id": batch_id, "txn_count": txn_count},
    )


def emit_alert_created(
    batch_id: str,
    alert_id: str,
    pattern_type: str,
    risk_score: float,
) -> None:
    publish_event_sync(
        "pipeline.alert_created",
        {
            "batch_id": batch_id,
            "alert_id": alert_id,
            "pattern_type": pattern_type,
            "risk_score": risk_score,
        },
    )


def emit_pipeline_completed(
    batch_id: str,
    alerts_generated: int,
    duration_seconds: float,
) -> None:
    publish_event_sync(
        "pipeline.completed",
        {
            "batch_id": batch_id,
            "alerts_generated": alerts_generated,
            "duration_seconds": duration_seconds,
        },
    )


def emit_pipeline_error(batch_id: str, error_message: str) -> None:
    publish_event_sync(
        "pipeline.error",
        {"batch_id": batch_id, "error_message": error_message},
    )
