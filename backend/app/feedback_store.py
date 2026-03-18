"""
Investigator feedback loop (PRD Section 12.2).

In-memory store for prototype: investigator_decisions and scorer_config.
When investigator marks false_positive with high confidence, we adjust
innocence discount for that pattern type (e.g. GST discount -20% -> -28%).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# In-memory tables (prototype; use DB in production)
investigator_decisions: List[Dict[str, Any]] = []
scorer_config: Dict[str, Dict[str, Any]] = {}
_model_version = 1


def add_decision(
    alert_id: str,
    decision: str,
    confidence: int,
    pattern_type: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Record investigator decision. decision: confirmed_fraud | false_positive | unclear.
    confidence: 1-5. When false_positive and confidence >= 4, increase GST discount
    for this pattern type so similar alerts get a stronger innocence discount.
    """
    global _model_version
    entry = {
        "alert_id": alert_id,
        "decision": decision,
        "confidence": confidence,
        "pattern_type": pattern_type,
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
    }
    investigator_decisions.append(entry)

    if decision == "false_positive" and confidence >= 4 and pattern_type:
        # Strengthen innocence discount for this pattern type (e.g. GST -20% -> -28%)
        if pattern_type not in scorer_config:
            scorer_config[pattern_type] = {"signal_weights": {}, "model_version": _model_version}
        cfg = scorer_config[pattern_type]
        current = cfg.get("gst_discount_pct", 20)
        # Cap at 30 (max innocence discount)
        new_val = min(30, current + 8)
        cfg["gst_discount_pct"] = new_val
        cfg["model_version"] = _model_version
        _model_version += 1

    return {"ok": True, "model_version": _model_version}


def get_scorer_config() -> Dict[str, Dict[str, Any]]:
    return dict(scorer_config)


def get_decisions(alert_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if alert_id is None:
        return list(investigator_decisions)
    return [d for d in investigator_decisions if d.get("alert_id") == alert_id]
