import os
import hashlib
from typing import Dict, Any, List
from pathlib import Path
import json

from app.privacy.token_vault import TokenVault, get_vault

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    OpenAI = None


_ROLE_MAPS = {
    "Cycle": lambda idx, is_first: "CYCLE_ORIGIN"
    if is_first
    else f"CYCLE_HOP_{idx:02d}",
    "Smurfing": lambda idx, _: f"STRUCTURING_SOURCE_{idx:02d}",
    "HubAndSpoke": lambda idx, is_first: "MULE_HUB" if is_first else f"SPOKE_{idx:02d}",
    "PassThrough": lambda idx, _: f"PASSTHROUGH_NODE_{idx:02d}",
    "DormantActivation": lambda idx, _: f"DORMANT_NODE_{idx:02d}",
}


def _assign_roles(pattern: str, edges: List[Dict[str, Any]]) -> Dict[str, str]:
    """Return a mapping of account_id -> role label."""
    role_fn = _ROLE_MAPS.get(pattern, lambda idx, _: f"NODE_{idx:02d}")
    roles: Dict[str, str] = {}
    counter = 0
    for edge in edges:
        for key in ("sender_id", "receiver_id"):
            node = edge.get(key, "")
            if node and node not in roles:
                roles[node] = role_fn(counter, counter == 0)
                counter += 1
    return roles


