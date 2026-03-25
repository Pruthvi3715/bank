"""
TokenVault: Per-session PII tokenization with SHA-256 + random salt.

Privacy-preserving layer that replaces all account IDs with role-based
token labels before any data leaves the local environment. Claude API
never sees raw account numbers.

Key Design Decisions:
- Per-session salt: same account produces different token each run
- Role-based tokens preserve graph topology (not sequential HOP_1, HOP_2)
- Vault stored in memory only - never persisted to disk
- Pattern-aware annotations help LLM understand topology
"""

import hashlib
import secrets
from typing import Optional


class TokenVault:
    """
    Per-session PII tokenization with SHA-256 + random salt.
    Vault mapping stored in memory only — never persisted.
    New salt generated every pipeline run.
    """

    def __init__(self):
        self.session_salt = secrets.token_hex(32)  # 256-bit random salt
        self._vault: dict[str, str] = {}  # token -> real_id
        self._reverse: dict[str, str] = {}  # real_id -> token

    def tokenize(self, account_id: str, role: str) -> str:
        """
        Convert account ID to role-based token.

        role: 'CYCLE_ORIGIN' | 'HUB_NODE' | 'SPOKE_001' | 'AGGREGATION_TARGET'
        Role-based NOT sequential (HOP_1, HOP_2) — preserves graph topology.
        """
        if account_id in self._reverse:
            return self._reverse[account_id]

        salted = f"{self.session_salt}:{account_id}"
        hash_val = hashlib.sha256(salted.encode("utf-8")).hexdigest()[:12]
        token = f"{role}_{hash_val}"

        self._vault[token] = account_id
        self._reverse[account_id] = token
        return token

    def detokenize(self, token: str) -> Optional[str]:
        """Convert token back to real account ID."""
        return self._vault.get(token)

    @property
    def reverse_mapping(self) -> dict[str, str]:
        """Public read-only view of real_id → token mapping."""
        return dict(self._reverse)

    def detokenize_text(self, text: str) -> str:
        """Replace all tokens in LLM output with real account IDs."""
        for token, real_id in self._vault.items():
            text = text.replace(token, real_id)
        return text

    def tokenize_subgraph(self, subgraph: dict, pattern_type: str) -> dict:
        """
        Tokenize all account IDs in a subgraph using pattern-aware roles.

        Cycle: CYCLE_ORIGIN, CYCLE_INTERMEDIARY_N, CYCLE_CLOSURE
        Hub: HUB_NODE, SPOKE_001..N, TERMINAL_BENEFICIARY
        Smurfing: AGGREGATION_TARGET, SOURCE_001..N
        """
        tokenized_nodes = []
        tokenized_edges = []

        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        for i, node in enumerate(nodes):
            role = self._assign_role(node, nodes, pattern_type, i)
            token = self.tokenize(node.get("account_id", node.get("id", "")), role)
            tokenized_nodes.append(
                {
                    **node,
                    "token": token,
                    "account_id": "[PROTECTED]",
                }
            )

        for edge in edges:
            sender_id = edge.get("sender_id", edge.get("source", ""))
            receiver_id = edge.get("receiver_id", edge.get("target", ""))
            tokenized_edges.append(
                {
                    **edge,
                    "sender_id": self._reverse.get(sender_id, sender_id),
                    "receiver_id": self._reverse.get(receiver_id, receiver_id),
                    "annotation": self._annotate_edge(edge, pattern_type),
                }
            )

        return {"nodes": tokenized_nodes, "edges": tokenized_edges}

    def _assign_role(
        self, node: dict, all_nodes: list, pattern_type: str, index: int
    ) -> str:
        """Assign role based on pattern type and node position."""
        node_id = node.get("account_id", node.get("id", ""))

        if pattern_type == "Cycle":
            if index == 0:
                return "CYCLE_ORIGIN"
            if index == len(all_nodes) - 1:
                return "CYCLE_CLOSURE"
            return f"CYCLE_INTERMEDIARY_{index}"

        elif pattern_type == "HubAndSpoke":
            if node.get("is_hub"):
                return "HUB_NODE"
            return f"SPOKE_{str(index).zfill(3)}"

        elif pattern_type == "Smurfing":
            if node.get("is_target"):
                return "AGGREGATION_TARGET"
            return f"SOURCE_{str(index).zfill(3)}"

        elif pattern_type == "PassThrough":
            return f"PASSTHROUGH_{str(index).zfill(3)}"

        elif pattern_type == "DormantActivation":
            if node.get("is_dormant"):
                return "DORMANT_ACCOUNT"
            return f"ACTIVE_ACCOUNT_{str(index).zfill(3)}"

        elif pattern_type == "TemporalLayering":
            return f"LAYER_{str(index).zfill(3)}"

        return f"NODE_{str(index).zfill(3)}"

    def _annotate_edge(self, edge: dict, pattern_type: str) -> str:
        """Generate structural annotation for edge."""
        amount = edge.get("amount", 0)
        channel = edge.get("channel", "")

        if pattern_type == "Cycle":
            if edge.get("is_closure"):
                return (
                    "[CLOSURE_EDGE: completes directed cycle back to CYCLE_ORIGIN; "
                    f"₹{amount:,.0f} via {channel}]"
                )
            return f"[CYCLE_EDGE: ₹{amount:,.0f} via {channel}]"

        elif pattern_type == "HubAndSpoke":
            return (
                f"[FAN_{'IN' if edge.get('is_fan_in') else 'OUT'}_EDGE: "
                f"₹{amount:,.0f} via {channel}]"
            )

        elif pattern_type == "Smurfing":
            return (
                f"[FAN_IN_EDGE: one of N convergent transfers to AGGREGATION_TARGET; "
                f"₹{amount:,.0f} via {channel}]"
            )

        elif pattern_type == "PassThrough":
            return f"[PASSTHROUGH_EDGE: immediate relay; ₹{amount:,.0f} via {channel}]"

        elif pattern_type == "DormantActivation":
            return (
                f"[ACTIVATION_EDGE: dormant reactivation; ₹{amount:,.0f} via {channel}]"
            )

        elif pattern_type == "TemporalLayering":
            return (
                f"[LAYERING_EDGE: long-horizon movement; ₹{amount:,.0f} via {channel}]"
            )

        return f"[TRANSFER: ₹{amount:,.0f} via {channel}]"

    def build_llm_prompt(
        self, tokenized_subgraph: dict, risk_score: int, pattern_type: str
    ) -> str:
        """Build prompt for SAR narrative generation."""
        subgraph_text = self._format_subgraph(tokenized_subgraph)
        annotations_text = self._format_annotations(tokenized_subgraph.get("edges", []))

        return f"""You are a senior AML investigator assistant for GraphSentinel.
Analyze this flagged transaction pattern and draft a SAR narrative.

PATTERN TYPE: {pattern_type}
RISK SCORE: {risk_score}/100

TRANSACTION GRAPH (all account IDs are tokenized for privacy):
{subgraph_text}

STRUCTURAL ANNOTATIONS:
{annotations_text}

RISK SIGNALS:
- Pattern: {pattern_type}
- Risk Score: {risk_score}/100
- Nodes involved: {len(tokenized_subgraph.get("nodes", []))}
- Edges involved: {len(tokenized_subgraph.get("edges", []))}

Write a 3-paragraph SAR narrative explaining:
1. What suspicious pattern was detected and why it is suspicious
2. The timeline and amounts involved
3. Recommended investigator actions

Use only the token labels (CYCLE_ORIGIN, HUB_NODE, etc.) — do not invent account numbers.
Be specific about amounts and channels."""

    def _format_subgraph(self, tokenized_subgraph: dict) -> str:
        """Format subgraph for LLM prompt."""
        lines = []
        for node in tokenized_subgraph.get("nodes", []):
            lines.append(f"  - {node.get('token', 'UNKNOWN')}")

        lines.append("")
        for edge in tokenized_subgraph.get("edges", []):
            sender = edge.get("sender_id", "?")
            receiver = edge.get("receiver_id", "?")
            amount = edge.get("amount", 0)
            channel = edge.get("channel", "UNKNOWN")
            annotation = edge.get("annotation", "")
            lines.append(
                f"  {sender} → {receiver} | ₹{amount:,.0f} | {channel} | {annotation}"
            )

        return "\n".join(lines)

    def _format_annotations(self, edges: list) -> str:
        """Format edge annotations for LLM prompt."""
        if not edges:
            return "  No structural annotations available."
        return "\n".join(
            f"  - {e.get('annotation', '')}" for e in edges if e.get("annotation")
        )

    def get_session_info(self) -> dict:
        """Get session metadata (for debugging, not for logging real IDs)."""
        return {
            "tokens_issued": len(self._vault),
            "session_salt_prefix": self.session_salt[:8]
            + "...",  # Privacy: no full salt
        }


# Global vault instance for request lifecycle
_vault_instance: Optional[TokenVault] = None


def get_vault() -> TokenVault:
    """Get or create the current session's TokenVault."""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = TokenVault()
    return _vault_instance


def reset_vault() -> None:
    """Reset vault for new session (called on pipeline restart)."""
    global _vault_instance
    _vault_instance = None
