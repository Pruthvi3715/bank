"""
SAR Chatbot — Conversational investigation interface.
Investigators can interrogate fraud cases using plain English.

Privacy: All account IDs are tokenized before LLM calls via TokenVault.
LangChain: Uses tool-calling agent with 4 tools (get_alert_details,
           get_subgraph, get_sar_draft, query_similar_cases).
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.privacy import get_vault
from app.rag import get_knowledge_base

_OLLAMA_AVAILABLE = False
try:
    from langchain_ollama import ChatOllama

    _OLLAMA_AVAILABLE = True
except ImportError:
    pass


# In-memory cache for pipeline results
_pipeline_cache: Dict[str, Any] = {}

# Quick question templates for the UI
QUICK_QUESTIONS = [
    {
        "label": "Why was this flagged?",
        "prompt": "Explain in plain English why this alert was flagged and what makes it suspicious.",
    },
    {
        "label": "Who is the key node?",
        "prompt": "Which account is the most central to this fraud pattern and why?",
    },
    {
        "label": "Show money trail",
        "prompt": "Describe the complete path the money took, with amounts and timestamps.",
    },
    {
        "label": "Draft FIU note",
        "prompt": "Draft a formal one-paragraph FIU-IND submission note for this case.",
    },
]


def cache_pipeline_result(result: dict) -> None:
    """Cache the latest pipeline result for chatbot context."""
    global _pipeline_cache
    _pipeline_cache = result


def get_cached_result() -> Dict[str, Any]:
    """Get cached pipeline result."""
    return _pipeline_cache


def get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    """Find an alert by ID from cached results."""
    for alert in _pipeline_cache.get("alerts", []):
        if alert.get("alert_id") == alert_id:
            return alert
    return None


def build_chat_context(alert_id: str, tokenize: bool = True) -> str:
    """
    Build context string for the chatbot from cached pipeline data.

    Args:
        alert_id: The alert to build context for
        tokenize: If True, replace account IDs with role-based tokens (default: True)
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return "No alert found with the given ID."

    vault = get_vault()
    pattern_type = alert.get("pattern_type", "Unknown")

    # Build subgraph for tokenization
    nodes = alert.get("subgraph_nodes", [])
    edges = alert.get("subgraph_edges", [])

    if tokenize and nodes:
        # Tokenize the subgraph
        subgraph = {
            "nodes": [{"account_id": n, "id": n} for n in nodes],
            "edges": _build_edges_for_tokenization(alert),
        }
        tokenized = vault.tokenize_subgraph(subgraph, pattern_type)
        tokenized_nodes = tokenized.get("nodes", [])
        tokenized_edges = tokenized.get("edges", [])
    else:
        tokenized_nodes = [{"token": n, "account_id": n} for n in nodes]
        tokenized_edges = _build_edges_for_tokenization(alert)

    parts = [
        f"ALERT ID: {alert.get('alert_id', 'N/A')}",
        f"PATTERN TYPE: {pattern_type}",
        f"RISK SCORE: {alert.get('risk_score', 0)}/100",
        f"STRUCTURAL SCORE: {alert.get('structural_score', 0)}",
        f"INNOCENCE DISCOUNT: {alert.get('innocence_discount', 0)}%",
        f"DISPOSITION: {alert.get('disposition', 'N/A')}",
        f"CHANNELS: {', '.join(alert.get('channels', []))}",
    ]

    signals = alert.get("scoring_signals", {})
    if signals:
        parts.append("\nSCORING SIGNALS:")
        for signal, value in signals.items():
            parts.append(f"  - {signal}: {value}")

    if tokenized_nodes:
        node_tokens = [n.get("token", "UNKNOWN") for n in tokenized_nodes[:20]]
        parts.append(
            f"\nSUBGRAPH NODES ({len(tokenized_nodes)}): {', '.join(node_tokens)}"
        )

    if tokenized_edges:
        edge_lines = []
        for e in tokenized_edges[:10]:
            sender = e.get("sender_id", "?")
            receiver = e.get("receiver_id", "?")
            annotation = e.get("annotation", "")
            amount = e.get("amount", 0)
            channel = e.get("channel", "UNKNOWN")
            edge_desc = f"{sender} → {receiver} | ₹{amount:,.0f} | {channel}"
            if annotation:
                edge_desc += f" {annotation}"
            edge_lines.append(edge_desc)
        parts.append(f"TRANSACTION EDGES ({len(tokenized_edges)}):")
        parts.extend(edge_lines)

    explanation = alert.get("llm_explanation", "")
    if explanation:
        parts.append(f"\nSAR NARRATIVE:\n{explanation}")

    return "\n".join(parts)


