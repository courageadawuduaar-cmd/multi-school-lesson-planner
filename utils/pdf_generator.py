from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import re


def clean_text(value):
    if not value:
        return "-"
    value = re.sub(r"<br\s*/?>", "\n", value)
    value = re.sub(r"</?p[^>]*>", "", value)
    value = re.sub(r"</?[^>]+>", "", value)
    return value


def lesson_to_pdf(lesson, file_path):
    styles = getSampleStyleSheet()

    # Custom styles
    school_style = ParagraphStyle(
        name="SchoolTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=10
    )

    center_style = ParagraphStyle(
        name="Center",
        parent=styles["Normal"],
        alignment=TA_CENTER
    )

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []

    # ===== SCHOOL HEADER (DYNAMIC) =====
    school_name = lesson.school.name if lesson.school else "School Name"

    elements.append(Paragraph(school_name.upper(), school_style))
    elements.append(Paragraph("OFFICIAL LESSON PLAN DOCUMENT", center_style))
    elements.append(Spacer(1, 18))

    # ===== TITLE =====
    elements.append(Paragraph("<b>LESSON PLAN</b>", styles["Heading2"]))
    elements.append(Spacer(1, 14))

    # ===== LESSON DETAILS TABLE =====
    def row(label, value):
        return [
            Paragraph(f"<b>{label}</b>", styles["Normal"]),
            Paragraph(clean_text(str(value)), styles["Normal"])
        ]

    table_data = [
        row("Teacher", lesson.teacher.email),
        row("Class", lesson.class_name),
        row("Subject", lesson.subject),
        row("Lesson Topic", lesson.lesson_topic),
        row("Strand", lesson.strand),
        row("Sub Strand", lesson.sub_strand),
        row("Day", lesson.day),
        row("Period", lesson.period),
        row("Class Size", lesson.class_size),
        row("Lesson Date", lesson.lesson_date.strftime("%d %B %Y")),
        row("Week Ending", lesson.week_ending.strftime("%d %B %Y")),
        row("Performance Indicator", lesson.performance_indicator),
        row("Content Standard Code", lesson.content_standard_code),
        row("Indicator Code", lesson.indicator_code),
        row("Core Competencies", lesson.core_competencies),
        row("Keywords", lesson.keywords),
        row("Reference", lesson.reference),
    ]

    details_table = Table(table_data, colWidths=[170, 350])
    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(details_table)
    elements.append(Spacer(1, 18))

    # ===== TLR =====
    elements.append(Paragraph("<b>Teaching & Learning Resources</b>", styles["Heading3"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(clean_text(lesson.tlr), styles["Normal"]))
    elements.append(Spacer(1, 14))

    # ===== PHASES TABLE =====
    phase_table_data = [
        row("Phase 1 (Introduction)", lesson.phase1),
        row("Phase 2 (Presentation)", lesson.phase2),
        row("Phase 3 (Reflection)", lesson.phase3),
    ]

    phase_table = Table(phase_table_data, colWidths=[170, 350])
    phase_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(phase_table)
    elements.append(Spacer(1, 24))

    # ===== APPROVAL STATUS =====
    elements.append(Paragraph("<b>Approval Status</b>", styles["Heading3"]))
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(f"<b>Status:</b> {lesson.status.capitalize()}", styles["Normal"])
    )

    elements.append(Spacer(1, 40))

    # ===== HEADMASTER SIGNATURE =====
    signature_table = Table(
        [
            ["______________________________", ""],
            ["Headmaster / Headmistress", "Date"]
        ],
        colWidths=[260, 260]
    )

    signature_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(signature_table)

    doc.build(elements)