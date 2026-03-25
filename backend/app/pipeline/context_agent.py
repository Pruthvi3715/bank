from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

MISMATCH_RISK_BONUS = 25.0
MISMATCH_RATIO_THRESHOLD = 3.0


class ContextAgent:
    """
    Evaluates innocence signals from KYC/profile data and returns a
    discount percentage (0–30%) that reduces the raw risk score.

    Signal breakdown (max 30%):
      +20%  GST-registered entity with active filings (or scorer_config override per pattern)
      +10%  Established banking relationship (account age > 6 months)
      -5%   Pending/failed KYC verification (negative signal)

    Also evaluates Profile Mismatch Detection (PS3 requirement):
      Detects when monthly transaction flow exceeds 3× declared annual income.
    """

    def __init__(self, mock_kyc_db: Dict[str, Any]):
        self.mock_kyc_db = mock_kyc_db

    def evaluate_node(
        self,
        node_id: str,
        pattern_type: Optional[str] = None,
        scorer_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> float:
        """Return innocence discount percentage [0, 30]."""
        kyc_data = self.mock_kyc_db.get(node_id)
        if not kyc_data:
            return 0.0

        discount = 0.0

        gst_pct = 20.0
        if pattern_type and scorer_config and pattern_type in scorer_config:
            gst_pct = float(scorer_config[pattern_type].get("gst_discount_pct", 20))
        if kyc_data.get("has_gst", False):
            discount += gst_pct

        if kyc_data.get("account_age_months", 0) > 6:
            discount += 10.0

        if kyc_data.get("kyc_status", "Verified") == "Pending":
            discount = max(0.0, discount - 5.0)

        return min(discount, 30.0)

    def detect_profile_mismatch(
        self,
        node_id: str,
        graph_edges: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Detect mismatches between declared customer income and actual transaction volume.

        PS3 Requirement: Flag accounts where monthly transaction flow exceeds
        3× declared annual income. This is a strong indicator of:
          - Undeclared business activity
          - mule account usage
          - structuring to avoid reporting thresholds

        Returns:
            dict with mismatch_detected, declared_monthly, actual_monthly,
            mismatch_ratio, and risk_signal (+25 if mismatch detected)
        """
        kyc_data = self.mock_kyc_db.get(node_id, {})
        declared_income = kyc_data.get("declared_income", 0.0)

        if not declared_income or declared_income <= 0:
            return {
                "mismatch_detected": False,
                "declared_monthly": 0.0,
                "actual_monthly": 0.0,
                "mismatch_ratio": 0.0,
                "risk_signal": 0.0,
                "note": "No declared_income data available",
            }

        declared_monthly = declared_income / 12.0

        if not graph_edges:
            return {
                "mismatch_detected": False,
                "declared_monthly": round(declared_monthly, 2),
                "actual_monthly": 0.0,
                "mismatch_ratio": 0.0,
                "risk_signal": 0.0,
                "note": "No edge data available for calculation",
            }

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_naive = cutoff.replace(tzinfo=None)

        monthly_flow = 0.0
        for edge in graph_edges:
            ts = edge.get("timestamp")
            if isinstance(ts, datetime):
                if ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)
            elif not isinstance(ts, datetime):
                try:
                    ts = datetime.fromisoformat(str(ts))
                    if ts.tzinfo is not None:
                        ts = ts.replace(tzinfo=None)
                except Exception:
                    continue
            if ts >= cutoff_naive:
                monthly_flow += abs(edge.get("amount", 0.0))

        mismatch_ratio = (
            monthly_flow / declared_monthly if declared_monthly > 0 else 0.0
        )
        mismatch_detected = mismatch_ratio > MISMATCH_RATIO_THRESHOLD

        return {
            "mismatch_detected": mismatch_detected,
            "declared_monthly": round(declared_monthly, 2),
            "actual_monthly": round(monthly_flow, 2),
            "mismatch_ratio": round(mismatch_ratio, 2),
            "risk_signal": MISMATCH_RISK_BONUS if mismatch_detected else 0.0,
            "threshold": MISMATCH_RATIO_THRESHOLD,
        }

    def score_pattern_mismatch(
        self,
        nodes: List[str],
        edges: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate Profile Mismatch across all nodes in a pattern subgraph.
        Returns worst-case mismatch signal across the subgraph.
        """
        worst: Optional[Dict[str, Any]] = None
        max_ratio = 0.0

        for node in nodes:
            result = self.detect_profile_mismatch(node, edges)
            ratio = result.get("mismatch_ratio", 0.0)
            if ratio > max_ratio:
                max_ratio = ratio
                worst = result

        if worst is None:
            return {
                "mismatch_detected": False,
                "max_ratio": 0.0,
                "risk_signal": 0.0,
                "note": "No nodes evaluated",
            }

        return {
            "mismatch_detected": worst["mismatch_detected"],
            "max_ratio": round(max_ratio, 2),
            "risk_signal": worst["risk_signal"],
            "declared_monthly": worst.get("declared_monthly", 0),
            "actual_monthly": worst.get("actual_monthly", 0),
        }