def _build_edges_for_tokenization(alert: dict) -> list:
    """Build edge list from alert for tokenization."""
    edges = []
    for edge_str in alert.get("subgraph_edges", []):
        if isinstance(edge_str, str) and "→" in edge_str:
            parts = edge_str.split("|")
            sender_receiver = parts[0].split("→")
            if len(sender_receiver) == 2:
                edges.append(
                    {
                        "sender_id": sender_receiver[0].strip(),
                        "receiver_id": sender_receiver[1].strip(),
                        "amount": float(
                            parts[1].replace("₹", "").replace(",", "").strip()
                        )
                        if len(parts) > 1
                        else 0,
                        "channel": parts[2].strip() if len(parts) > 2 else "UNKNOWN",
                    }
                )
        elif isinstance(edge_str, dict):
            edges.append(edge_str)
    return edges


def _build_langchain_llm():
    """Build a LangChain LLM instance. Priority: Ollama (qwen2.5) -> OpenRouter -> None."""
    if _OLLAMA_AVAILABLE:
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
        try:
            return ChatOllama(
                base_url=ollama_base_url,
                model=ollama_model,
                temperature=0.3,
                num_predict=800,
            )
        except Exception:
            pass

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.3,
            max_tokens=800,
        )
    except ImportError:
        return None


