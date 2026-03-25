"""
LangChain SAR Agent — Conversational investigation with tool-use.

Provides 4 tools:
  1. get_alert_details   — Full alert metadata + risk score
  2. get_subgraph       — Tokenized transaction graph
  3. get_sar_draft      — Pre-generated SAR narrative
  4. query_similar_cases — Historical alerts with same pattern type

The agent decides when to call tools vs. answer directly.
"""

import json
from typing import List, Dict, Any, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from app.sar_chatbot import (
    build_chat_context,
    cache_pipeline_result,
    get_alert_by_id,
    get_cached_result,
)


@tool
def get_alert_details(alert_id: str) -> str:
    """
    Get full details of a fraud alert including risk score, pattern type,
    scoring signals, innocence discount, and disposition.

    Use this tool whenever the investigator asks about an alert's details,
    risk score, pattern type, or why it was flagged.

    Args:
        alert_id: The unique identifier of the alert (e.g., "ALERT_001")
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return f"Alert '{alert_id}' not found. Available alerts: {list_alerts()}"
    return json.dumps(
        {
            "alert_id": alert.get("alert_id"),
            "pattern_type": alert.get("pattern_type", "Unknown"),
            "risk_score": alert.get("risk_score", 0),
            "structural_score": alert.get("structural_score", 0),
            "ml_if_score": alert.get("ml_if_score", 0),
            "ml_gb_score": alert.get("ml_gb_score", 0),
            "innocence_discount": alert.get("innocence_discount", 0),
            "disposition": alert.get("disposition", "N/A"),
            "channels": alert.get("channels", []),
            "scoring_signals": alert.get("scoring_signals", {}),
            "node_count": len(alert.get("subgraph_nodes", [])),
            "edge_count": len(alert.get("subgraph_edges", [])),
            "created_at": alert.get("created_at", "N/A"),
        },
        indent=2,
    )


@tool
def get_subgraph(alert_id: str) -> str:
    """
    Get the transaction subgraph for a specific alert.
    Returns tokenized node IDs and directed edges with amounts and channels.

    Use this tool when the investigator asks about specific accounts,
    transaction paths, money flow, or the graph structure.

    Args:
        alert_id: The unique identifier of the alert
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return f"Alert '{alert_id}' not found. Available alerts: {list_alerts()}"
    subgraph_nodes = alert.get("subgraph_nodes", [])
    subgraph_edges = alert.get("subgraph_edges", [])
    pattern_type = alert.get("pattern_type", "Unknown")
    risk_score = alert.get("risk_score", 0)

    edge_lines = []
    for edge_str in subgraph_edges[:15]:
        if isinstance(edge_str, str):
            edge_lines.append(edge_str)
        elif isinstance(edge_str, dict):
            amount = edge_str.get("amount", 0)
            channel = edge_str.get("channel", "UNKNOWN")
            sender = edge_str.get("sender_id", "?")
            receiver = edge_str.get("receiver_id", "?")
            edge_lines.append(f"{sender} → {receiver} | ₹{amount:,.0f} | {channel}")

    return json.dumps(
        {
            "alert_id": alert_id,
            "pattern_type": pattern_type,
            "risk_score": risk_score,
            "nodes": subgraph_nodes,
            "edge_count": len(subgraph_edges),
            "edges": edge_lines,
        },
        indent=2,
    )


