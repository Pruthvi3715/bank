from typing import Any, Dict, Optional


class ContextAgent:
    """
    Evaluates innocence signals from KYC/profile data and returns a
    discount percentage (0–30%) that reduces the raw risk score.

    Signal breakdown (max 30%):
      +20%  GST-registered entity with active filings (or scorer_config override per pattern)
      +10%  Established banking relationship (account age > 6 months)
      -5%   Pending/failed KYC verification (negative signal)
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
            # Unknown / unregistered account — no discount
            return 0.0

        discount = 0.0

        # Signal 1: GST-registered business (+20% or config override from investigator feedback)
        gst_pct = 20.0
        if pattern_type and scorer_config and pattern_type in scorer_config:
            gst_pct = float(scorer_config[pattern_type].get("gst_discount_pct", 20))
        if kyc_data.get("has_gst", False):
            discount += gst_pct

        # Signal 2: Established relationship — age > 6 months (+10%)
        if kyc_data.get("account_age_months", 0) > 6:
            discount += 10.0

        # Negative signal: pending KYC removes the age bonus
        if kyc_data.get("kyc_status", "Verified") == "Pending":
            discount = max(0.0, discount - 5.0)

        return min(discount, 30.0)
