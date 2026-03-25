"""
One-page summary PDF for GraphSentinel — PSBs Hackathon 2026 submission.
Creates a professional summary suitable for judges and upload to Google Drive.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_project_summary_pdf() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#1E3A5F")
    green = colors.HexColor("#15803D")
    orange = colors.HexColor("#C2410C")

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=22,
        textColor=accent,
        spaceAfter=4,
        leading=26,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=accent,
        spaceBefore=10,
        spaceAfter=4,
        leading=14,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=12,
        bulletIndent=4,
    )

    story = []

    story.append(Paragraph("GraphSentinel", title_style))
    story.append(
        Paragraph(
            "AI-Powered Real-Time Fund Flow Fraud Detection for Banks",
            subtitle_style,
        )
    )
    story.append(
        Paragraph(
            "Team Elida · MMIT Pune · PSBs Hackathon Series 2026 · Grand Finale — March 27, VIT Pune",
            ParagraphStyle(
                "meta", parent=body_style, fontSize=8, textColor=colors.grey
            ),
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=8))

    detection_data = [
        ["Fraud Pattern", "Algorithm", "ML Score"],
        [
            "Cycle / Circular Transactions",
            "DFS cycle detection + Tarjan SCC",
            "Isolation Forest + XGBoost",
        ],
        [
            "Smurfing (Fan-in)",
            "In-degree threshold + amount clustering",
            "Isolation Forest + XGBoost",
        ],
        [
            "Hub-and-Spoke",
            "Betweenness centrality + degree analysis",
            "Isolation Forest + XGBoost",
        ],
        [
            "Pass-Through Nodes",
            "In-out ratio analysis + Louvain",
            "Isolation Forest + XGBoost",
        ],
        [
            "Dormant Account Activation",
            "Recency scoring + motif detection",
            "Isolation Forest",
        ],
        [
            "Temporal Layering",
            "Reverse BFS + time-window analysis",
            "Isolation Forest + XGBoost",
        ],
    ]
    detection_table = Table(detection_data, colWidths=[5.5 * cm, 6 * cm, 4.5 * cm])
    detection_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F3F4F6")],
                ),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("TEXTCOLOR", (0, 1), (0, -1), accent),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(Paragraph("Detection Capabilities", heading_style))
    story.append(detection_table)
    story.append(Spacer(1, 8))

    stack_data = [
        ["Component", "Technology"],
        ["Backend API", "FastAPI + Pydantic v2"],
        ["Graph Engine", "NetworkX + Neo4j (fallback)"],
        ["ML — Anomaly", "Isolation Forest + XGBoost"],
        ["ML — Features", "10 graph-structural features per node"],
        ["Vector Store", "ChromaDB (RAG for chatbot)"],
        ["Streaming", "Redpanda / Kafka (live mode)"],
        ["Auth", "JWT Bearer tokens + RBAC"],
        ["Privacy", "TokenVault SHA-256 per-session tokenization"],
        ["LLM Agent", "LangChain + OpenRouter (Claude/Sonnet)"],
        ["PDF Export", "ReportLab — FIU-IND SAR format"],
        ["Cache", "Redis (demo + production)"],
    ]
    stack_table = Table(stack_data, colWidths=[5 * cm, 11 * cm])
    stack_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#F9FAFB"), colors.HexColor("#F3F4F6")],
                ),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (0, -1), accent),
            ]
        )
    )

    left_col = [
        Paragraph("Tech Stack", heading_style),
        stack_table,
    ]

    right_col = [
        Paragraph("Key Differentiators", heading_style),
        Paragraph(
            "🔐 Privacy-Preserving TokenVault — SHA-256 per-session tokenization ensures raw account IDs never reach the LLM or frontend. Complies with data minimization principles.",
            bullet_style,
        ),
        Spacer(1, 4),
        Paragraph(
            "🤖 LangChain Agent — Conversational SAR chatbot with 4 tools: alert lookup, subgraph retrieval, SAR drafting, and similar case analysis.",
            bullet_style,
        ),
        Spacer(1, 4),
        Paragraph(
            "📊 6 Advanced Algorithms — Tarjan SCC, Louvain community detection, PageRank, Betweenness centrality, temporal motifs, reverse BFS.",
            bullet_style,
        ),
        Spacer(1, 4),
        Paragraph(
            "⚡ Streaming Mode — CSV → Kafka → Detection pipeline processes transactions in real-time batches of 500 or every 10 seconds.",
            bullet_style,
        ),
        Spacer(1, 4),
        Paragraph(
            "📄 FIU-IND PDF Export — Generates printable SAR reports directly from detected alerts with risk breakdown.",
            bullet_style,
        ),
        Spacer(1, 4),
        Paragraph(
            "🔄 Self-Improving — Feedback loop adjusts scoring weights based on investigator confirmed/false-positive decisions.",
            bullet_style,
        ),
    ]

    from reportlab.platypus import KeepInFrame

    half = KeepInFrame(8 * cm, 14 * cm, left_col)
    half2 = KeepInFrame(8 * cm, 14 * cm, right_col)
    two_col = [[half, half2]]
    two_col_table = Table(two_col, colWidths=[8.5 * cm, 8.5 * cm])
    two_col_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(two_col_table)

    story.append(Spacer(1, 6))
    story.append(
        HRFlowable(
            width="100%", thickness=0.5, color=colors.HexColor("#D1D5DB"), spaceBefore=4
        )
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=body_style,
        fontSize=7.5,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph(
            "GraphSentinel · Team Elida · VOIS Innovation Marathon 2.0 Winners · PSBs Hackathon Series 2026 · www.graphsentinel.ai",
            footer_style,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    pdf_bytes = generate_project_summary_pdf()
    output_path = "C:/Users/pshin/CODEE/bank/GraphSentinel_Summary.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Written: {output_path} ({len(pdf_bytes):,} bytes)")