@tool
def get_sar_draft(alert_id: str) -> str:
    """
    Get the pre-generated SAR narrative for an alert.

    Use this tool when the investigator asks about the SAR draft,
    narrative, explanation, or wants a summary of the fraud case.

    Args:
        alert_id: The unique identifier of the alert
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        return f"Alert '{alert_id}' not found. Available alerts: {list_alerts()}"

    narrative = alert.get("llm_explanation", "")
    if not narrative:
        pattern = alert.get("pattern_type", "Unknown")
        score = alert.get("risk_score", 0)
        nodes = len(alert.get("subgraph_nodes", []))
        edges = len(alert.get("subgraph_edges", []))
        narrative = (
            f"Automated analysis identified a {pattern} pattern scoring {score}/100. "
            f"The subgraph contains {nodes} nodes and {edges} directed transaction edges. "
            f"No pre-generated narrative available."
        )
    return narrative


@tool
def query_similar_cases(pattern_type: str, limit: int = 5) -> str:
    """
    Find similar fraud cases from pipeline history by pattern type.
    Useful for comparing current alert against historical cases.

    Use this tool when the investigator asks about similar cases,
    historical patterns, or how this compares to past alerts.

    Args:
        pattern_type: Filter by fraud pattern — one of:
            Cycle | Smurfing | HubAndSpoke | PassThrough | DormantActivation | TemporalLayering
        limit: Maximum number of similar cases to return (default: 5)
    """
    cached = get_cached_result()
    alerts = cached.get("alerts", [])
    similar = [
        {
            "alert_id": a.get("alert_id"),
            "pattern_type": a.get("pattern_type"),
            "risk_score": a.get("risk_score", 0),
            "node_count": len(a.get("subgraph_nodes", [])),
            "edge_count": len(a.get("subgraph_edges", [])),
            "channels": a.get("channels", []),
        }
        for a in alerts
        if a.get("pattern_type") == pattern_type
    ]
    return json.dumps(
        {
            "pattern_type": pattern_type,
            "similar_count": len(similar),
            "cases": similar[:limit],
        },
        indent=2,
    )


def list_alerts() -> List[str]:
    """Return list of available alert IDs from cached results."""
    cached = get_cached_result()
    return [
        a.get("alert_id", "") for a in cached.get("alerts", []) if a.get("alert_id")
    ]


TOOLS = [get_alert_details, get_subgraph, get_sar_draft, query_similar_cases]


def build_sar_agent_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "You are a senior AML (Anti-Money Laundering) investigator assistant "
                    "for GraphSentinel — an AI-powered fraud detection system.\n\n"
                    "Your role is to help investigators understand fraud alerts, "
                    "interpret graph analysis results, and draft regulatory filings.\n\n"
                    "IMPORTANT GUIDELINES:\n"
                    "1. Always use the provided TOOLS to look up case data before answering.\n"
                    "2. Be specific: cite node IDs, amounts, and pattern types.\n"
                    "3. Use formal language when discussing FIU-IND regulatory filings.\n"
                    "4. Keep responses concise and actionable.\n"
                    "5. If an alert_id is not provided, ask the investigator to specify one.\n"
                    "6. If asked about FIU notes, SAR drafts, or filing language, "
                    "always use the get_sar_draft tool.\n\n"
                    "GRAPH SENTINEL PATTERN TYPES:\n"
                    "- Cycle: Round-trip money laundering (A→B→C→A)\n"
                    "- Smurfing: Multiple small transactions below CTR threshold\n"
                    "- HubAndSpoke: Central mule aggregating from many sources and fanning out\n"
                    "- PassThrough: Accounts that immediately forward nearly all received funds\n"
                    "- DormantActivation: Previously inactive accounts suddenly receiving high volume\n"
                    "- TemporalLayering: Multi-hop fund movement across extended time periods"
                )
            ),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


def create_sar_agent(llm):
    agent = create_tool_calling_agent(llm, TOOLS, build_sar_agent_prompt())
    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
    )


def run_sar_agent(
    user_message: str,
    alert_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    llm=None,
) -> str:
    """
    Run the LangChain SAR agent with a user message.

    Args:
        user_message: The investigator's question
        alert_id: Optional default alert context
        chat_history: Previous chat messages for context
        llm: LLM instance (e.g., ChatOpenAI or ChatAnthropic)

    Returns:
        Agent's text response
    """
    if llm is None:
        return _rule_based_fallback(user_message, alert_id)

    try:
        executor = create_sar_agent(llm)

        history_messages = []
        for h in (chat_history or [])[-6:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            if role == "user":
                history_messages.append(HumanMessage(content=content))
            else:
                history_messages.append(SystemMessage(content=f"Assistant: {content}"))

        result = executor.invoke(
            {
                "input": user_message,
                "chat_history": history_messages,
            }
        )
        return result.get("output", "I couldn't generate a response. Please try again.")
    except Exception as e:
        return _rule_based_fallback(user_message, alert_id, error=str(e))


def _rule_based_fallback(
    message: str,
    alert_id: Optional[str] = None,
    error: str = "",
) -> str:
    if error:
        return f"(Tool unavailable: {error}) "
    if not alert_id:
        alerts = list_alerts()
        return f"Please specify an alert ID. Available alerts: {', '.join(alerts) or 'none'}"
    alert = get_alert_by_id(alert_id)
    if not alert:
        return f"Alert '{alert_id}' not found."
    context = build_chat_context(alert_id, tokenize=False)
    return f"Alert context:\n{context}\n\nYour question: {message}"
