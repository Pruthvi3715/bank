"""
ML-based anomaly detection for GraphSentinel.
Isolation Forest (unsupervised) + Gradient Boosting (supervised).
Models are trained on-the-fly from graph data each pipeline run.
"""

import numpy as np
import networkx as nx
from typing import Dict, Any, Optional

from app.ml.feature_extractor import (
    extract_node_features,
    extract_all_features,
    FEATURE_NAMES,
)


class AnomalyDetector:
    """Dual ML scoring: Isolation Forest + Gradient Boosting."""

    def __init__(self):
        self.if_model = None
        self.gb_model = None
        self._feature_names = FEATURE_NAMES

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train_isolation_forest(self, feature_matrix: np.ndarray) -> None:
        """Train Isolation Forest — no labels needed."""
        try:
            from sklearn.ensemble import IsolationForest

            self.if_model = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42,
                n_jobs=-1,
            )
            self.if_model.fit(feature_matrix)
        except ImportError:
            self.if_model = None

    def train_gradient_boosting(
        self, feature_matrix: np.ndarray, labels: np.ndarray
    ) -> None:
        """Train Gradient Boosting with fraud labels."""
        try:
            from sklearn.ensemble import GradientBoostingClassifier

            self.gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
            self.gb_model.fit(feature_matrix, labels)
        except ImportError:
            self.gb_model = None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def score_if(self, features: np.ndarray) -> float:
        """Isolation Forest anomaly score (0-1, higher = more anomalous)."""
        if self.if_model is None:
            return 0.0
        try:
            raw = self.if_model.decision_function(features.reshape(1, -1))[0]
            return round(max(0.0, min(1.0, 0.5 - raw)), 4)
        except Exception:
            return 0.0

    def score_gb(self, features: np.ndarray) -> float:
        """Gradient Boosting fraud probability (0-1)."""
        if self.gb_model is None:
            return 0.0
        try:
            proba = self.gb_model.predict_proba(features.reshape(1, -1))[0]
            return round(float(proba[1]) if len(proba) > 1 else 0.0, 4)
        except Exception:
            return 0.0

    def get_feature_importance(self) -> Dict[str, float]:
        """Feature importances (from GB model or domain-knowledge defaults)."""
        if self.gb_model is not None:
            importances = self.gb_model.feature_importances_
            return dict(zip(self._feature_names, importances.tolist()))
        return {
            "in_degree": 0.08,
            "out_degree": 0.09,
            "in_out_ratio": 0.15,
            "total_in": 0.12,
            "total_out": 0.11,
            "channel_mix": 0.10,
            "off_hours_ratio": 0.13,
            "dormancy_days": 0.07,
            "txn_count": 0.06,
            "amount_variance": 0.09,
        }

    # ------------------------------------------------------------------
    # Full pipeline scoring
    # ------------------------------------------------------------------
    def score_all_nodes(
        self,
        graph: nx.MultiDiGraph,
        kyc_db: Optional[dict] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Score every node with both ML models."""
        feature_matrix, node_ids = extract_all_features(graph, kyc_db)
        if len(feature_matrix) == 0:
            return {}

        # Train IF on current data
        if self.if_model is None:
            self.train_isolation_forest(feature_matrix)

        # Train GB with heuristic labels if no real labels available
        if self.gb_model is None:
            labels = self._generate_heuristic_labels(feature_matrix, graph, node_ids)
            if labels is not None and len(np.unique(labels)) > 1:
                self.train_gradient_boosting(feature_matrix, labels)

        scores: Dict[str, Dict[str, float]] = {}
        for i, node_id in enumerate(node_ids):
            f = feature_matrix[i]
            scores[node_id] = {
                "if_score": self.score_if(f),
                "xgb_score": self.score_gb(f),
            }
        return scores

    # ------------------------------------------------------------------
    # Heuristic label generation (for demo without ground-truth labels)
    # ------------------------------------------------------------------
    def _generate_heuristic_labels(
        self,
        features: np.ndarray,
        graph: nx.MultiDiGraph,
        node_ids: list,
    ) -> Optional[np.ndarray]:
        if len(features) < 20:
            return None

        labels = np.zeros(len(features), dtype=int)
        for i, _node_id in enumerate(node_ids):
            signals = 0
            if 0.85 <= features[i][2] <= 1.15:  # pass-through ratio
                signals += 1
            if features[i][6] > 0.3:  # off-hours ratio
                signals += 1
            if features[i][5] >= 3:  # channel mix
                signals += 1
            if features[i][0] >= 5 or features[i][1] >= 5:  # high degree
                signals += 1
            if signals >= 2:
                labels[i] = 1

        # Ensure at least some positive labels
        if labels.sum() == 0:
            total_flow = features[:, 3] + features[:, 4]
            threshold = np.percentile(total_flow, 95)
            labels[total_flow >= threshold] = 1

        return labels
