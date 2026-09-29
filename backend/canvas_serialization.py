"""
Canvas persistence serializers for the AEGIS AI chat Canvas.

Converts the JSON payloads emitted by the frontend Canvas editors
(`apps/chat-frontend/src/components/canvas/*`) back into genuine on-disk
deliverables, so pressing "Save" really rewrites the .docx / .xlsx / .pptx /
source file that `GET /api/files/{id}` serves.

Payload contracts (mirroring the editor shapes exactly):

    .docx  {"html":  "<h1>..</h1><p>..</p><table>..</table>"}
    .xlsx  {"sheets": [{"id", "name", "rows": [[{"value", "formula",
                                                    "isHeader", "style"}]]}]}
    .pptx  {"slides": [{"layout", "title", "subtitle", "bullets", "kpis",
                        "timeline", "tableData", "notes", "bgColor",
                        "accentColor"}]}
    text   {"code":  "..."}

Design rules:
    * Every writer is pure with respect to the deliverable: it only ever writes
      to the path it is handed, so the caller can serialize to a temp file and
      atomically `os.replace` it over the live deliverable. A failed
      serialization therefore never corrupts the original.
    * The writer preserves the file extension of the target path, so dispatch
      uses the suffix of the path passed in.
    * Guard rails (sheet/row/slide/payload ceilings) reject hostile payloads
      rather than silently truncating a refinery deliverable.
"""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Guard rails
MAX_SHEETS = 50
MAX_ROWS_PER_SHEET = 5000
MAX_COLS_PER_SHEET = 256
MAX_SLIDES = 200
MAX_TEXT_BYTES = 5 * 1024 * 1024


class CanvasSerializationError(ValueError):
    """Raised when a canvas payload cannot be serialised safely."""


# ────────────────────────── shared helpers ──────────────────────────

_WHITESPACE_RE = re.compile(r"\s+")
_NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?$")
_HEX_RE = re.compile(r"^[0-9a-fA-F]{6}$")
_INVALID_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")


def _clean_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "")


def _hex6(value: Any) -> Optional[str]:
    """Normalises #rgb / #rrggbb / rrggbb / ARGB strings to uppercase RRGGBB."""
    v = str(value or "").strip().lstrip("#")
    if len(v) == 3:
        v = "".join(ch * 2 for ch in v)
    if len(v) == 8:
        v = v[2:]
    if not _HEX_RE.match(v):
        return None
    return v.upper()


def _argb(value: Any) -> Optional[str]:
    """Excel/openpyxl colours are 8-digit ARGB."""
    h = _hex6(value)
    return f"FF{h}" if h else None


# ───────────────────────────── HTML → DOCX ─────────────────────────────

_BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _HtmlBlockParser(HTMLParser):
    """Flattens styled editor HTML into an ordered list of typed blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: List[Dict[str, Any]] = []
        self._block_tag: Optional[str] = None
        self._block_color: Optional[str] = None
        self._runs: List[Tuple[str, Dict[str, bool]]] = []
        self._flags = {"bold": False, "italic": False, "underline": False}
        self._table: Optional[Dict[str, Any]] = None
        self._row: Optional[List[str]] = None
        self._cell: Optional[List[str]] = None

    # -- internals
    def _flush_block(self) -> None:
        if self._block_tag is None:
            return
        if self._block_tag in _HEADING_TAGS:
            kind = f"heading{self._block_tag[1]}"
        elif self._block_tag == "li":
            kind = "bullet"
        else:
            kind = "paragraph"
        runs = [r for r in self._runs if r[0].strip()]
        if runs:
            self.blocks.append({"kind": kind, "color": self._block_color, "runs": runs})
        self._block_tag = None
        self._block_color = None
        self._runs = []

    def _append_text(self, raw: str) -> None:
        if not raw:
            return
        text = _clean_whitespace(raw)
        if not text:
            return

        # Table cell capture
        if self._cell is not None:
            self._cell.append(text)
            return

        if self._block_tag is None:
            self._block_tag = "p"

        if self._runs and self._runs[-1][0].endswith(" "):
            text = text.lstrip(" ")
            if not text:
                return

        self._runs.append((text, dict(self._flags)))

    # -- HTMLParser hooks
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_map = dict(attrs)

        if tag == "table":
            self._flush_block()
            self._table = {"rows": []}
            return

        if self._table is not None:
            if tag == "tr":
                self._row = []
            elif tag in ("td", "th"):
                self._cell = []
            return

        if tag in _BLOCK_TAGS:
            self._flush_block()
            self._block_tag = tag
            style = (attr_map.get("style") or "").replace(" ", "")
            match = re.search(r"color:(#[0-9a-fA-F]{3,6})", style)
            if match:
                self._block_color = _hex6(match.group(1))
            return

        if tag == "br":
            self._append_text(" ")
            return
        if tag in ("b", "strong"):
            self._flags["bold"] = True
            return
        if tag in ("i", "em"):
            self._flags["italic"] = True
            return
        if tag in ("u", "ins"):
            self._flags["underline"] = True
            return

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "table":
            if self._table and self._table.get("rows"):
                self.blocks.append({"kind": "table", "rows": self._table["rows"]})
            self._table = None
            self._row = None
            self._cell = None
            return

        if self._table is not None:
            if tag in ("td", "th"):
                if self._row is not None and self._cell is not None:
                    self._row.append(" ".join(self._cell).strip())
                self._cell = None
            elif tag == "tr":
                if self._row and any(cell for cell in self._row):
                    self._table["rows"].append(self._row)
                self._row = None
            return

        if tag in _BLOCK_TAGS:
            self._flush_block()
            return
        if tag in ("b", "strong"):
            self._flags["bold"] = False
            return
        if tag in ("i", "em"):
            self._flags["italic"] = False
            return
        if tag in ("u", "ins"):
            self._flags["underline"] = False
            return

    def handle_data(self, data):
        if self._cell is None and self._block_tag is None and not self._table:
            return
        self._append_text(data)


def _append_table_to_docx(document, rows: List[List[str]]) -> None:
    if not rows:
        return
    from docx.shared import Pt

    col_count = max(len(row) for row in rows)
    table = document.add_table(rows=len(rows), cols=col_count)
    try:
        table.style = "Table Grid"
    except Exception:
        pass

    for r_idx, row in enumerate(rows):
        for c_idx in range(col_count):
            value = row[c_idx] if c_idx < len(row) else ""
            cell = table.cell(r_idx, c_idx)
            cell.text = value
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    if r_idx == 0:
                        run.bold = True


def html_to_docx(html: str, out_path: Path) -> None:
    """Rebuilds a .docx deliverable from the Canvas editor's HTML buffer."""
    import docx
    from docx.shared import RGBColor

    parser = _HtmlBlockParser()
    parser.feed(html or "")
    parser.close()

    document = docx.Document()
    if not parser.blocks:
        document.add_paragraph("")

    for block in parser.blocks:
        kind = block.get("kind")

        if kind == "table":
            _append_table_to_docx(document, block.get("rows") or [])
            continue

        if kind and kind.startswith("heading"):
            level = max(1, min(int(kind.replace("heading", "") or 1), 9))
            paragraph = document.add_heading(level=level)
        elif kind == "bullet":
            try:
                paragraph = document.add_paragraph(style="List Bullet")
            except KeyError:
                paragraph = document.add_paragraph()
        else:
            paragraph = document.add_paragraph()

        block_color = _hex6(block.get("color"))
        for text, flags in block.get("runs") or []:
            run = paragraph.add_run(text)
            if flags.get("bold"):
                run.bold = True
            if flags.get("italic"):
                run.italic = True
            if flags.get("underline"):
                run.underline = True
            if block_color:
                try:
                    run.font.color.rgb = RGBColor.from_string(block_color)
                except Exception:
                    pass

    document.save(str(out_path))


# ───────────────────────────── XLSX payload ─────────────────────────────

def _coerce_cell_value(cell: Dict[str, Any]) -> Any:
    """Turns the editor's display string into a genuine cell value."""
    formula = str(cell.get("formula") or "").strip()
    if formula.startswith("="):
        # openpyxl writes "=..." as a real workbook formula
        return formula

    raw = cell.get("value")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw

    text = str(raw).strip()
    if not text:
        return None

    style = cell.get("style") or {}
    number_format = style.get("format")

    if number_format in ("number", "currency", "percent"):
        cleaned = text
        for token in ("₹", "Rs.", "rs.", "$", "%", ","):
            cleaned = cleaned.replace(token, "")
        cleaned = cleaned.strip()
        try:
            return float(cleaned)
        except ValueError:
            return text

    if _NUMERIC_RE.match(text):
        # Preserve leading-zero identifiers (P&ID tags, permit numbers, IDs)
        if text.startswith("0") and not text.startswith("0.") and len(text) > 1:
            return text
        try:
            return float(text) if "." in text else int(text)
        except ValueError:
            return text

    return text


def _safe_sheet_title(name: Any, fallback: str = "Sheet") -> str:
    cleaned = _INVALID_SHEET_CHARS.sub("", str(name or "").strip())
    cleaned = cleaned.strip("'") or fallback
    return cleaned[:31]


def sheets_to_xlsx(sheets: Any, out_path: Path) -> None:
    """Rebuilds a .xlsx deliverable from the Canvas editor's sheet buffer."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    if not isinstance(sheets, list) or not sheets:
        raise CanvasSerializationError("Workbook payload contains no sheets.")
    if len(sheets) > MAX_SHEETS:
        raise CanvasSerializationError(f"Workbook payload exceeds the {MAX_SHEETS}-sheet canvas limit.")

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    for index, sheet in enumerate(sheets[:MAX_SHEETS]):
        if not isinstance(sheet, dict):
            sheet = {"name": f"Sheet{index + 1}", "rows": sheet}
        worksheet = workbook.create_sheet(title=_safe_sheet_title(sheet.get("name"), f"Sheet{index + 1}"))

        rows = sheet.get("rows") or []
        if not isinstance(rows, list):
            raise CanvasSerializationError(f"Sheet '{sheet.get('name')}' has malformed rows.")
        if len(rows) > MAX_ROWS_PER_SHEET:
            raise CanvasSerializationError(
                f"Sheet '{sheet.get('name')}' exceeds the {MAX_ROWS_PER_SHEET}-row canvas limit."
            )

        for r_idx, row in enumerate(rows[:MAX_ROWS_PER_SHEET], start=1):
            cells = row if isinstance(row, list) else []
            for c_idx, cell in enumerate(cells[:MAX_COLS_PER_SHEET], start=1):
                if not isinstance(cell, dict):
                    cell = {"value": cell}
                target = worksheet.cell(row=r_idx, column=c_idx, value=_coerce_cell_value(cell))

                style = cell.get("style") or {}
                is_header = bool(cell.get("isHeader"))

                font_kwargs: Dict[str, Any] = {}
                if style.get("bold") or is_header:
                    font_kwargs["bold"] = True
                if style.get("italic"):
                    font_kwargs["italic"] = True
                if style.get("underline"):
                    font_kwargs["underline"] = "single"
                elif style.get("strikethrough"):
                    font_kwargs["strike"] = True
                font_color = _argb(style.get("color"))
                if font_color:
                    font_kwargs["color"] = font_color
                if font_kwargs:
                    target.font = Font(**font_kwargs)

                fill_color = _argb(style.get("bgColor"))
                if fill_color:
                    target.fill = PatternFill("solid", fgColor=fill_color)

                align = style.get("align")
                if align in ("left", "center", "right"):
                    target.alignment = Alignment(horizontal=align, vertical="center", wrap_text=is_header)

                number_format = style.get("format")
                if number_format == "currency":
                    target.number_format = "#,##0.00"
                elif number_format == "percent":
                    target.number_format = "0.00%"
                elif number_format == "number":
                    target.number_format = "0.00"

        for idx, width in enumerate(sheet.get("colWidths") or [], start=1):
            if idx > MAX_COLS_PER_SHEET:
                break
            try:
                worksheet.column_dimensions[get_column_letter(idx)].width = max(8.0, min(float(width), 120.0))
            except (TypeError, ValueError):
                continue

        if not worksheet.max_column:
            worksheet.column_dimensions["A"].width = 18

    workbook.save(str(out_path))


# ───────────────────────────── PPTX payload ─────────────────────────────

def _add_text_box(
    slide,
    left,
    top,
    width,
    height,
    lines: List[Any],
    default_size: int = 14,
    default_color: str = "1E293B",
    default_align=None,
):
    """Adds a text box; each line is a string or (string, options-dict)."""
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True

    align = default_align if default_align is not None else PP_ALIGN.LEFT

    for index, line in enumerate(lines):
        if isinstance(line, tuple):
            text, options = line
        else:
            text, options = line, {}
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = options.get("align", align)
        run = paragraph.add_run()
        run.text = str(text)
        run.font.size = _to_points(options.get("size", default_size))
        run.font.bold = bool(options.get("bold", False))
        color = _hex6(options.get("color") or default_color)
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        if options.get("space_before") is not None:
            paragraph.space_before = _to_points(options["space_before"])
        if options.get("space_after") is not None:
            paragraph.space_after = _to_points(options["space_after"])

    return box


def _to_points(value: Any):
    from pptx.util import Pt

    try:
        return Pt(float(value))
    except (TypeError, ValueError):
        return Pt(14)


def slides_to_pptx(slides: Any, out_path: Path) -> None:
    """Rebuilds a .pptx deliverable from the Canvas editor's slide buffer."""
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches

    if not isinstance(slides, list) or not slides:
        raise CanvasSerializationError("Presentation payload contains no slides.")
    if len(slides) > MAX_SLIDES:
        raise CanvasSerializationError(f"Presentation payload exceeds the {MAX_SLIDES}-slide canvas limit.")

    presentation = Presentation()
    blank_layout = presentation.slide_layouts[6]

    slide_width = presentation.slide_width
    slide_height = presentation.slide_height
    margin = Inches(0.6)
    content_width = slide_width - (2 * margin)

    for payload in slides[:MAX_SLIDES]:
        if not isinstance(payload, dict):
            payload = {"title": str(payload)}

        slide = presentation.slides.add_slide(blank_layout)

        accent_hex = _hex6(payload.get("accentColor")) or "EA580C"
        accent = RGBColor.from_string(accent_hex)
        text_hex = _hex6(payload.get("color")) or "1E293B"
        text_rgb = RGBColor.from_string(text_hex)

        bg_hex = _hex6(payload.get("bgColor")) or "FFFFFF"
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = RGBColor.from_string(bg_hex)

        layout = str(payload.get("layout") or "content").lower()
        title = str(payload.get("title") or "").strip()
        subtitle = str(payload.get("subtitle") or "").strip()

        if layout == "title":
            _add_text_box(
                slide, margin, int(slide_height * 0.32), content_width, Inches(1.4),
                [(title or "Untitled Slide", {"size": 40, "bold": True, "color": accent_hex, "align": PP_ALIGN.CENTER})],
                default_align=PP_ALIGN.CENTER,
            )
            if subtitle:
                _add_text_box(
                    slide, margin, int(slide_height * 0.58), content_width, Inches(0.8),
                    [(subtitle, {"size": 18, "color": text_hex, "align": PP_ALIGN.CENTER})],
                    default_align=PP_ALIGN.CENTER,
                )
        else:
            _add_text_box(
                slide, margin, margin, content_width, Inches(0.9),
                [(title or "Untitled Slide", {"size": 28, "bold": True, "color": accent_hex})],
            )
            if subtitle:
                _add_text_box(
                    slide, margin, margin + Inches(0.9), content_width, Inches(0.5),
                    [(subtitle, {"size": 14, "color": text_hex})],
                )

            body_top = margin + Inches(1.5)
            body_height = slide_height - body_top - margin

            table_data = payload.get("tableData")
            bullets = [str(b) for b in (payload.get("bullets") or []) if str(b).strip()]
            kpis = payload.get("kpis") or []
            timeline = payload.get("timeline") or []
            quote = str(payload.get("quoteText") or "").strip()
            quote_author = str(payload.get("quoteAuthor") or "").strip()

            if table_data and table_data.get("headers"):
                headers = [str(h) for h in table_data.get("headers") or []]
                body_rows = [[str(c) for c in row] for row in (table_data.get("rows") or [])]
                col_count = max([len(headers)] + [len(row) for row in body_rows]) or 1
                row_count = min(len(body_rows) + (1 if headers else 0), 25)

                shape = slide.shapes.add_table(row_count, col_count, margin, body_top, content_width, body_height)
                table = shape.table
                offset = 0
                if headers:
                    for c_idx in range(col_count):
                        cell = table.cell(0, c_idx)
                        cell.text = headers[c_idx] if c_idx < len(headers) else ""
                    offset = 1
                for r_idx, row in enumerate(body_rows[: row_count - offset], start=offset):
                    for c_idx in range(col_count):
                        table.cell(r_idx, c_idx).text = row[c_idx] if c_idx < len(row) else ""

                for r_idx in range(row_count):
                    for c_idx in range(col_count):
                        cell = table.cell(r_idx, c_idx)
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.font.size = _to_points(11)
                                run.font.color.rgb = text_rgb
                                if r_idx == 0 and headers:
                                    run.font.bold = True
                                    run.font.color.rgb = accent

            elif kpis:
                lines = []
                for kpi in kpis[:6]:
                    if not isinstance(kpi, dict):
                        continue
                    label = str(kpi.get("label") or "").strip()
                    value = str(kpi.get("value") or "").strip()
                    change = str(kpi.get("change") or "").strip()
                    entry = f"{label}: {value}".strip(": ").strip()
                    if change:
                        entry = f"{entry}  ({change})"
                    if entry:
                        lines.append((entry, {"size": 18, "bold": True, "color": accent_hex, "space_after": 8}))
                _add_text_box(slide, margin, body_top, content_width, body_height, lines)

            elif timeline:
                lines = []
                for index, step in enumerate(timeline[:8], start=1):
                    if not isinstance(step, dict):
                        continue
                    step_title = str(step.get("title") or step.get("step") or f"Step {index}").strip()
                    step_desc = str(step.get("desc") or "").strip()
                    lines.append((f"{index}. {step_title}", {"size": 16, "bold": True, "color": accent_hex, "space_before": 4}))
                    if step_desc:
                        lines.append((step_desc, {"size": 12, "color": text_hex, "space_after": 6}))
                _add_text_box(slide, margin, body_top, content_width, body_height, lines)

            elif quote:
                lines = [(quote, {"size": 20, "bold": True, "color": accent_hex})]
                if quote_author:
                    lines.append((f"— {quote_author}", {"size": 12, "color": text_hex, "space_before": 8}))
                _add_text_box(slide, margin, body_top, content_width, body_height, lines)

            elif bullets:
                lines = [
                    (f"•  {bullet}", {"size": 15, "color": text_hex, "space_after": 8})
                    for bullet in bullets[:12]
                ]
                _add_text_box(slide, margin, body_top, content_width, body_height, lines)

        notes = str(payload.get("notes") or "").strip()
        if notes:
            try:
                slide.notes_slide.notes_text_frame.text = notes
            except Exception:
                pass

    presentation.save(str(out_path))


# ───────────────────────────── dispatch ─────────────────────────────

def apply_editor_content_to_file(out_path: Path, file_type: str, content: Dict[str, Any]) -> None:
    """
    Serializes a Canvas editor payload into `out_path`.

    Dispatch is suffix-first so the temp-file name used by the caller may keep
    the original extension (`report.tmp.docx`).
    """
    if not isinstance(content, dict) or not content:
        raise CanvasSerializationError("Canvas payload is empty.")

    out_path = Path(out_path)
    suffix = out_path.suffix.lower()
    kind = str(file_type or suffix.lstrip(".")).lower()

    if suffix == ".docx" or kind == "docx":
        html_to_docx(str(content.get("html") or ""), out_path)
        return

    if suffix == ".xlsx" or kind == "xlsx":
        sheets_to_xlsx(content.get("sheets") or [], out_path)
        return

    if suffix == ".pptx" or kind == "pptx":
        slides_to_pptx(content.get("slides") or [], out_path)
        return

    code = content.get("code")
    if code is None:
        code = content.get("text")
    if code is None:
        raise CanvasSerializationError(
            f"Unsupported canvas payload for {suffix or kind} deliverables (expected 'code', 'html', 'sheets' or 'slides')."
        )

    text = str(code)
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise CanvasSerializationError("Text payload exceeds the 5 MB canvas limit.")
    out_path.write_text(text, encoding="utf-8")