class ReportAgent:
    """
    Generates LLM explanations and formats SAR documents for investigators.

    Flow: assign roles → tokenize node IDs → call LLM → detokenize response.
    scored_subgraph is never mutated; a new dict is returned.
    """

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", os.getenv("OPENROUTER_API_KEY"))
        self.base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "GraphSentinel",
                },
            )

    # ------------------------------------------------------------------
    # Public API — does NOT mutate scored_subgraph
    # ------------------------------------------------------------------
    def generate_sar_draft(
        self, scored_subgraph: Dict[str, Any], edges: List[Dict[str, Any]]
    ) -> str:
        """
        Returns the LLM narrative string.  Does not modify scored_subgraph.
        Uses the shared session vault from app.privacy for consistent tokenization.
        """
        vault = get_vault()
        pattern = scored_subgraph.get("pattern_type", "Unknown")

        # 1. Assign topology roles to each node
        node_roles = _assign_roles(pattern, edges)

        # 2. Build tokenized edge list
        tokenized_edges = []
        for edge in edges:
            sender = edge.get("sender_id", "")
            receiver = edge.get("receiver_id", "")
            tok_s = vault.tokenize(sender, node_roles.get(sender, "NODE"))
            tok_r = vault.tokenize(receiver, node_roles.get(receiver, "NODE"))
            tokenized_edges.append(
                {
                    "sender": tok_s,
                    "receiver": tok_r,
                    "amount": edge.get("amount", 0),
                    "timestamp": edge.get("timestamp", ""),
                    "channel": edge.get("channel", ""),
                }
            )

        demo_mode = str(os.getenv("DEMO_MODE", "")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if demo_mode:
            cache_dir = (
                Path(__file__).resolve().parents[3] / "demo_cache" / "explanations"
            )
            cache_dir.mkdir(parents=True, exist_ok=True)
            key_payload = {
                "pattern_type": pattern,
                "final_score": scored_subgraph.get("final_score"),
                "scoring_signals": scored_subgraph.get("scoring_signals", {}),
                "edges": tokenized_edges,
            }
            cache_key = hashlib.sha256(
                json.dumps(key_payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            path = cache_dir / f"{cache_key}.txt"
            if path.exists():
                return vault.detokenize(path.read_text(encoding="utf-8"))

        # 3. Build prompt & call LLM
        prompt = self._format_prompt(scored_subgraph, tokenized_edges)
        if self.client:
            try:
                response = self.client.chat.completions.create(  # type: ignore
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Anti-Money Laundering (AML) investigator "
                                "for FIU-IND. Write a concise SAR narrative from the tokenised "
                                "transaction data. Real account IDs are hidden; use the role "
                                "tokens provided."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=600,
                    temperature=0.3,
                )
                safe_narrative = response.choices[0].message.content or ""
            except Exception as exc:
                print(f"[ReportAgent] LLM call failed: {exc}")
                safe_narrative = self._mock_narrative(scored_subgraph)
        else:
            safe_narrative = self._mock_narrative(scored_subgraph)

        # 4. Detokenize (replace role tokens with real IDs in the output)
        if demo_mode:
            try:
                path.write_text(safe_narrative, encoding="utf-8")
            except Exception:
                pass
        return vault.detokenize(safe_narrative)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _format_prompt(
        self,
        scored_subgraph: Dict[str, Any],
        tokenized_edges: List[Dict[str, Any]],
    ) -> str:
        pattern = scored_subgraph.get("pattern_type")
        score = scored_subgraph.get("final_score")
        signals = scored_subgraph.get("scoring_signals", {})

        lines = [
            f"Pattern Type: {pattern}",
            f"System Risk Score: {score}/100",
            "",
            "Active Scoring Signals:",
        ]
        for sig, val in signals.items():
            if val > 0:
                lines.append(f"  - {sig}: +{val}")

        lines += ["", "Transaction Edges (tokenised):"]
        for e in tokenized_edges:
            ts = e["timestamp"]
            if hasattr(ts, "isoformat"):
                ts = ts.isoformat()
            lines.append(
                f"  [{ts}] {e['sender']} --INR {e['amount']:,.0f} via {e['channel']}--> {e['receiver']}"
            )

        lines += [
            "",
            "Generate the FIU-IND SAR narrative using exactly this format:",
            "",
            "**PART C: Investigator Narrative**",
            "[3-5 sentences describing the suspicious activity]",
            "",
            "**Recommendation:**",
            "[1-2 sentences on required action]",
        ]
        return "\n".join(lines)

    def _mock_narrative(self, scored_subgraph: Dict[str, Any]) -> str:
        pattern = scored_subgraph.get("pattern_type", "Unknown")
        score = scored_subgraph.get("final_score", 0)
        templates = {
            "Cycle": (
                "**PART C: Investigator Narrative**\n"
                "A directed cyclic fund flow has been detected, consistent with round-tripping "
                "used to obscure beneficial ownership. Funds originating from the cycle's "
                "entry node were routed through intermediary accounts and returned to an "
                f"associated account, forming a closed loop. The system assigned a risk score "
                f"of {score}/100.\n\n"
                "**Recommendation:** Freeze all accounts in the cycle and initiate Enhanced Due "
                "Diligence (EDD) under Section 12 of PMLA. File STR with FIU-IND within 7 days."
            ),
            "Smurfing": (
                "**PART C: Investigator Narrative**\n"
                "A high fan-in structuring pattern (smurfing) has been identified. Multiple "
                "distinct source accounts transferred amounts clustered just below the ₹50,000 "
                "Cash Transaction Report threshold, converging on a single beneficiary. This is "
                f"consistent with structuring designed to avoid CTR triggers. Risk score: {score}/100.\n\n"
                "**Recommendation:** Immediately file a Suspicious Transaction Report (STR). "
                "Freeze the beneficiary account and initiate KYC re-verification on all sources."
            ),
            "HubAndSpoke": (
                "**PART C: Investigator Narrative**\n"
                "A hub-and-spoke mule network pattern has been identified. A central hub account "
                "exhibits both high in-degree (aggregation) and high out-degree (disbursement) "
                "within a short time window, characteristic of a money-mule coordinator account. "
                f"Risk score: {score}/100.\n\n"
                "**Recommendation:** Escalate to senior compliance officer. File CTR and STR for "
                "all connected accounts. Refer to law enforcement under PMLA Section 13."
            ),
            "PassThrough": (
                "**PART C: Investigator Narrative**\n"
                "A pass-through layering pattern has been detected. The flagged account exhibits "
                "near-zero fund retention — nearly all received funds are forwarded immediately, "
                f"indicating use as a mule or layering node. Risk score: {score}/100.\n\n"
                "**Recommendation:** Block outgoing transactions and initiate contact with account "
                "holder for source-of-funds verification under PMLA."
            ),
            "DormantActivation": (
                "**PART C: Investigator Narrative**\n"
                "A dormant account activation pattern has been detected. An account that was "
                "inactive for an extended period has suddenly resumed high-volume transaction "
                f"activity, a known red flag for account takeover or illicit reactivation. "
                f"Risk score: {score}/100.\n\n"
                "**Recommendation:** Suspend account activity pending KYC re-verification. "
                "Investigate whether the account has been compromised or sold."
            ),
        }
        return templates.get(
            pattern,
            (
                "**PART C: Investigator Narrative**\n"
                f"Suspicious activity detected — pattern type: {pattern}, risk score: {score}/100. "
                "Manual review required.\n\n"
                "**Recommendation:** Escalate to compliance officer for STR assessment."
            ),
        )
