"""
Kafka/Redpanda Transaction Consumer — Streams live transactions into the detection pipeline.

Consumes from: graphsentinel.transactions.raw
Batches transactions by time window (default 10s) or count (default 500).
Runs DetectionOrchestrator on each batch and emits alerts.
Uses fire-and-forget throughout — consumer failures never crash the app.
"""

import os
import json
import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from app.events.producer import (
    emit_pipeline_started,
    emit_alert_created,
    emit_pipeline_completed,
    emit_pipeline_error,
)
from app.pipeline.orchestrator import DetectionOrchestrator

logger = logging.getLogger(__name__)

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    _HAS_AIOKAFKA = True
except ImportError:
    _HAS_AIOKAFKA = False

_BOOTSTRAP_SERVERS = os.getenv("REDPANDA_BROKERS", "localhost:9092").split(",")
_TRANSACTION_TOPIC = "graphsentinel.transactions.raw"
_ALERT_TOPIC = "graphsentinel.alerts.detected"

_BATCH_TIMEOUT_SEC = float(os.getenv("KAFKA_BATCH_TIMEOUT_SEC", "10"))
_BATCH_SIZE = int(os.getenv("KAFKA_BATCH_SIZE", "500"))
_ENABLE_STREAMING = os.getenv("KAFKA_ENABLE_STREAMING", "false").lower() == "true"

_consumer_instance: Optional["AIOKafkaConsumer"] = None
_producer_instance: Optional["AIOKafkaProducer"] = None
_orchestrator = DetectionOrchestrator()
_txn_buffer: list = []
_buffer_lock = threading.Lock()
_last_flush = datetime.now(timezone.utc)
_running = False


async def _get_consumer() -> Optional["AIOKafkaConsumer"]:
    global _consumer_instance
    if not _HAS_AIOKAFKA:
        return None
    if _consumer_instance is None:
        _consumer_instance = AIOKafkaConsumer(
            _TRANSACTION_TOPIC,
            bootstrap_servers=_BOOTSTRAP_SERVERS,
            group_id="graphsentinel-consumer",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        try:
            await _consumer_instance.start()
            logger.info("Kafka consumer started — subscribed to %s", _TRANSACTION_TOPIC)
        except Exception as exc:
            logger.warning("Failed to start Kafka consumer: %s", exc)
            _consumer_instance = None
            return None
    return _consumer_instance


async def _get_producer() -> Optional["AIOKafkaProducer"]:
    global _producer_instance
    if not _HAS_AIOKAFKA:
        return None
    if _producer_instance is None:
        _producer_instance = AIOKafkaProducer(
            bootstrap_servers=_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",
        )
        try:
            await _producer_instance.start()
        except Exception as exc:
            logger.warning("Failed to start Kafka producer (alert output): %s", exc)
            _producer_instance = None
            return None
    return _producer_instance


async def _close():
    global _consumer_instance, _producer_instance, _running
    _running = False
    if _consumer_instance:
        try:
            await _consumer_instance.stop()
        except Exception:
            pass
        _consumer_instance = None
    if _producer_instance:
        try:
            await _producer_instance.stop()
        except Exception:
            pass
        _producer_instance = None


def _flush_buffer() -> list:
    global _txn_buffer, _last_flush
    with _buffer_lock:
        flushed = list(_txn_buffer)
        _txn_buffer.clear()
        _last_flush = datetime.now(timezone.utc)
    return flushed


def _should_flush() -> bool:
    global _txn_buffer, _last_flush
    now = datetime.now(timezone.utc)
    age = (now - _last_flush).total_seconds()
    with _buffer_lock:
        count = len(_txn_buffer)
    return count >= _BATCH_SIZE or (count > 0 and age >= _BATCH_TIMEOUT_SEC)


def _publish_alert_to_kafka(alert: dict, producer) -> None:
    if producer is None:
        return
    try:
        producer.send(_ALERT_TOPIC, value=alert)
    except Exception:
        pass


async def _process_batch(transactions: list, batch_id: str) -> None:
    """Run detection on a batch and emit results."""
    if not transactions:
        return

    from app.models.schemas import TransactionBase

    txns = [TransactionBase(**t) for t in transactions]
    emit_pipeline_started(batch_id, len(txns))

    try:
        result = _orchestrator.run_detection_pipeline(transactions=txns)
        alerts = result.get("alerts", [])
        emit_pipeline_completed(
            batch_id, len(alerts), result.get("duration_seconds", 0)
        )

        producer = await _get_producer()
        for alert in alerts:
            alert_dict = alert if isinstance(alert, dict) else alert.model_dump()
            _publish_alert_to_kafka(alert_dict, producer)
            emit_alert_created(
                batch_id,
                alert_dict.get("alert_id", ""),
                alert_dict.get("pattern_type", ""),
                alert_dict.get("risk_score", 0.0),
            )
    except Exception as exc:
        logger.error("Pipeline error on batch %s: %s", batch_id, exc)
        emit_pipeline_error(batch_id, str(exc))


async def _consume_loop():
    """Main consumer loop — batches transactions and runs detection."""
    global _running
    _running = True
    consumer = await _get_consumer()
    if not consumer:
        logger.warning(
            "Kafka streaming consumer not available — running in polling-only mode"
        )
        return

    logger.info(
        "Starting Kafka consume loop — batching by %ds or %d txns",
        _BATCH_TIMEOUT_SEC,
        _BATCH_SIZE,
    )
    batch_counter = 0

    while _running:
        try:
            records = await asyncio.wait_for(consumer.getmany(), timeout=2.0)
        except asyncio.TimeoutError:
            records = []
        except Exception as exc:
            logger.warning("Consumer error: %s — retrying in 5s", exc)
            await asyncio.sleep(5)
            continue

        for tp, msgs in records.items():
            for msg in msgs:
                try:
                    txn = msg.value
                    with _buffer_lock:
                        _txn_buffer.append(txn)
                except Exception as exc:
                    logger.warning("Failed to parse transaction: %s", exc)

        if _should_flush():
            batch_counter += 1
            batch_id = f"kafka-batch-{batch_counter}"
            transactions = _flush_buffer()
            await _process_batch(transactions, batch_id)


async def start_streaming():
    """Start the Kafka consumer in the background (call from FastAPI lifespan)."""
    if not _HAS_AIOKAFKA:
        logger.info("aiokafka not installed — streaming disabled")
        return
    if not _ENABLE_STREAMING:
        logger.info("KAFKA_ENABLE_STREAMING=false — streaming disabled")
        return
    task = asyncio.create_task(_consume_loop(), name="kafka-consumer-loop")
    return task


async def stop_streaming():
    """Flush remaining buffer and close consumer."""
    global _running
    _running = False
    if _txn_buffer:
        batch_id = "kafka-flush-shutdown"
        transactions = _flush_buffer()
        await _process_batch(transactions, batch_id)
    await _close()
