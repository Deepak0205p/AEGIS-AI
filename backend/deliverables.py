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


def _add_docx_header_footer(doc, title: str):
    """Adds professional header and footer with page numbers to the document."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import datetime
    
    section = doc.sections[0]
    
    # ── Header ──
    header = section.header
    header.is_linked_to_previous = False
    header_para = header.paragraphs[0]
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = header_para.add_run(f"SOVEREIGN AI PLATFORM  |  {title.upper()}")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(100, 100, 120)
    run.font.name = "Calibri"
    
    # ── Footer with Page Numbers ──
    footer = section.footer
    footer.is_linked_to_previous = False
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    run = footer_para.add_run(f"Generated: {timestamp}  |  Page ")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(120, 120, 140)
    run.font.name = "Calibri"
    
    # Insert PAGE field
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(qn('w:fldCharType'), 'begin')
    run2 = footer_para.add_run()
    run2._r.append(fldChar_begin)
    
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    run3 = footer_para.add_run()
    run3._r.append(instrText)
    
    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(qn('w:fldCharType'), 'end')
    run4 = footer_para.add_run()
    run4._r.append(fldChar_end)
    
    run5 = footer_para.add_run(" of ")
    run5.font.size = Pt(8)
    run5.font.color.rgb = RGBColor(120, 120, 140)
    
    # Insert NUMPAGES field
    fldChar_begin2 = OxmlElement('w:fldChar')
    fldChar_begin2.set(qn('w:fldCharType'), 'begin')
    run6 = footer_para.add_run()
    run6._r.append(fldChar_begin2)
    
    instrText2 = OxmlElement('w:instrText')
    instrText2.set(qn('xml:space'), 'preserve')
    instrText2.text = ' NUMPAGES '
    run7 = footer_para.add_run()
    run7._r.append(instrText2)
    
    fldChar_end2 = OxmlElement('w:fldChar')
    fldChar_end2.set(qn('w:fldCharType'), 'end')
    run8 = footer_para.add_run()
    run8._r.append(fldChar_end2)


def _add_docx_toc(doc):
    """Inserts a Table of Contents field at the current position."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    
    para = doc.add_paragraph()
    run = para.add_run()
    
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(qn('w:fldCharType'), 'begin')
    run._r.append(fldChar_begin)
    
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' TOC \\o "1-3" \\h \\z \\u '
    run._r.append(instrText)
    
    fldChar_separate = OxmlElement('w:fldChar')
    fldChar_separate.set(qn('w:fldCharType'), 'separate')
    run._r.append(fldChar_separate)
    
    # Placeholder text
    run2 = para.add_run("[Table of Contents — Right-click → Update Field to populate]")
    run2.font.color.rgb = RGBColor(140, 140, 160)
    run2.font.size = Pt(9)
    run2.font.italic = True
    
    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(qn('w:fldCharType'), 'end')
    run3 = para.add_run()
    run3._r.append(fldChar_end)
    
    # Add page break after TOC
    doc.add_page_break()


def build_docx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a professional Microsoft Word (.docx) document with headers, footers,
    page numbers, table of contents, and numbered headings."""
    title = plan.get("title", "Engineering Report")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.docx"), ".docx")
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    doc = Document()
    
    # ── Set default font to Calibri ──
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    
    # ── Professional Header & Footer ──
    _add_docx_header_footer(doc, title)
    
    # ── Title ──
    title_p = doc.add_heading(title, level=0)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ── Table of Contents ──
    toc_heading = doc.add_heading("Table of Contents", level=1)
    _add_docx_toc(doc)
    
    # ── Numbered Heading Counters ──
    h1_counter = 0
    h2_counter = 0
    h3_counter = 0
    
    # ── Blocks ──
    blocks = plan.get("blocks", [])
    for idx, b in enumerate(blocks):
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        
        if b_type == "heading":
            level = b.get("level", 1)
            level = min(3, max(1, level))
            
            # Auto-number headings
            if level == 1:
                h1_counter += 1
                h2_counter = 0
                h3_counter = 0
                numbered_text = f"{h1_counter}. {text}"
            elif level == 2:
                h2_counter += 1
                h3_counter = 0
                numbered_text = f"{h1_counter}.{h2_counter} {text}"
            else:
                h3_counter += 1
                numbered_text = f"{h1_counter}.{h2_counter}.{h3_counter} {text}"
            
            doc.add_heading(numbered_text, level=level)
            
        elif b_type == "paragraph":
            if text:
                p = doc.add_paragraph(text)
                for run in p.runs:
                    run.font.name = 'Calibri'
                    run.font.size = Pt(11)
                
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
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.name = 'Calibri'
                            run.font.size = Pt(10)
                    if r_idx == 0:
                        # Bold header with blue background
                        from docx.oxml.ns import qn as _qn
                        shading = cell._element.get_or_add_tcPr()
                        shd = docx.oxml.OxmlElement('w:shd')
                        shd.set(_qn('w:fill'), '1F4E78')
                        shd.set(_qn('w:val'), 'clear')
                        shading.append(shd)
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.bold = True
                                run.font.color.rgb = RGBColor(255, 255, 255)
                    elif r_idx % 2 == 0:
                        # Alternating row shading
                        from docx.oxml.ns import qn as _qn
                        shading = cell._element.get_or_add_tcPr()
                        shd = docx.oxml.OxmlElement('w:shd')
                        shd.set(_qn('w:fill'), 'F2F6FA')
                        shd.set(_qn('w:val'), 'clear')
                        shading.append(shd)
                        
            doc.add_paragraph()  # Spacing after table
                
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


def _build_xlsx_sheet(ws, blocks: List, header_fill, header_font, title_font, thin_border, start_row: int = 1):
    """Populates a single worksheet from a list of blocks starting at specified row."""
    current_row = start_row
    
    for b in blocks:
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        
        if b_type in ("heading", "paragraph"):
            if text:
                try:
                    cell = ws.cell(row=current_row, column=1, value=text)
                    cell.font = Font(name="Calibri", bold=(b_type == "heading"), size=12 if b_type == "heading" else 11, color="1F4E78" if b_type == "heading" else "000000")
                except Exception:
                    pass
                current_row += 2
                
        elif b_type == "bullets":
            items = b.get("items", []) or [it.strip().lstrip("-*• ") for it in text.split("\n") if it.strip()]
            for item in items:
                try:
                    cell = ws.cell(row=current_row, column=1, value=f"• {item}")
                    cell.font = Font(name="Calibri", size=10)
                except Exception:
                    pass
                current_row += 1
            current_row += 1
            
        elif b_type == "table" and rows:
            start_table_row = current_row
            num_cols = len(rows[0]) if rows else 0
            if num_cols == 0:
                continue
            
            for r_idx, row_data in enumerate(rows):
                for c_idx, val in enumerate(row_data):
                    try:
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
                            cell.value = str(val) if val is not None else ""
                            
                        cell.border = thin_border
                        
                        if r_idx == 0:
                            cell.fill = header_fill
                            cell.font = header_font
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        else:
                            if is_num:
                                cell.alignment = Alignment(horizontal="right", vertical="center")
                            else:
                                cell.alignment = Alignment(horizontal="left", vertical="center")
                    except Exception as e:
                        logger.warning(f"[XLSX] Cell write warning at r={current_row} c={c_idx+1}: {e}")
                            
                current_row += 1
            
            # ── Auto Formula Summary Row ──
            if len(rows) > 2:
                data_start = start_table_row + 1  # First data row (after header)
                data_end = current_row - 1         # Last data row
                
                # Check if any columns are numeric
                numeric_cols = []
                for c_idx in range(1, num_cols):
                    sample_cell = ws.cell(row=data_start, column=c_idx + 1)
                    if isinstance(sample_cell.value, (int, float)):
                        numeric_cols.append(c_idx + 1)
                
                if numeric_cols:
                    summary_row = current_row
                    try:
                        lbl_cell = ws.cell(row=summary_row, column=1, value="TOTAL")
                        lbl_cell.font = Font(name="Calibri", bold=True, size=11, color="1F4E78")
                        lbl_cell.border = thin_border
                        
                        for col_num in numeric_cols:
                            col_letter = openpyxl.utils.get_column_letter(col_num)
                            formula = f"=SUM({col_letter}{data_start}:{col_letter}{data_end})"
                            cell = ws.cell(row=summary_row, column=col_num, value=formula)
                            cell.font = Font(name="Calibri", bold=True, size=11, color="1F4E78")
                            cell.border = thin_border
                            cell.alignment = Alignment(horizontal="right", vertical="center")
                        current_row += 1
                    except Exception as e:
                        logger.warning(f"[XLSX] Summary row warning: {e}")
            
            # ── Conditional Formatting Rules ──
            highlight_rules = b.get("highlight_rules", [])
            for rule in highlight_rules:
                try:
                    col_num = int(rule.get("column", 1))
                    condition = rule.get("condition", "greater_than").lower()
                    value = rule.get("value", 0)
                    color = rule.get("color", "FF4444").lstrip("#")
                    
                    col_letter = openpyxl.utils.get_column_letter(col_num)
                    cell_range = f"{col_letter}{start_table_row + 1}:{col_letter}{current_row - 1}"
                    
                    fill_color = PatternFill(start_color=color, end_color=color, fill_type="solid")
                    
                    from openpyxl.formatting.rule import CellIsRule
                    
                    op_map = {
                        "greater_than": "greaterThan",
                        "less_than": "lessThan",
                        "equal": "equal",
                        "greater_than_or_equal": "greaterThanOrEqual",
                        "less_than_or_equal": "lessThanOrEqual",
                        "not_equal": "notEqual",
                    }
                    op = op_map.get(condition, "greaterThan")
                    ws.conditional_formatting.add(
                        cell_range,
                        CellIsRule(operator=op, formula=[str(value)], fill=fill_color)
                    )
                except Exception as e:
                    logger.warning(f"[XLSX] Failed to apply highlight rule: {e}")
            
            current_row += 2
            
        elif b_type == "chart" and rows and len(rows) > 1:
            chart_start_row = current_row
            for r_idx, row_data in enumerate(rows):
                for c_idx, val in enumerate(row_data):
                    try:
                        cell = ws.cell(row=current_row, column=c_idx + 1)
                        cell.value = float(str(val).replace(",", "")) if r_idx > 0 else str(val)
                    except ValueError:
                        cell.value = str(val)
                    except Exception:
                        pass
                current_row += 1
                    
            try:
                chart = BarChart()
                chart.title = b.get("title") or text or "Analysis Chart"
                chart.style = 10
                data_ref = Reference(ws, min_col=2, min_row=chart_start_row, max_col=len(rows[0]), max_row=chart_start_row + len(rows) - 1)
                cats_ref = Reference(ws, min_col=1, min_row=chart_start_row + 1, max_row=chart_start_row + len(rows) - 1)
                chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(cats_ref)
                ws.add_chart(chart, f"E{chart_start_row}")
            except Exception as e:
                logger.warning(f"[XLSX] Chart insertion warning: {e}")
            current_row += 15

    return current_row


def build_xlsx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a professional Microsoft Excel (.xlsx) workbook with multi-sheet support,
    conditional formatting, formula summary rows, and frozen header panes."""
    title = plan.get("title", "Data Sheet")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.xlsx"), ".xlsx")
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    wb = openpyxl.Workbook()
    
    # Shared styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1F4E78")
    thin_border = Border(
        left=Side(style='thin', color="D9D9D9"),
        right=Side(style='thin', color="D9D9D9"),
        top=Side(style='thin', color="D9D9D9"),
        bottom=Side(style='thin', color="D9D9D9")
    )
    
    # ── Multi-Sheet Support ──
    sheets_data = plan.get("sheets", None)
    
    if sheets_data and isinstance(sheets_data, list) and len(sheets_data) > 0:
        # Multi-sheet mode: each sheet has name + blocks
        for s_idx, sheet_info in enumerate(sheets_data):
            sheet_name = sheet_info.get("name", f"Sheet{s_idx + 1}")[:31]  # Excel 31-char limit
            sheet_blocks = sheet_info.get("blocks", [])
            
            if s_idx == 0:
                ws = wb.active
                ws.title = sheet_name
            else:
                ws = wb.create_sheet(title=sheet_name)
            
            # Title row
            ws.cell(row=1, column=1, value=f"{title} — {sheet_name}").font = title_font
            
            # Build content starting from row 3
            content_blocks = sheet_blocks if sheet_blocks else []
            _build_xlsx_sheet(ws, content_blocks, header_fill, header_font, title_font, thin_border, start_row=3)
            
            # Freeze header pane at row 3 (where headers start)
            ws.freeze_panes = "A4"
            
    else:
        # Single-sheet fallback (backward compatible)
        ws = wb.active
        ws.title = "Summary"
        
        # Title row
        ws.cell(row=1, column=1, value=title).font = title_font
        
        blocks = plan.get("blocks", [])
        _build_xlsx_sheet(ws, blocks, header_fill, header_font, title_font, thin_border, start_row=3)
        
        # Freeze header pane at row 3
        ws.freeze_panes = "A4"

    # ── Auto-adjust column widths (all sheets) ──
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len and len(val_str) < 50:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
        # Set print area for each sheet
        if ws.max_column and ws.max_row:
            last_col = openpyxl.utils.get_column_letter(ws.max_column)
            ws.print_area = f"A1:{last_col}{ws.max_row}"
            ws.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(fitToPage=True)
        
    wb.save(str(out_path))
    logger.info(f"[DELIVERABLE] XLSX created: {out_path} ({len(wb.worksheets)} sheets)")
    return file_id, filename, out_path


from backend.ppt_styles import resolve_ppt_style, hex_to_rgb


def _apply_theme_to_slide(slide, style: Dict[str, Any], is_title_slide: bool = False):
    """Applies dynamic theme background and font styling to a slide based on selected style."""
    background = slide.background
    fill = background.fill
    fill.solid()
    
    bg_tuple = style["bg_title_rgb"] if is_title_slide else style["bg_content_rgb"]
    fill.fore_color.rgb = PPTRGBColor(*bg_tuple)


def _set_text_themed(text_frame, color_tuple, font_name: str = "Calibri"):
    """Sets text color and font family in a text frame."""
    for p in text_frame.paragraphs:
        for run in p.runs:
            run.font.name = font_name
            run.font.color.rgb = PPTRGBColor(*color_tuple)


def _add_slide_footer(slide, prs_title: str, slide_num: int, style: Dict[str, Any]):
    """Adds a professional footer with slide number and title."""
    footer_tb = slide.shapes.add_textbox(
        PPTInches(0.5), PPTInches(6.85), PPTInches(9.0), PPTInches(0.35)
    )
    tf = footer_tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{prs_title}  |  Slide {slide_num}  |  Sovereign AI Platform"
    p.font.size = PPTPt(8)
    footer_color = style.get("footer_text_rgb", (140, 140, 160))
    p.font.color.rgb = PPTRGBColor(*footer_color)
    p.alignment = PP_ALIGN.CENTER


