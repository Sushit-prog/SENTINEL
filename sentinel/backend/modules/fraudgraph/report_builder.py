import os
import io
import csv
import json
import uuid
import zipfile
import logging
from datetime import datetime
from typing import List, Dict, Any
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


# ── EVIDENCE KIT ──────────────────────────────────────────────────────────────

LEGAL_DISCLAIMER = (
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


def build_evidence_kit(
    session_id: str,
    entities: List[Any],
    relationships: List[Any],
    clusters: List[Any],
    risk_level: str,
    risk_score: float,
    llm_summary: str,
    graph_html: str,
    neo4j_connected: bool,
) -> bytes:
    """
    Build a court-admissible evidence kit as a ZIP file.
    Contains: PDF report, graph HTML, entity CSV, analysis JSON, manifest.
    Returns ZIP bytes (in-memory, no temp files).
    """
    buf = io.BytesIO()
    short_id = session_id[:8].upper()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # 1. PDF report (from disk if exists)
        pdf_filename = f"SENTINEL_FRAUD_INTELLIGENCE_{short_id}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                zf.writestr(pdf_filename, f.read())
        else:
            zf.writestr(pdf_filename, b"PDF not available")

        # 2. Graph HTML
        zf.writestr("graph_visualization.html", graph_html or "<html><body>Graph not available</body></html>")

        # 3. Entity CSV
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["entity_id", "type", "value", "first_seen", "risk_flags"])
        for e in entities:
            eid = getattr(e, "id", "") if hasattr(e, "id") else e.get("id", "")
            etype = getattr(e, "type", "") if hasattr(e, "type") else e.get("type", "")
            if hasattr(etype, "value"):
                etype = etype.value
            evalue = getattr(e, "value", "") if hasattr(e, "value") else e.get("value", "")
            meta = getattr(e, "metadata", {}) if hasattr(e, "metadata") else e.get("metadata", {})
            source = meta.get("source", "unknown") if isinstance(meta, dict) else "unknown"
            writer.writerow([eid, etype, evalue, source, ""])
        zf.writestr("entities.csv", csv_buf.getvalue())

        # 4. Analysis JSON
        analysis_data = {
            "session_id": session_id,
            "generated_at": now,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "entities": [
                {
                    "id": getattr(e, "id", "") if hasattr(e, "id") else e.get("id", ""),
                    "type": getattr(e, "type", "") if hasattr(e, "type") else e.get("type", ""),
                    "value": getattr(e, "value", "") if hasattr(e, "value") else e.get("value", ""),
                    "metadata": getattr(e, "metadata", {}) if hasattr(e, "metadata") else e.get("metadata", {}),
                }
                for e in entities
            ],
            "relationships": [
                {
                    "from_id": getattr(r, "from_id", "") if hasattr(r, "from_id") else r.get("from_id", ""),
                    "to_id": getattr(r, "to_id", "") if hasattr(r, "to_id") else r.get("to_id", ""),
                    "rel_type": getattr(r, "rel_type", "") if hasattr(r, "rel_type") else r.get("rel_type", ""),
                    "weight": getattr(r, "weight", 1.0) if hasattr(r, "weight") else r.get("weight", 1.0),
                }
                for r in relationships
            ],
            "clusters": [
                {
                    "cluster_id": getattr(c, "cluster_id", 0) if hasattr(c, "cluster_id") else c.get("cluster_id", 0),
                    "nodes": getattr(c, "nodes", []) if hasattr(c, "nodes") else c.get("nodes", []),
                    "size": getattr(c, "size", 0) if hasattr(c, "size") else c.get("size", 0),
                    "hub_node": getattr(c, "hub_node", None) if hasattr(c, "hub_node") else c.get("hub_node", None),
                    "victim_count": getattr(c, "victim_count", 0) if hasattr(c, "victim_count") else c.get("victim_count", 0),
                    "risk_score": getattr(c, "risk_score", 0.0) if hasattr(c, "risk_score") else c.get("risk_score", 0.0),
                }
                for c in clusters
            ],
            "llm_summary": llm_summary,
            "neo4j_connected": neo4j_connected,
        }
        zf.writestr("analysis_data.json", json.dumps(analysis_data, indent=2, default=str))

        # 5. Manifest
        manifest = (
            f"SENTINEL FRAUD INTELLIGENCE EVIDENCE KIT\n"
            f"{'=' * 50}\n\n"
            f"Analysis ID:      {session_id}\n"
            f"Short ID:         {short_id}\n"
            f"Generated:        {now}\n"
            f"Risk Level:       {risk_level}\n"
            f"Risk Score:       {risk_score:.3f}\n"
            f"Entities:         {len(entities)}\n"
            f"Relationships:    {len(relationships)}\n"
            f"Fraud Rings:      {len(clusters)}\n\n"
            f"{'=' * 50}\n"
            f"CONTENTS:\n"
            f"{'-' * 50}\n"
            f"  1. {pdf_filename}           - PDF intelligence report\n"
            f"  2. graph_visualization.html  - Interactive network graph\n"
            f"  3. entities.csv              - Entity inventory (CSV)\n"
            f"  4. analysis_data.json        - Full structured analysis data\n"
            f"  5. manifest.txt              - This file\n\n"
            f"{'=' * 50}\n"
            f"LEGAL DISCLAIMER\n"
            f"{'-' * 50}\n"
            f"{LEGAL_DISCLAIMER}\n\n"
            f"SENTINEL - AI for Digital Public Safety | ET AI Hackathon 2.0\n"
        )
        zf.writestr("manifest.txt", manifest)

    buf.seek(0)
    return buf.getvalue()