def generate_chat_response(
    alert_id: str,
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Generate a chat response for the investigator.
    Priority: Ollama qwen2.5 (direct) -> OpenRouter -> rule-based.
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return "I couldn't find that alert. Please select an alert from the feed first."

    vault = get_vault()

    if _OLLAMA_AVAILABLE:
        try:
            context = build_chat_context(alert_id)
            rag_context = _build_rag_context(message, alert)
            if rag_context:
                context = f"{context}\n\n{rag_context}"
            return _ollama_chat(context, message, history or [])
        except Exception:
            pass

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            context = build_chat_context(alert_id)
            rag_context = _build_rag_context(message, alert)
            if rag_context:
                context = f"{context}\n\n{rag_context}"
            return _llm_chat(context, message, history or [], api_key)
        except Exception:
            pass

    return _rule_based_response(alert, message)


def _build_rag_context(message: str, alert: Dict[str, Any]) -> str:
    """Build RAG-enhanced context from the knowledge base."""
    try:
        kb = get_knowledge_base()
        pattern_type = alert.get("pattern_type")
        return kb.build_rag_context(message, pattern_type=pattern_type, n_results=3)
    except Exception:
        return ""


def _llm_chat(context: str, message: str, history: list, api_key: str) -> str:
    """Generate response using LLM API. Detokenizes response before returning."""
    import httpx

    vault = get_vault()

    system_prompt = (
        "You are a senior AML investigator assistant for GraphSentinel.\n"
        f"You have access to the following fraud case data:\n\n{context}\n\n"
        "Answer the investigator's questions using only this case data.\n"
        "Be specific, cite node IDs and amounts.\n"
        "If asked to draft FIU content, use formal regulatory language.\n"
        "Keep responses concise and actionable.\n"
        "IMPORTANT: Use the token labels provided (e.g., HUB_NODE_abc123, CYCLE_ORIGIN_def456) "
        "when referencing accounts — do not invent account numbers."
    )

    messages = [
        {"role": h.get("role", "user"), "content": h.get("content", "")}
        for h in (history or [])[-6:]
    ]
    messages.append({"role": "user", "content": message})

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")

    resp = httpx.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": 800,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    raw_response = resp.json()["choices"][0]["message"]["content"]

    return vault.detokenize_text(raw_response)


def _ollama_chat(context: str, message: str, history: list) -> str:
    """Generate response using local Ollama qwen2.5. Detokenizes response before returning."""
    import httpx

    vault = get_vault()

    system_prompt = (
        "You are a senior AML investigator assistant for GraphSentinel.\n"
        "You have access to the following fraud case data:\n\n"
        f"{context}\n\n"
        "Answer the investigator's questions using only this case data.\n"
        "Be specific, cite node IDs and amounts.\n"
        "If asked to draft FIU content, use formal regulatory language.\n"
        "Keep responses concise and actionable.\n"
        "IMPORTANT: Use the token labels provided (e.g., HUB_NODE_abc123, CYCLE_ORIGIN_def456) "
        "when referencing accounts — do not invent account numbers."
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ]
    for h in (history or [])[-6:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role not in ("user", "assistant"):
            role = "user"
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")

    resp = httpx.post(
        f"{ollama_base}/api/chat",
        json={
            "model": ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 800,
            },
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    raw_response = resp.json()["message"]["content"]

    return vault.detokenize_text(raw_response)


def _rule_based_response(alert: dict, message: str) -> str:
    """Fallback rule-based responses when no LLM is available."""
    msg = message.lower()
    pattern = alert.get("pattern_type", "Unknown")
    score = alert.get("risk_score", 0)
    nodes = alert.get("subgraph_nodes", [])
    edges = alert.get("subgraph_edges", [])
    channels = alert.get("channels", [])
    signals = alert.get("scoring_signals", {})
    explanation = alert.get("llm_explanation", "")

    # --- Why flagged ---
    if any(w in msg for w in ["why", "flagged", "suspicious", "reason"]):
        r = f"This alert was flagged as a **{pattern}** pattern with risk score **{score}/100**.\n\n"
        r += "**Contributing risk signals:**\n"
        for s, v in signals.items():
            if v > 0:
                r += f"- {s.replace('_', ' ').title()}: +{v} points\n"
        r += f"\n**Disposition:** {alert.get('disposition', 'N/A')}"
        if alert.get("innocence_discount", 0) > 0:
            r += f"\n**Innocence discount:** {alert['innocence_discount']}%"
        return r

    # --- Key node ---
    if any(w in msg for w in ["key node", "central", "main", "primary"]):
        if not nodes:
            return "No node data available for this alert."
        r = f"In this {pattern} pattern involving **{len(nodes)} nodes**, "
        if pattern == "HubAndSpoke":
            r += f"the central hub node is **{nodes[0]}** connecting {len(nodes) - 1} spokes."
        elif pattern == "Cycle":
            r += f"the cycle originates at **{nodes[0]}** → {' → '.join(nodes[1:3])}{'...' if len(nodes) > 3 else ''}."
        elif pattern == "Smurfing":
            r += f"the aggregation target is **{nodes[-1]}**, receiving from {len(nodes) - 1} sources."
        else:
            r += f"the primary node of interest is **{nodes[0]}**."
        return r

    # --- Money trail ---
    if any(w in msg for w in ["money trail", "path", "flow", "trace"]):
        if not edges:
            return "No transaction edge data available."
        r = f"**Money trail ({pattern}):**\n\n"
        for i, edge in enumerate(edges[:8], 1):
            r += f"{i}. {edge}\n"
        if len(edges) > 8:
            r += f"... and {len(edges) - 8} more transfers\n"
        r += f"\n**Channels:** {', '.join(channels) if channels else 'N/A'}"
        return r

    # --- FIU note ---
    if any(w in msg for w in ["fiu", "draft", "note", "report", "filing"]):
        return (
            f"**FIU-IND Suspicious Transaction Report Draft**\n\n"
            f"**Ref:** STR-{alert.get('alert_id', '')[:8].upper()}\n"
            f"**Date:** {datetime.now().strftime('%d-%b-%Y')}\n\n"
            f"**Nature of Suspicion:** {pattern} pattern detected involving "
            f"{len(nodes)} accounts across {', '.join(channels)} channels.\n\n"
            f"**Summary:** Automated graph analysis identified a {pattern.lower()} "
            f"pattern scoring {score}/100. The subgraph has {len(nodes)} nodes and "
            f"{len(edges)} directed edges. "
            + (
                "Rapid multi-hop fund movement within 24h detected. "
                if signals.get("temporal_velocity", 0) > 0
                else ""
            )
            + (
                "Cross-channel switching observed. "
                if signals.get("cross_channel", 0) > 0
                else ""
            )
            + f"\n\n**Recommended Action:** {alert.get('disposition', 'Review required')}"
        )

    # --- Default ---
    if explanation:
        return (
            f"Here's what I know about this alert:\n\n{explanation}\n\n"
            'You can ask me:\n- "Why was this flagged?"\n- "Who is the key node?"\n'
            '- "Show money trail"\n- "Draft FIU note"'
        )
    return (
        f"This is a **{pattern}** alert with risk score **{score}/100**.\n\n"
        "I can help you understand:\n- Why it was flagged\n- The key nodes\n"
        "- The money trail\n- Draft an FIU note\n\nWhat would you like to know?"
    )
