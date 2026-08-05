"""
OSMOS Executive Report Generator — Exporter (Phase 8.6)
======================================================
Export engine saving reports as Markdown (.md), styled HTML (.html), and PDF (.pdf).

Target Folder: reports/generated/
"""

import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional

from reports.report_schemas import ReportExportResult

logger = logging.getLogger("OSMOS_REPORT_EXPORTER")

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "generated")


def ensure_reports_dir_exists() -> str:
    """Ensures reports/generated/ directory exists."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR


def convert_markdown_to_html(markdown_text: str) -> str:
    """Converts raw markdown into styled HTML with modern OSMOS theme CSS."""
    # Basic markdown parsing to clean HTML
    html_lines = []
    lines = markdown_text.splitlines()

    in_table = False

    for line in lines:
        l = line.strip()
        if not l:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            html_lines.append("<br>")
            continue

        if l.startswith("# "):
            html_lines.append(f"<h1 style='color: #22d3ee; font-size: 26px; border-bottom: 2px solid #22d3ee; padding-bottom: 6px;'>{l[2:]}</h1>")
        elif l.startswith("## "):
            html_lines.append(f"<h2 style='color: #a78bfa; font-size: 20px; margin-top: 20px;'>{l[3:]}</h2>")
        elif l.startswith("### "):
            html_lines.append(f"<h3 style='color: #e2e8f0; font-size: 16px;'>{l[4:]}</h3>")
        elif l.startswith("#### "):
            html_lines.append(f"<h4 style='color: #94a3b8; font-size: 14px;'>{l[5:]}</h4>")
        elif l.startswith("> "):
            html_lines.append(f"<blockquote style='border-left: 4px solid #6366f1; padding-left: 12px; color: #cbd5e1; background: #0f172a; margin: 8px 0;'>{l[2:]}</blockquote>")
        elif l.startswith("- "):
            html_lines.append(f"<li style='color: #e2e8f0; margin-bottom: 4px;'>{l[2:]}</li>")
        elif l.startswith("|") and "|" in l[1:]:
            if not in_table:
                html_lines.append("<table style='width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px;'>")
                in_table = True
            cells = [c.strip() for c in l.split("|")[1:-1]]
            if "---" in cells[0]:
                continue  # Skip separator line
            row_html = "".join([f"<td style='border: 1px solid #334155; padding: 8px 12px;'>{c}</td>" for c in cells])
            html_lines.append(f"<tr style='background: #1e293b;'>{row_html}</tr>")
        else:
            # Inline formatting replacement
            formatted = line
            formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
            formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
            formatted = re.sub(r'`(.*?)`', r'<code style="background: #1e293b; color: #22d3ee; padding: 2px 6px; border-radius: 4px;">\1</code>', formatted)
            html_lines.append(f"<p style='color: #e2e8f0; line-height: 1.6;'>{formatted}</p>")

    if in_table:
        html_lines.append("</table>")

    body_content = "\n".join(html_lines)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OSMOS Executive Supervision Report</title>
    <style>
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #06090e;
            color: #f1f5f9;
            margin: 0;
            padding: 40px;
            max-width: 960px;
            margin-left: auto;
            margin-right: auto;
        }}
        code {{ font-family: 'JetBrains Mono', monospace; }}
        table {{ border-radius: 8px; overflow: hidden; }}
    </style>
</head>
<body>
{body_content}
</body>
</html>
"""


def save_report_markdown(markdown_text: str, file_path: str) -> bool:
    """Saves markdown text to file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return True
    except Exception as e:
        logger.error(f"Failed to save report markdown: {e}")
        return False


def save_report_html(html_text: str, file_path: str) -> bool:
    """Saves HTML text to file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        return True
    except Exception as e:
        logger.error(f"Failed to save report HTML: {e}")
        return False


def save_report_pdf(html_text: str, file_path: str) -> bool:
    """Saves report as PDF using ReportLab or HTML converter if available."""
    try:
        import reportlab  # Check availability
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Simple text extraction for ReportLab PDF story
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        for block in clean_text.splitlines():
            if block.strip():
                story.append(Paragraph(block.strip(), styles['Normal']))
                story.append(Spacer(1, 6))

        doc.build(story)
        return True
    except Exception as e:
        logger.debug(f"ReportLab PDF generation fallback: {e}")

    return False


def export_report_to_file(
    markdown_text: str,
    file_name_base: str,
    export_format: str = "markdown",
) -> ReportExportResult:
    """Exports report to target format (.md, .html, .pdf) in reports/generated/."""
    target_dir = ensure_reports_dir_exists()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    clean_base = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name_base)

    if export_format == "html":
        filename = f"{clean_base}_{timestamp}.html"
        filepath = os.path.join(target_dir, filename)
        html_text = convert_markdown_to_html(markdown_text)
        success = save_report_html(html_text, filepath)
    elif export_format == "pdf":
        filename = f"{clean_base}_{timestamp}.pdf"
        filepath = os.path.join(target_dir, filename)
        html_text = convert_markdown_to_html(markdown_text)
        success = save_report_pdf(html_text, filepath)
        if not success:
            # Fallback to HTML if PDF engine unavailable
            filename = f"{clean_base}_{timestamp}.html"
            filepath = os.path.join(target_dir, filename)
            save_report_html(html_text, filepath)
            export_format = "html (PDF fallback)"
    else:
        filename = f"{clean_base}_{timestamp}.md"
        filepath = os.path.join(target_dir, filename)
        success = save_report_markdown(markdown_text, filepath)

    if success:
        return ReportExportResult(
            file_path=filepath,
            file_name=filename,
            export_format=export_format,
            status="Success",
        )

    return ReportExportResult(
        file_path="",
        file_name=filename,
        export_format=export_format,
        status="Error",
        error_message="Failed to write report export file.",
    )
