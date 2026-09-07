"""
Presentation Styles & Themes Registry for Sovereign Air-Gapped AI.
Defines executive, engineering, minimal, corporate, high-contrast, and custom presentation styles.
Allows LLM to autonomously pick the optimal style or dynamically generate custom color palettes.
"""

from typing import Dict, Any, List, Optional
from pptx.dml.color import RGBColor

# Predefined Presentation Styles
PPT_THEMES: Dict[str, Dict[str, Any]] = {
    "executive_dark": {
        "id": "executive_dark",
        "name": "Executive Deep Navy",
        "description": "Premium dark navy/indigo aesthetic with vibrant amber & cyan highlights. Ideal for leadership briefings.",
        "bg_title_rgb": (15, 20, 40),      # #0f1428
        "bg_content_rgb": (26, 26, 46),    # #1a1a2e
        "title_text_rgb": (255, 255, 255), # #ffffff
        "body_text_rgb": (224, 224, 224),  # #e0e0e0
        "accent_rgb": (234, 88, 12),       # Amber Flame #ea580c
        "accent_bar_rgb": (31, 78, 120),   # Industrial Blue
        "table_header_bg": (31, 78, 120),
        "table_row_alt1": (38, 38, 58),
        "table_row_alt2": (30, 30, 50),
        "footer_text_rgb": (140, 140, 160),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#ea580c",
        "ui_bg": "#ffffff"
    },
    "emerald_industrial": {
        "id": "emerald_industrial",
        "name": "Emerald Safety & Ecology",
        "description": "Refinery HSE, environment, sustainability, and plant reliability theme.",
        "bg_title_rgb": (10, 35, 25),      # Deep forest green
        "bg_content_rgb": (18, 38, 32),    # Dark emerald slate
        "title_text_rgb": (255, 255, 255),
        "body_text_rgb": (210, 240, 225),
        "accent_rgb": (22, 163, 74),       # Emerald Green #16a34a
        "accent_bar_rgb": (16, 185, 129),  # Mint
        "table_header_bg": (16, 120, 75),
        "table_row_alt1": (22, 48, 40),
        "table_row_alt2": (16, 36, 30),
        "footer_text_rgb": (130, 175, 155),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#16a34a",
        "ui_bg": "#f0fdf4"
    },
    "clean_corporate_light": {
        "id": "clean_corporate_light",
        "name": "Clean Modern Corporate (Light)",
        "description": "Crisp white background with royal blue corporate headers and slate typography. Perfect for formal audits.",
        "bg_title_rgb": (245, 248, 252),   # Soft crisp white-blue
        "bg_content_rgb": (255, 255, 255), # Pure White
        "title_text_rgb": (30, 58, 138),   # Royal Navy #1e3a8a
        "body_text_rgb": (30, 41, 59),     # Slate Dark #1e293b
        "accent_rgb": (37, 99, 235),       # Royal Blue #2563eb
        "accent_bar_rgb": (37, 99, 235),
        "table_header_bg": (30, 58, 138),
        "table_row_alt1": (248, 250, 252),
        "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#2563eb",
        "ui_bg": "#ffffff"
    },
    "midnight_cyan": {
        "id": "midnight_cyan",
        "name": "Midnight Tech & AI",
        "description": "Futuristic deep obsidian background with neon cyan and electric blue accents.",
        "bg_title_rgb": (11, 15, 25),      # Obsidian Black
        "bg_content_rgb": (17, 24, 39),    # Deep Slate
        "title_text_rgb": (255, 255, 255),
        "body_text_rgb": (203, 213, 225),
        "accent_rgb": (6, 182, 212),       # Electric Cyan #06b6d4
        "accent_bar_rgb": (14, 165, 233),  # Sky Blue
        "table_header_bg": (14, 116, 144),
        "table_row_alt1": (30, 41, 59),
        "table_row_alt2": (15, 23, 42),
        "footer_text_rgb": (148, 163, 184),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#06b6d4",
        "ui_bg": "#f0f9ff"
    },
    "crimson_alert": {
        "id": "crimson_alert",
        "name": "Crimson Emergency & Critical Incident",
        "description": "High-urgency theme for incident investigation, fire alarms, safety hazards, and risk mitigation.",
        "bg_title_rgb": (35, 10, 15),      # Deep Wine Red
        "bg_content_rgb": (38, 18, 22),    # Dark Crimson Slate
        "title_text_rgb": (255, 255, 255),
        "body_text_rgb": (240, 215, 220),
        "accent_rgb": (225, 29, 72),       # Rose Crimson #e11d48
        "accent_bar_rgb": (239, 68, 68),   # Red Accent
        "table_header_bg": (159, 18, 57),
        "table_row_alt1": (50, 25, 30),
        "table_row_alt2": (35, 15, 20),
        "footer_text_rgb": (180, 140, 150),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#e11d48",
        "ui_bg": "#fff1f2"
    },
    "gold_apex": {
        "id": "gold_apex",
        "name": "Apex Gold & Financial Review",
        "description": "Commercial performance, gross refining margin (GRM), economics, and revenue analytics.",
        "bg_title_rgb": (25, 20, 10),      # Dark Bronze
        "bg_content_rgb": (35, 30, 20),    # Warm Charcoal
        "title_text_rgb": (255, 255, 255),
        "body_text_rgb": (245, 235, 215),
        "accent_rgb": (217, 119, 6),       # Warm Gold Amber #d97706
        "accent_bar_rgb": (245, 158, 11),  # Golden Yellow
        "table_header_bg": (146, 64, 14),
        "table_row_alt1": (45, 38, 25),
        "table_row_alt2": (30, 25, 15),
        "footer_text_rgb": (180, 165, 140),
        "font_title": "Calibri",
        "font_body": "Calibri",
        "ui_accent": "#d97706",
        "ui_bg": "#fffbeb"
    }
}


