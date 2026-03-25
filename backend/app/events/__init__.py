"""Kafka/Redpanda event producer for real-time pipeline events."""

from app.events.producer import (
    emit_pipeline_started,
    emit_alert_created,
    emit_pipeline_completed,
    emit_pipeline_error,
    _close_producer,
)

__all__ = [
    "emit_pipeline_started",
    "emit_alert_created",
    "emit_pipeline_completed",
    "emit_pipeline_error",
    "_close_producer",
]
