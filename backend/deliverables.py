"""
Deliverable Builder module.
Generates genuine .docx, .xlsx, and .pptx files from structured JSON plans using Python.
Guarantees the LLM never generates raw file bytes.
"""

import os
import uuid
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference

from pptx import Presentation
from pptx.util import Inches as PPTInches, Pt as PPTPt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor as PPTRGBColor

from backend.config import GENERATED_DIR, logger
from backend.db import save_file_record


def sanitize_filename(name: str, default_ext: str = ".bin") -> str:
    """Sanitizes filename for safe filesystem storage."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    if not name:
        name = f"deliverable_{uuid.uuid4().hex[:6]}"
    if not any(name.lower().endswith(ext) for ext in [".docx", ".xlsx", ".pptx", ".pdf", ".txt", ".csv"]):
        name += default_ext
    return name


def generate_chart_image(block: Dict[str, Any], output_path: Path) -> bool:
    """Renders a matplotlib chart to PNG and returns True on success."""
    try:
        title = block.get("title") or block.get("text") or "Data Chart"
        rows = block.get("rows", [])
        chart_type = block.get("chart_type", "bar").lower()
        
        plt.figure(figsize=(7, 4.2), dpi=150)
        plt.style.use("ggplot" if "ggplot" in plt.style.available else "default")
        
        if rows and len(rows) >= 2:
            headers = [str(c) for c in rows[0]]
            data_rows = rows[1:]
            
            # X labels from column 0
            labels = [str(r[0]) for r in data_rows if len(r) > 0]
            
            # Numeric series from column 1..N
            num_series = len(headers) - 1
            if num_series >= 1:
                import numpy as np
                x = np.arange(len(labels))
                width = 0.8 / max(1, num_series)
                
                for i in range(num_series):
                    col_idx = i + 1
                    series_name = headers[col_idx] if col_idx < len(headers) else f"Series {col_idx}"
                    values = []
                    for r in data_rows:
                        val = 0.0
                        if col_idx < len(r):
                            try:
                                val = float(str(r[col_idx]).replace(",", "").replace("%", ""))
                            except (ValueError, TypeError):
                                val = 0.0
                        values.append(val)
                    
                    if "line" in chart_type:
                        plt.plot(labels, values, marker='o', linewidth=2, label=series_name)
                    else:
                        plt.bar(x + (i - (num_series - 1) / 2) * width, values, width, label=series_name)
                
                if "line" not in chart_type:
                    plt.xticks(x, labels, rotation=20, ha='right')
                plt.legend()
        else:
            # Fallback simple plot
            plt.bar(["Metric A", "Metric B", "Metric C"], [10, 25, 15], color="#2563eb")
            
        plt.title(title, fontsize=12, fontweight="bold", pad=12)
        plt.tight_layout()
        plt.savefig(output_path, format="png")
        plt.close()
        return True
    except Exception as e:
        logger.error(f"Error rendering chart: {e}")
        plt.close()
        return False


def build_docx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a polished Microsoft Word (.docx) document."""
    title = plan.get("title", "Engineering Report")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.docx"), ".docx")
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    doc = Document()
    
    # Title
    title_p = doc.add_heading(title, level=0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Blocks
    blocks = plan.get("blocks", [])
    for idx, b in enumerate(blocks):
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        
        if b_type == "heading":
            level = b.get("level", 1)
            doc.add_heading(text, level=min(3, max(1, level)))
            
        elif b_type == "paragraph":
            if text:
                doc.add_paragraph(text)
                
        elif b_type == "bullets":
            items = b.get("items", [])
            if not items and text:
                items = [it.strip().lstrip("-*• ") for it in text.split("\n") if it.strip()]
            for it in items:
                doc.add_paragraph(it, style="List Bullet")
                
        elif b_type == "table" and rows:
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = 'Table Grid'
            
            for r_idx, row in enumerate(rows):
                for c_idx, cell_value in enumerate(row):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = str(cell_value)
                    if r_idx == 0:
                        # Bold header
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.bold = True
                                
        elif b_type == "chart":
            chart_img = chat_dir / f"temp_chart_{idx}_{uuid.uuid4().hex[:6]}.png"
            if generate_chart_image(b, chart_img):
                doc.add_picture(str(chart_img), width=Inches(6.0))
                if chart_img.exists():
                    chart_img.unlink(missing_ok=True)
            elif text:
                doc.add_paragraph(f"[Chart: {text}]")
                
    doc.save(str(out_path))
    logger.info(f"[DELIVERABLE] DOCX created: {out_path}")
    return file_id, filename, out_path


def build_xlsx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a structured Microsoft Excel (.xlsx) workbook."""
    title = plan.get("title", "Data Sheet")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.xlsx"), ".xlsx")
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    
    # Styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1F4E78")
    thin_border = Border(
        left=Side(style='thin', color="D9D9D9"),
        right=Side(style='thin', color="D9D9D9"),
        top=Side(style='thin', color="D9D9D9"),
        bottom=Side(style='thin', color="D9D9D9")
    )
    
    # Title row
    ws.cell(row=1, column=1, value=title).font = title_font
    current_row = 3
    
    blocks = plan.get("blocks", [])
    for b in blocks:
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        
        if b_type in ("heading", "paragraph"):
            if text:
                ws.cell(row=current_row, column=1, value=text).font = Font(bold=(b_type == "heading"), size=12)
                current_row += 2
                
        elif b_type == "bullets":
            items = b.get("items", []) or [it.strip().lstrip("-*• ") for it in text.split("\n") if it.strip()]
            for item in items:
                ws.cell(row=current_row, column=1, value=f"• {item}")
                current_row += 1
            current_row += 1
            
        elif b_type == "table" and rows:
            start_table_row = current_row
            num_cols = len(rows[0])
            
            for r_idx, row_data in enumerate(rows):
                for c_idx, val in enumerate(row_data):
                    cell = ws.cell(row=current_row, column=c_idx + 1)
                    
                    # Check numeric conversion
                    is_num = False
                    if isinstance(val, (int, float)):
                        cell.value = val
                        is_num = True
                    elif isinstance(val, str):
                        val_clean = val.strip()
                        if val_clean.startswith("="):
                            cell.value = val_clean  # Formula
                        else:
                            try:
                                if "." in val_clean:
                                    cell.value = float(val_clean.replace(",", ""))
                                else:
                                    cell.value = int(val_clean.replace(",", ""))
                                is_num = True
                            except ValueError:
                                cell.value = val_clean
                    else:
                        cell.value = str(val)
                        
                    cell.border = thin_border
                    
                    if r_idx == 0:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        if is_num:
                            cell.alignment = Alignment(horizontal="right")
                            
                current_row += 1
            current_row += 2
            
        elif b_type == "chart" and rows and len(rows) > 1:
            # Add table first if not added
            chart_start_row = current_row
            for r_idx, row_data in enumerate(rows):
                for c_idx, val in enumerate(row_data):
                    cell = ws.cell(row=current_row, column=c_idx + 1)
                    try:
                        cell.value = float(str(val).replace(",", "")) if r_idx > 0 else str(val)
                    except ValueError:
                        cell.value = str(val)
                    current_row += 1
                    
            chart = BarChart()
            chart.title = b.get("title") or text or "Analysis Chart"
            chart.style = 10
            data_ref = Reference(ws, min_col=2, min_row=chart_start_row, max_col=len(rows[0]), max_row=chart_start_row + len(rows) - 1)
            cats_ref = Reference(ws, min_col=1, min_row=chart_start_row + 1, max_row=chart_start_row + len(rows) - 1)
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)
            ws.add_chart(chart, f"E{chart_start_row}")
            current_row += 15

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len and len(val_str) < 50:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
    wb.save(str(out_path))
    logger.info(f"[DELIVERABLE] XLSX created: {out_path}")
    return file_id, filename, out_path


def build_pptx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a PowerPoint (.pptx) presentation with title and section slides."""
    title = plan.get("title", "Engineering Briefing")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.pptx"), ".pptx")
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    prs = Presentation()
    
    # 1. Title Slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = title
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = "Sovereign Air-Gapped Industrial AI Platform\nStrict Technical Report"
        
    # Group blocks into slides by heading
    blocks = plan.get("blocks", [])
    current_slide = None
    current_text_frame = None
    
    content_layout = prs.slide_layouts[1]  # Title & Content
    
    for idx, b in enumerate(blocks):
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        
        if b_type == "heading" or current_slide is None:
            current_slide = prs.slides.add_slide(content_layout)
            current_slide.shapes.title.text = text if b_type == "heading" else title
            current_text_frame = current_slide.placeholders[1].text_frame
            current_text_frame.word_wrap = True
            if b_type == "heading":
                continue
                
        if b_type == "paragraph":
            if text and current_text_frame:
                p = current_text_frame.add_paragraph() if current_text_frame.text else current_text_frame.paragraphs[0]
                p.text = text
                p.font.size = PPTPt(16)
                
        elif b_type == "bullets":
            items = b.get("items", []) or [it.strip().lstrip("-*• ") for it in text.split("\n") if it.strip()]
            for item in items:
                if current_text_frame:
                    p = current_text_frame.add_paragraph() if current_text_frame.text else current_text_frame.paragraphs[0]
                    p.text = f"• {item}"
                    p.font.size = PPTPt(15)
                    
        elif b_type == "table" and rows:
            # Add table shape on the current slide
            blank_layout = prs.slide_layouts[6]
            table_slide = prs.slides.add_slide(blank_layout)
            
            # Slide heading
            tb = table_slide.shapes.add_textbox(PPTInches(0.8), PPTInches(0.5), PPTInches(8.4), PPTInches(0.8))
            tb.text_frame.text = b.get("title") or "Tabular Data Summary"
            tb.text_frame.paragraphs[0].font.size = PPTPt(22)
            tb.text_frame.paragraphs[0].font.bold = True
            
            rows_cnt = len(rows)
            cols_cnt = len(rows[0])
            table_shape = table_slide.shapes.add_table(
                rows_cnt, cols_cnt,
                PPTInches(0.8), PPTInches(1.5), PPTInches(8.4), PPTInches(min(5.0, rows_cnt * 0.5))
            )
            table = table_shape.table
            for r_i, r_data in enumerate(rows):
                for c_i, c_val in enumerate(r_data):
                    cell = table.cell(r_i, c_i)
                    cell.text = str(c_val)
                    if r_i == 0:
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = PPTRGBColor(31, 78, 120)
                        for p in cell.text_frame.paragraphs:
                            p.font.bold = True
                            p.font.color.rgb = PPTRGBColor(255, 255, 255)
                            
        elif b_type == "chart":
            blank_layout = prs.slide_layouts[6]
            chart_slide = prs.slides.add_slide(blank_layout)
            
            # Slide heading
            tb = chart_slide.shapes.add_textbox(PPTInches(0.8), PPTInches(0.5), PPTInches(8.4), PPTInches(0.8))
            tb.text_frame.text = b.get("title") or text or "Graphical Visualization"
            tb.text_frame.paragraphs[0].font.size = PPTPt(22)
            tb.text_frame.paragraphs[0].font.bold = True
            
            chart_img = chat_dir / f"temp_ppt_chart_{idx}_{uuid.uuid4().hex[:6]}.png"
            if generate_chart_image(b, chart_img):
                chart_slide.shapes.add_picture(str(chart_img), PPTInches(1.2), PPTInches(1.5), width=PPTInches(7.6))
                if chart_img.exists():
                    chart_img.unlink(missing_ok=True)

    prs.save(str(out_path))
    logger.info(f"[DELIVERABLE] PPTX created: {out_path}")
    return file_id, filename, out_path


def create_deliverable_file(plan: Dict[str, Any], mode: str, chat_id: str) -> Dict[str, Any]:
    """
    Builds the target deliverable based on mode ('docs', 'excel', 'ppt'),
    persists it, records in SQLite, and returns metadata with download URL.
    """
    mode = mode.lower()
    if mode == "docs":
        file_id, filename, file_path = build_docx(plan, chat_id)
        file_type = "docx"
    elif mode == "excel":
        file_id, filename, file_path = build_xlsx(plan, chat_id)
        file_type = "xlsx"
    elif mode == "ppt":
        file_id, filename, file_path = build_pptx(plan, chat_id)
        file_type = "pptx"
    else:
        file_id, filename, file_path = build_docx(plan, chat_id)
        file_type = "docx"
        
    save_file_record(file_id, chat_id, filename, file_type, str(file_path))
    
    return {
        "file_id": file_id,
        "filename": filename,
        "file_type": file_type,
        "file_path": str(file_path),
        "download_url": f"/api/files/{file_id}"
    }