def hex_to_rgb(hex_str: str) -> tuple:
    """Converts hex color code to (R, G, B) tuple."""
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 6:
        try:
            return (
                int(hex_clean[0:2], 16),
                int(hex_clean[2:4], 16),
                int(hex_clean[4:6], 16),
            )
        except ValueError:
            pass
    return (31, 78, 120)


def resolve_ppt_style(style_input: Any) -> Dict[str, Any]:
    """
    Resolves the presentation style.
    If style_input is a predefined key (e.g. 'emerald_industrial', 'clean_corporate_light'), returns it.
    If style_input is a custom dict with colors, merges with fallback executive theme.
    """
    if isinstance(style_input, str):
        style_key = style_input.strip().lower()
        if style_key in PPT_THEMES:
            return PPT_THEMES[style_key]
        # Auto-match keywords
        if any(w in style_key for w in ["safety", "green", "hse", "eco", "environment"]):
            return PPT_THEMES["emerald_industrial"]
        if any(w in style_key for w in ["light", "white", "corporate", "clean", "audit"]):
            return PPT_THEMES["clean_corporate_light"]
        if any(w in style_key for w in ["tech", "cyan", "ai", "digital", "future"]):
            return PPT_THEMES["midnight_cyan"]
        if any(w in style_key for w in ["danger", "hazard", "red", "emergency", "incident"]):
            return PPT_THEMES["crimson_alert"]
        if any(w in style_key for w in ["finance", "gold", "margin", "money", "budget"]):
            return PPT_THEMES["gold_apex"]

    if isinstance(style_input, dict):
        base = dict(PPT_THEMES["executive_dark"])
        if "bg_color" in style_input:
            base["bg_content_rgb"] = hex_to_rgb(style_input["bg_color"])
            base["bg_title_rgb"] = hex_to_rgb(style_input["bg_color"])
        if "accent_color" in style_input:
            acc_rgb = hex_to_rgb(style_input["accent_color"])
            base["accent_rgb"] = acc_rgb
            base["accent_bar_rgb"] = acc_rgb
            base["ui_accent"] = style_input["accent_color"]
        return base

    return PPT_THEMES["executive_dark"]
