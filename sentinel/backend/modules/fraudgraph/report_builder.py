import os
import uuid
import logging
from datetime import datetime
from typing import List
from backend.models.fraud_models import Entity, Relationship, FraudCluster, RiskLevel

logger = logging.getLogger(__name__)

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# SENTINEL color palette (RGB tuples 0-1)
COLOR_CRITICAL = (0.80, 0.10, 0.10)
COLOR_HIGH     = (0.85, 0.40, 0.10)
COLOR_MEDIUM   = (0.85, 0.70, 0.10)
COLOR_LOW      = (0.20, 0.65, 0.30)
COLOR_DARK     = (0.10, 0.10, 0.12)
COLOR_LIGHT    = (0.95, 0.95, 0.95)
COLOR_ACCENT   = (0.00, 0.60, 0.85)


def get_risk_color(risk_level: RiskLevel):
    mapping = {
        RiskLevel.CRITICAL: COLOR_CRITICAL,
        RiskLevel.HIGH: COLOR_HIGH,
        RiskLevel.MEDIUM: COLOR_MEDIUM,
        RiskLevel.LOW: COLOR_LOW,
    }
    return mapping.get(risk_level, COLOR_LOW)


def generate_fraud_report(
    session_id: str,
    entities: List[Entity],
    relationships: List[Relationship],
    clusters: List[FraudCluster],
    risk_level: RiskLevel,
    risk_score: float,
    llm_summary: str,
    neo4j_connected: bool
) -> str:
    """
    Generate PDF intelligence package.
    Returns file path of generated PDF.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

        filename = f"SENTINEL_FRAUD_INTELLIGENCE_{session_id[:8].upper()}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="SENTINEL Fraud Intelligence Package",
            author="SENTINEL Digital Public Safety Platform"
        )

        styles = getSampleStyleSheet()
        risk_rgb = get_risk_color(risk_level)
        risk_color_rl = colors.Color(*risk_rgb)

        # Custom styles
        style_header = ParagraphStyle(
            "SentinelHeader",
            parent=styles["Heading1"],
            textColor=colors.white,
            backColor=colors.Color(*COLOR_DARK),
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=6,
            spaceBefore=6,
        )
        style_section = ParagraphStyle(
            "SentinelSection",
            parent=styles["Heading2"],
            textColor=colors.Color(*COLOR_ACCENT),
            fontSize=13,
            spaceBefore=14,
            spaceAfter=6,
            borderPadding=(0, 0, 4, 0),
        )
        style_body = ParagraphStyle(
            "SentinelBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            alignment=TA_JUSTIFY,
        )
        style_meta = ParagraphStyle(
            "SentinelMeta",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        style_verdict = ParagraphStyle(
            "SentinelVerdict",
            parent=styles["Heading1"],
            textColor=risk_color_rl,
            fontSize=28,
            alignment=TA_CENTER,
            spaceBefore=8,
            spaceAfter=8,
        )

        story = []

        # HEADER
        story.append(Paragraph("SENTINEL", style_header))
        story.append(Paragraph("Digital Public Safety Intelligence Platform", style_meta))
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.Color(*COLOR_ACCENT)))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "<font color='#FF4444'><b>CONFIDENTIAL - FOR LAW ENFORCEMENT USE ONLY</b></font>",
            ParagraphStyle("warn", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9)
        ))
        story.append(Spacer(1, 0.4*cm))

        # RISK VERDICT
        story.append(Paragraph(f"RISK ASSESSMENT: {risk_level.value}", style_verdict))
        story.append(Paragraph(f"Composite Risk Score: {risk_score:.1%}", style_meta))
        story.append(Spacer(1, 0.4*cm))

        # META TABLE
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_data = [
            ["Session ID", session_id],
            ["Generated", now],
            ["Entities Detected", str(len(entities))],
            ["Relationships Mapped", str(len(relationships))],
            ["Fraud Rings Identified", str(len(clusters))],
            ["Neo4j Graph Persisted", "YES" if neo4j_connected else "NO (in-memory mode)"],
        ]
        meta_table = Table(meta_data, colWidths=[5*cm, 11*cm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.15, 0.15, 0.18)),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.Color(*COLOR_ACCENT)),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.3, 0.3, 0.3)),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.5*cm))

        # SECTION 1: INTELLIGENCE SUMMARY
        story.append(Paragraph("1. Intelligence Summary", style_section))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))
        summary_text = llm_summary.replace("\n", "<br/>")
        story.append(Paragraph(summary_text, style_body))
        story.append(Spacer(1, 0.4*cm))

        # SECTION 2: ENTITY INVENTORY
        story.append(Paragraph("2. Entity Inventory", style_section))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))

        entity_data = [["#", "Type", "Value", "Source"]]
        for i, entity in enumerate(entities, 1):
            entity_data.append([
                str(i),
                entity.type.value,
                entity.value,
                entity.metadata.get("source", "unknown")
            ])

        entity_table = Table(entity_data, colWidths=[1*cm, 3*cm, 9*cm, 3*cm])
        entity_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(*COLOR_DARK)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(entity_table)
        story.append(Spacer(1, 0.4*cm))

        # SECTION 3: FRAUD RING ANALYSIS
        story.append(Paragraph("3. Fraud Ring Analysis", style_section))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))

        if clusters:
            cluster_data = [["Ring #", "Size", "Victims", "Hub Node", "Risk Score"]]
            for cluster in clusters:
                hub_display = cluster.hub_node[:30] if cluster.hub_node else "N/A"
                cluster_data.append([
                    str(cluster.cluster_id + 1),
                    str(cluster.size),
                    str(cluster.victim_count),
                    hub_display,
                    f"{cluster.risk_score:.1%}"
                ])
            cluster_table = Table(cluster_data, colWidths=[2*cm, 2*cm, 2*cm, 8*cm, 3*cm])
            cluster_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(*COLOR_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(cluster_table)
        else:
            story.append(Paragraph("No fraud rings detected. Insufficient data for clustering.", style_body))

        story.append(Spacer(1, 0.4*cm))

        # SECTION 4: LEGAL DISCLAIMER
        story.append(PageBreak())
        story.append(Paragraph("4. Legal Disclaimer & Data Governance", style_section))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))
        disclaimer = (
            "This intelligence package has been generated by SENTINEL - an AI-assisted fraud analysis platform. "
            "The findings presented herein are based on pattern analysis and machine learning inference and should "
            "be treated as investigative leads, NOT as conclusive evidence of criminal activity. "
            "All information must be independently verified by authorized law enforcement personnel before being "
            "used in any legal proceeding. The platform operators accept no liability for actions taken based "
            "solely on this report. This document is classified as CONFIDENTIAL and may only be shared with "
            "authorized personnel in accordance with applicable data protection laws, including the Information "
            "Technology Act, 2000 and the Digital Personal Data Protection Act, 2023 (India). "
            "Unauthorized disclosure is prohibited."
        )
        story.append(Paragraph(disclaimer, style_body))
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.Color(*COLOR_DARK)))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "SENTINEL - AI for Digital Public Safety | ET AI Hackathon 2.0",
            style_meta
        ))

        doc.build(story)
        logger.info(f"Fraud intelligence PDF generated: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise
