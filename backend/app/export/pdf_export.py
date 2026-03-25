"""
PDF SAR Export — Generates printable Suspicious Activity Reports.

Format follows FIU-IND STR requirements with:
  - Header: GraphSentinel branding + alert metadata
  - Pattern analysis section
  - Transaction subgraph (tokenized for privacy)
  - Risk scoring breakdown
  - Investigator notes section
  - Footer: generation timestamp + classification
"""

import io
from datetime import datetime
from typing import Any, Dict, List

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
        KeepTogether,
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    _HAS_REPORTLAB = True

    RISK_COLOR = {
        "Critical": colors.HexColor("#DC2626"),
        "High": colors.HexColor("#EA580C"),
        "Medium": colors.HexColor("#D97706"),
        "Low": colors.HexColor("#65A30D"),
        "Unknown": colors.HexColor("#6B7280"),
    }
except ImportError:
    _HAS_REPORTLAB = False
    RISK_COLOR = {
        "Critical": "#DC2626",
        "High": "#EA580C",
        "Medium": "#D97706",
        "Low": "#65A30D",
        "Unknown": "#6B7280",
    }
    colors = None  # type: ignore[assignment]

PATTERN_DISPOSITION = {
    "Cycle": "Initiate STR; freeze cycle accounts; contact counterpart banks",
    "HubAndSpoke": "File STR; suspend hub account; escalate to senior compliance officer",
    "Smurfing": "File STR immediately; CTR filing for sub-threshold transactions",
    "PassThrough": "Block account pending source-of-funds verification; file STR",
    "DormantActivation": "Suspend account; KYC re-verification; file STR",
    "TemporalLayering": "File STR; request transaction history from all connected accounts",
    "Unknown": "Escalate to compliance officer for pattern assessment",
}


def _risk_band(score: float) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def generate_alert_pdf(alert: Dict[str, Any]) -> bytes:
    """Generate a SAR PDF for a single alert. Returns PDF as bytes."""
    if not _HAS_REPORTLAB:
        raise RuntimeError("reportlab not installed")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"GraphSentinel SAR — Alert {alert.get('alert_id', 'UNKNOWN')}",
        author="GraphSentinel AML System",
        subject="Suspicious Activity Report",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Title_Custom",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.HexColor("#1E3A5F"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading1_Custom",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor("#1E3A5F"),
            spaceBefore=14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2_Custom",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body_Custom",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Mono",
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7,
            textColor=colors.HexColor("#9CA3AF"),
            alignment=TA_CENTER,
        )
    )

    story: List[Any] = []

    # ── Header ──────────────────────────────────────────────────────────
    story.append(Paragraph("🔍 GraphSentinel", styles["Title_Custom"]))
    story.append(
        Paragraph(
            "Suspicious Activity Report — Confidential",
            styles["Heading2_Custom"],
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A5F"))
    )
    story.append(Spacer(1, 4 * mm))

    # ── Alert Metadata ──────────────────────────────────────────────────
    score = alert.get("risk_score", 0)
    band = _risk_band(score)
    pattern = alert.get("pattern_type", "Unknown")
    disposition = alert.get(
        "disposition", PATTERN_DISPOSITION.get(pattern, "Review required")
    )

    meta_data = [
        ["Alert ID", alert.get("alert_id", "N/A")],
        ["Pattern Type", pattern],
        ["Risk Score", f"{score}/100 — {band}"],
        ["Structural Score", str(alert.get("structural_score", "N/A"))],
        ["Innocence Discount", f"{alert.get('innocence_discount', 0)}%"],
        ["Disposition", disposition],
        ["Channels", ", ".join(alert.get("channels", [])) or "N/A"],
        ["Generated", datetime.now().strftime("%d-%b-%Y %H:%M IST")],
    ]

    meta_table = Table(meta_data, colWidths=[4 * cm, 13 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                (
                    "ROWBACKGROUNDS",
                    (0, 0),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F9FAFB")],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                (
                    "TEXTCOLOR",
                    (1, 2),
                    (1, 2),
                    RISK_COLOR.get(band, colors.HexColor("#6B7280")),
                ),
                ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    # ── Scoring Signals ─────────────────────────────────────────────────
    signals = alert.get("scoring_signals", {})
    if signals:
        story.append(Paragraph("Risk Scoring Signals", styles["Heading1_Custom"]))
        signal_rows = [
            [k.replace("_", " ").title(), f"+{v} pts"]
            for k, v in signals.items()
            if v > 0
        ]
        if signal_rows:
            st = Table(signal_rows, colWidths=[10 * cm, 7 * cm])
            st.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(st)
            story.append(Spacer(1, 4 * mm))

    # ── LLM Narrative ───────────────────────────────────────────────────
    narrative = alert.get("llm_explanation", "")
    if narrative:
        story.append(Paragraph("Investigator Narrative", styles["Heading1_Custom"]))
        story.append(Paragraph(narrative[:1500], styles["Body_Custom"]))
        story.append(Spacer(1, 4 * mm))

    # ── Subgraph ────────────────────────────────────────────────────────
    nodes = alert.get("subgraph_nodes", [])
    edges = alert.get("subgraph_edges", [])
    if nodes:
        story.append(Paragraph("Transaction Subgraph", styles["Heading1_Custom"]))
        story.append(
            Paragraph(
                f"Nodes: {len(nodes)} | Edges: {len(edges)}", styles["Body_Custom"]
            )
        )
        story.append(Spacer(1, 3 * mm))

        if edges:
            edge_rows = [["From", "To", "Amount (₹)", "Channel"]]
            for e in edges[:15]:
                if isinstance(e, str):
                    parts = e.replace("→", "|").split("|")
                    edge_rows.append(
                        [
                            parts[0].strip() if len(parts) > 0 else "?",
                            parts[1].strip() if len(parts) > 1 else "?",
                            parts[2].strip() if len(parts) > 2 else "?",
                            parts[3].strip() if len(parts) > 3 else "?",
                        ]
                    )
                elif isinstance(e, dict):
                    edge_rows.append(
                        [
                            e.get("sender_id", "?")[:20],
                            e.get("receiver_id", "?")[:20],
                            f"{e.get('amount', 0):,.0f}",
                            e.get("channel", "?")[:15],
                        ]
                    )
            et = Table(edge_rows, colWidths=[4.5 * cm, 4.5 * cm, 4 * cm, 4 * cm])
            et.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F9FAFB")],
                        ),
                        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
                    ]
                )
            )
            story.append(KeepTogether(et))
        story.append(Spacer(1, 4 * mm))

    # ── FIU Recommendation ──────────────────────────────────────────────
    story.append(Paragraph("FIU-IND Filing Recommendation", styles["Heading1_Custom"]))
    rec_color = RISK_COLOR.get(band, colors.HexColor("#6B7280"))
    rec_style = ParagraphStyle(
        name="Recommendation",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=rec_color,
        borderColor=rec_color,
        borderWidth=1,
        borderPadding=6,
        backColor=colors.HexColor("#F9FAFB"),
    )
    story.append(Paragraph(disposition, rec_style))
    story.append(Spacer(1, 6 * mm))

    # ── Footer ──────────────────────────────────────────────────────────
    story.append(
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D1D5DB"))
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "CONFIDENTIAL — FIU-IND Filing Material | GraphSentinel AML System | "
            f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M IST')}",
            styles["Disclaimer"],
        )
    )
    story.append(
        Paragraph(
            "This document contains sensitive financial information. Handle in accordance with "
            "PMLA (2002) and applicable data privacy regulations.",
            styles["Disclaimer"],
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.read()
