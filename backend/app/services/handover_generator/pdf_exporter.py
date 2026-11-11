import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_handover_pdf(report_data: Dict[str, Any]) -> io.BytesIO:
    """
    Generates a professional enterprise PDF handover document using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    NAVY = colors.HexColor("#0f172a")
    TEAL = colors.HexColor("#0d9488")
    GREY_TEXT = colors.HexColor("#475569")
    LIGHT_BG = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=NAVY,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=TEAL,
        alignment=TA_LEFT
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=NAVY
    )

    meta_style = ParagraphStyle(
        'MetaCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=GREY_TEXT
    )

    story = []

    meta = report_data.get("metadata", {})
    proj_name = meta.get("project_name", "Continuum Project")
    report_title = meta.get("report_title", f"Knowledge Handover — {proj_name}")
    created_at = meta.get("generated_at", "Date not specified")
    view_mode = meta.get("view_mode", "Incoming Member View").replace("_", " ").title()

    # --- HEADER ---
    story.append(Paragraph("CONTINUUM AI", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(report_title, title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"View Mode: {view_mode} | Generated: {created_at} | Status: Official Handover Dossier", meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceBefore=4, spaceAfter=14))

    # --- 1. OVERVIEW & OBJECTIVES ---
    overview = report_data.get("1_project_overview", {})
    story.append(Paragraph(overview.get("title", "1. Project Overview"), h1_style))
    story.append(Paragraph(f"<b>Core Purpose:</b> {overview.get('purpose', 'N/A')}", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Current Stage:</b> {overview.get('stage', 'N/A')}", body_style))
    story.append(Spacer(1, 8))

    objectives = report_data.get("2_project_objectives", {}).get("objectives", [])
    if objectives:
        story.append(Paragraph("<b>Primary Objectives:</b>", body_style))
        for obj in objectives:
            story.append(Paragraph(f"• {obj}", body_style))
        story.append(Spacer(1, 8))

    # --- 2. RECOMMENDED NEXT ACTIONS (BLUEPRINT) ---
    actions = report_data.get("12_recommended_next_actions", {}).get("items", [])
    if actions:
        story.append(Paragraph("Continuity Blueprint — Priority Continuation Steps", h1_style))
        action_data = [["#", "Actionable Continuation Task"]]
        for i, a in enumerate(actions, 1):
            action_data.append([str(i), a])
        t_actions = Table(action_data, colWidths=[25, 495])
        t_actions.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
            ('TEXTCOLOR', (0,0), (-1,0), NAVY),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ]))
        story.append(t_actions)
        story.append(Spacer(1, 12))

    # --- 3. COMPLETED & PENDING TASKS ---
    completed = report_data.get("4_completed_work", {}).get("items", [])
    pending = report_data.get("6_pending_tasks", {}).get("items", [])
    
    story.append(Paragraph("Task Status & Continuity Backlog", h1_style))
    task_rows = [["Task", "Status", "Owner", "Evidence / Source"]]
    for item in completed[:5]:
        task_rows.append([item.get("title", ""), "Completed", item.get("owner", "Unknown"), item.get("source", "Doc") or "Verified"])
    for item in pending[:5]:
        task_rows.append([item.get("title", ""), "Pending", item.get("owner", "Unknown"), item.get("priority", "High").title()])
    
    t_tasks = Table(task_rows, colWidths=[180, 70, 90, 180])
    t_tasks.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ]))
    story.append(t_tasks)
    story.append(Spacer(1, 12))

    # --- 4. RISKS, BUGS & BLOCKERS ---
    risks = report_data.get("9_risks_and_blockers", {}).get("items", [])
    bugs = report_data.get("9_risks_and_blockers", {}).get("unresolved_bugs", [])
    if bugs:
        story.append(Paragraph("Unresolved Bugs & Technical Debt", h1_style))
        bug_rows = [["Code", "Title", "Classification", "Severity", "Recommended Next Action"]]
        for b in bugs[:5]:
            bug_rows.append([b.get("code", ""), b.get("title", "")[:28], b.get("classification", ""), b.get("severity", "").upper(), b.get("action", "")[:45]])
        t_bugs = Table(bug_rows, colWidths=[55, 140, 105, 55, 165])
        t_bugs.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fee2e2")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#991b1b")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ]))
        story.append(t_bugs)
        story.append(Spacer(1, 10))

    if risks:
        story.append(Paragraph("Identified Technical & Operational Risks", h1_style))
        risk_rows = [["Risk", "Severity", "Impact & Suggested Resolution"]]
        for r in risks:
            desc = f"{r.get('description', '')}\nResolution: {r.get('resolution', 'N/A')}"
            risk_rows.append([r.get("title", ""), r.get("severity", "Medium").upper(), desc])
        t_risks = Table(risk_rows, colWidths=[150, 70, 300])
        t_risks.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
            ('TEXTCOLOR', (0,0), (-1,0), NAVY),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ]))
        story.append(t_risks)
        story.append(Spacer(1, 12))

    # --- 4B. API HANDOVER INVENTORY ---
    api_inv = report_data.get("8_technical_architecture", {}).get("api_inventory", [])
    if api_inv:
        story.append(Paragraph("API Handover Inventory (Backend Endpoints)", h1_style))
        api_rows = [["Method & Path", "Status", "Module", "Coverage"]]
        for a in api_inv[:6]:
            api_rows.append([a.get("endpoint", ""), a.get("status", ""), a.get("module", ""), a.get("coverage", "")])
        t_api = Table(api_rows, colWidths=[200, 110, 110, 100])
        t_api.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
            ('TEXTCOLOR', (0,0), (-1,0), NAVY),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ]))
        story.append(t_api)
        story.append(Spacer(1, 12))

    # --- 5. EVIDENCE PASSPORT ---
    evidence_list = report_data.get("13_supporting_evidence", {}).get("items", [])
    if evidence_list:
        story.append(Paragraph("Evidence Passport (Claim Traceability)", h1_style))
        ev_rows = [["Claim", "Source Document", "Verification Status", "Direct Citation Snippet"]]
        for ev in evidence_list[:6]:
            snippet = ev.get("snippet", "")
            if len(snippet) > 85:
                snippet = snippet[:82] + "..."
            ev_rows.append([
                ev.get("claim", ""),
                f"{ev.get('document', '')} (P.{ev.get('page', 1)})",
                ev.get("status", ""),
                snippet
            ])
        t_ev = Table(ev_rows, colWidths=[130, 110, 80, 200])
        t_ev.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
            ('TEXTCOLOR', (0,0), (-1,0), NAVY),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ]))
        story.append(t_ev)
        story.append(Spacer(1, 14))

    # --- FOOTER ---
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER_COLOR, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("Continuum AI Platform • Reconstructing Knowledge, Ensuring Continuity • Verified Enterprise Handover Report", meta_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