def _add_accent_bar(slide, top_inches: float = 1.3, color_tuple=None):
    """Adds a thin colored accent bar across the slide."""
    if color_tuple is None:
        color_tuple = (31, 78, 120)
    bar = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        PPTInches(0.8), PPTInches(top_inches), PPTInches(8.4), PPTInches(0.04)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = PPTRGBColor(*color_tuple)
    bar.line.fill.background()  # No border


def _inject_speaker_notes(slide, notes_text: str):
    """Injects speaker notes into a slide's notes pane."""
    if notes_text:
        notes_slide = slide.notes_slide
        notes_tf = notes_slide.notes_text_frame
        notes_tf.text = notes_text


def build_pptx(plan: Dict[str, Any], chat_id: str) -> Tuple[str, str, Path]:
    """Builds a professional PowerPoint (.pptx) presentation dynamically styled using
    either an AI-chosen style preset or custom generated theme with speaker notes,
    slide numbers, custom accent bars, themed tables, and auto-conclusion slide."""
    title = plan.get("title", "Engineering Briefing")
    filename = sanitize_filename(plan.get("filename", f"{title.lower().replace(' ', '_')}.pptx"), ".pptx")
    
    # ── Resolve Presentation Style ──
    raw_style = plan.get("style") or plan.get("theme") or "executive_dark"
    style = resolve_ppt_style(raw_style)
    
    title_font_name = style.get("font_title", "Calibri")
    body_font_name = style.get("font_body", "Calibri")
    title_color = style.get("title_text_rgb", (255, 255, 255))
    body_color = style.get("body_text_rgb", (224, 224, 224))
    accent_bar_color = style.get("accent_bar_rgb", (31, 78, 120))
    table_hdr_bg = style.get("table_header_bg", (31, 78, 120))
    table_row1_bg = style.get("table_row_alt1", (38, 38, 58))
    table_row2_bg = style.get("table_row_alt2", (30, 30, 50))
    
    chat_dir = GENERATED_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    out_path = chat_dir / f"{file_id}_{filename}"
    
    prs = Presentation()
    slide_counter = 0
    all_bullet_points = []  # Collect for auto-conclusion
    has_conclusion = False
    
    # ── 1. Title Slide ──────────────────────────────────────────────────────
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    _apply_theme_to_slide(slide, style, is_title_slide=True)
    slide.shapes.title.text = title
    for run in slide.shapes.title.text_frame.paragraphs[0].runs:
        run.font.name = title_font_name
        run.font.color.rgb = PPTRGBColor(*title_color)
        run.font.size = PPTPt(36)
    if len(slide.placeholders) > 1:
        subtitle_text = plan.get("subtitle") or "Sovereign Air-Gapped Industrial AI Platform\nExecutive Technical Briefing"
        slide.placeholders[1].text = subtitle_text
        _set_text_themed(slide.placeholders[1].text_frame, body_color, body_font_name)
    slide_counter += 1
    _add_slide_footer(slide, title, slide_counter, style)
    _inject_speaker_notes(slide, plan.get("title_notes", f"Presentation: {title}"))
        
    # ── 2. Content Slides from Blocks ────────────────────────────────────
    blocks = plan.get("blocks", [])
    current_slide = None
    current_text_frame = None
    
    content_layout = prs.slide_layouts[1]  # Title & Content
    
    for idx, b in enumerate(blocks):
        b_type = (b.get("type") or "paragraph").lower()
        text = b.get("text", "")
        rows = b.get("rows", [])
        notes = b.get("notes", "")
        
        # Check if this is a conclusion/summary heading
        if b_type == "heading" and text:
            heading_lower = text.lower()
            if any(kw in heading_lower for kw in ["conclusion", "summary", "takeaway", "key point"]):
                has_conclusion = True
        
        if b_type == "heading" or current_slide is None:
            current_slide = prs.slides.add_slide(content_layout)
            slide_counter += 1
            _apply_theme_to_slide(current_slide, style, is_title_slide=False)
            
            heading_text = text if b_type == "heading" else title
            current_slide.shapes.title.text = heading_text
            for run in current_slide.shapes.title.text_frame.paragraphs[0].runs:
                run.font.name = title_font_name
                run.font.color.rgb = PPTRGBColor(*title_color)
                run.font.size = PPTPt(28)
            
            _add_accent_bar(current_slide, top_inches=1.25, color_tuple=accent_bar_color)
            _add_slide_footer(current_slide, title, slide_counter, style)
            
            current_text_frame = current_slide.placeholders[1].text_frame
            current_text_frame.word_wrap = True
            
            if notes:
                _inject_speaker_notes(current_slide, notes)
            
            if b_type == "heading":
                continue
                
        if b_type == "paragraph":
            if text and current_text_frame:
                p = current_text_frame.add_paragraph() if current_text_frame.text else current_text_frame.paragraphs[0]
                p.text = text
                p.font.name = body_font_name
                p.font.size = PPTPt(16)
                p.font.color.rgb = PPTRGBColor(*body_color)
                if notes and current_slide:
                    _inject_speaker_notes(current_slide, notes)
                
        elif b_type == "bullets":
            items = b.get("items", []) or [it.strip().lstrip("-*• ") for it in text.split("\n") if it.strip()]
            for item in items:
                all_bullet_points.append(item)  # Collect for conclusion
                if current_text_frame:
                    p = current_text_frame.add_paragraph() if current_text_frame.text else current_text_frame.paragraphs[0]
                    p.text = f"• {item}"
                    p.font.name = body_font_name
                    p.font.size = PPTPt(15)
                    p.font.color.rgb = PPTRGBColor(*body_color)
            if notes and current_slide:
                _inject_speaker_notes(current_slide, notes)
                    
        elif b_type == "table" and rows:
            # Use blank layout for table slides
            blank_layout = prs.slide_layouts[6]
            table_slide = prs.slides.add_slide(blank_layout)
            slide_counter += 1
            _apply_theme_to_slide(table_slide, style, is_title_slide=False)
            
            # Slide heading
            tb = table_slide.shapes.add_textbox(PPTInches(0.8), PPTInches(0.4), PPTInches(8.4), PPTInches(0.7))
            tb.text_frame.text = b.get("title") or "Tabular Data Summary"
            tb.text_frame.paragraphs[0].font.name = title_font_name
            tb.text_frame.paragraphs[0].font.size = PPTPt(22)
            tb.text_frame.paragraphs[0].font.bold = True
            tb.text_frame.paragraphs[0].font.color.rgb = PPTRGBColor(*title_color)
            
            _add_accent_bar(table_slide, top_inches=1.1, color_tuple=accent_bar_color)
            _add_slide_footer(table_slide, title, slide_counter, style)
            
            rows_cnt = len(rows)
            cols_cnt = len(rows[0])
            table_shape = table_slide.shapes.add_table(
                rows_cnt, cols_cnt,
                PPTInches(0.8), PPTInches(1.3), PPTInches(8.4), PPTInches(min(5.2, rows_cnt * 0.5))
            )
            table = table_shape.table
            for r_i, r_data in enumerate(rows):
                for c_i, c_val in enumerate(r_data):
                    cell = table.cell(r_i, c_i)
                    cell.text = str(c_val)
                    if r_i == 0:
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = PPTRGBColor(*table_hdr_bg)
                        for p in cell.text_frame.paragraphs:
                            p.font.name = title_font_name
                            p.font.bold = True
                            p.font.color.rgb = PPTRGBColor(255, 255, 255)
                            p.font.size = PPTPt(12)
                    else:
                        cell.fill.solid()
                        alt_color = table_row1_bg if r_i % 2 == 1 else table_row2_bg
                        cell.fill.fore_color.rgb = PPTRGBColor(*alt_color)
                        for p in cell.text_frame.paragraphs:
                            p.font.name = body_font_name
                            p.font.color.rgb = PPTRGBColor(*body_color)
                            p.font.size = PPTPt(11)
            if notes:
                _inject_speaker_notes(table_slide, notes)
                            
        elif b_type == "chart":
            blank_layout = prs.slide_layouts[6]
            chart_slide = prs.slides.add_slide(blank_layout)
            slide_counter += 1
            _apply_theme_to_slide(chart_slide, style, is_title_slide=False)
            
            # Slide heading
            tb = chart_slide.shapes.add_textbox(PPTInches(0.8), PPTInches(0.4), PPTInches(8.4), PPTInches(0.7))
            tb.text_frame.text = b.get("title") or text or "Graphical Visualization"
            tb.text_frame.paragraphs[0].font.name = title_font_name
            tb.text_frame.paragraphs[0].font.size = PPTPt(22)
            tb.text_frame.paragraphs[0].font.bold = True
            tb.text_frame.paragraphs[0].font.color.rgb = PPTRGBColor(*title_color)
            
            _add_accent_bar(chart_slide, top_inches=1.1, color_tuple=accent_bar_color)
            _add_slide_footer(chart_slide, title, slide_counter, style)
            
            chart_img = chat_dir / f"temp_ppt_chart_{idx}_{uuid.uuid4().hex[:6]}.png"
            if generate_chart_image(b, chart_img):
                chart_slide.shapes.add_picture(str(chart_img), PPTInches(1.2), PPTInches(1.3), width=PPTInches(7.6))
                if chart_img.exists():
                    chart_img.unlink(missing_ok=True)
            if notes:
                _inject_speaker_notes(chart_slide, notes)

    # ── 3. Auto-Conclusion Slide ─────────────────────────────────────────
    if not has_conclusion and all_bullet_points:
        conclusion_slide = prs.slides.add_slide(content_layout)
        slide_counter += 1
        _apply_theme_to_slide(conclusion_slide, style, is_title_slide=False)
        
        conclusion_slide.shapes.title.text = "Key Takeaways"
        for run in conclusion_slide.shapes.title.text_frame.paragraphs[0].runs:
            run.font.name = title_font_name
            run.font.color.rgb = PPTRGBColor(*title_color)
            run.font.size = PPTPt(28)
        
        _add_accent_bar(conclusion_slide, top_inches=1.25, color_tuple=accent_bar_color)
        _add_slide_footer(conclusion_slide, title, slide_counter, style)
        
        tf = conclusion_slide.placeholders[1].text_frame
        tf.word_wrap = True
        # Take up to 6 key bullet points for the conclusion
        takeaways = all_bullet_points[:6]
        for i, item in enumerate(takeaways):
            p = tf.paragraphs[0] if i == 0 and not tf.text else tf.add_paragraph()
            p.text = f"✓ {item}"
            p.font.name = body_font_name
            p.font.size = PPTPt(14)
            p.font.color.rgb = PPTRGBColor(*body_color)
        
        _inject_speaker_notes(conclusion_slide, "Summary of key takeaways from this presentation.")

    prs.save(str(out_path))
    logger.info(f"[DELIVERABLE] PPTX created: {out_path} ({slide_counter} slides, style={style.get('id', 'custom')})")
    return file_id, filename, out_path


def create_deliverable_file(plan: Dict[str, Any], mode: str, chat_id: str) -> Dict[str, Any]:
    """
    Builds the target deliverable based on mode ('docs', 'excel', 'ppt'),
    persists it, records in database, and returns metadata with download URL.
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
