"""
Presentation Styles & Themes Registry for Sovereign Air-Gapped AI.
Contains 50+ unique, specialized presentation styles across industries, domains, and color formats.
Allows LLM to autonomously pick the optimal style or dynamically generate custom color palettes.
"""

from typing import Dict, Any, List, Optional
from pptx.dml.color import RGBColor

# Predefined 50 Unique Presentation Styles across 8 Categories
PPT_THEMES: Dict[str, Dict[str, Any]] = {
    # ── 1. EXECUTIVE & CORPORATE LEADERSHIP (1-7) ──
    "executive_dark": {
        "id": "executive_dark",
        "name": "Executive Deep Navy",
        "category": "Executive",
        "description": "Premium dark navy aesthetic with vibrant amber & cyan highlights.",
        "bg_title_rgb": (15, 20, 40), "bg_content_rgb": (26, 26, 46),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (224, 224, 224),
        "accent_rgb": (234, 88, 12), "accent_bar_rgb": (31, 78, 120),
        "table_header_bg": (31, 78, 120), "table_row_alt1": (38, 38, 58), "table_row_alt2": (30, 30, 50),
        "footer_text_rgb": (140, 140, 160), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#ea580c", "ui_bg": "#ffffff"
    },
    "clean_corporate_light": {
        "id": "clean_corporate_light",
        "name": "Clean Modern Corporate",
        "category": "Executive",
        "description": "Crisp white background with royal blue corporate headers and slate typography.",
        "bg_title_rgb": (245, 248, 252), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (30, 58, 138), "body_text_rgb": (30, 41, 59),
        "accent_rgb": (37, 99, 235), "accent_bar_rgb": (37, 99, 235),
        "table_header_bg": (30, 58, 138), "table_row_alt1": (248, 250, 252), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#2563eb", "ui_bg": "#ffffff"
    },
    "boardroom_slate": {
        "id": "boardroom_slate",
        "name": "Boardroom Slate & Platinum",
        "category": "Executive",
        "description": "High-level board meeting aesthetic with cool slate and platinum accents.",
        "bg_title_rgb": (30, 41, 59), "bg_content_rgb": (15, 23, 42),
        "title_text_rgb": (248, 250, 252), "body_text_rgb": (203, 213, 225),
        "accent_rgb": (148, 163, 184), "accent_bar_rgb": (71, 85, 105),
        "table_header_bg": (51, 65, 85), "table_row_alt1": (30, 41, 59), "table_row_alt2": (15, 23, 42),
        "footer_text_rgb": (100, 116, 139), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#64748b", "ui_bg": "#f8fafc"
    },
    "royal_monarch": {
        "id": "royal_monarch",
        "name": "Royal Monarch Indigo",
        "category": "Executive",
        "description": "Deep imperial indigo with gold filigree highlights for strategic summits.",
        "bg_title_rgb": (24, 18, 56), "bg_content_rgb": (30, 22, 68),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (230, 225, 245),
        "accent_rgb": (234, 179, 8), "accent_bar_rgb": (147, 51, 234),
        "table_header_bg": (79, 70, 229), "table_row_alt1": (45, 35, 90), "table_row_alt2": (35, 26, 75),
        "footer_text_rgb": (160, 150, 185), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#eab308", "ui_bg": "#faf5ff"
    },
    "nordic_minimal": {
        "id": "nordic_minimal",
        "name": "Nordic Minimalist Snow",
        "category": "Executive",
        "description": "Scandinavian clean design with pale gray tones and subtle charcoal lettering.",
        "bg_title_rgb": (250, 250, 250), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (24, 24, 27), "body_text_rgb": (63, 63, 70),
        "accent_rgb": (14, 165, 233), "accent_bar_rgb": (212, 212, 216),
        "table_header_bg": (39, 39, 42), "table_row_alt1": (244, 244, 245), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (161, 161, 170), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#0ea5e9", "ui_bg": "#ffffff"
    },
    "charcoal_prestige": {
        "id": "charcoal_prestige",
        "name": "Charcoal Prestige",
        "category": "Executive",
        "description": "Dark matte charcoal with silver-white typography for luxury and prestige briefs.",
        "bg_title_rgb": (20, 20, 20), "bg_content_rgb": (28, 28, 28),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (220, 220, 220),
        "accent_rgb": (245, 158, 11), "accent_bar_rgb": (80, 80, 80),
        "table_header_bg": (60, 60, 60), "table_row_alt1": (40, 40, 40), "table_row_alt2": (30, 30, 30),
        "footer_text_rgb": (120, 120, 120), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f59e0b", "ui_bg": "#1c1c1c"
    },
    "ivory_editorial": {
        "id": "ivory_editorial",
        "name": "Ivory Editorial & Gazette",
        "category": "Executive",
        "description": "Warm ivory background with dark espresso text and crimson editorial rule bars.",
        "bg_title_rgb": (253, 251, 247), "bg_content_rgb": (255, 253, 250),
        "title_text_rgb": (41, 37, 36), "body_text_rgb": (68, 64, 60),
        "accent_rgb": (185, 28, 28), "accent_bar_rgb": (185, 28, 28),
        "table_header_bg": (68, 64, 60), "table_row_alt1": (245, 240, 230), "table_row_alt2": (255, 253, 250),
        "footer_text_rgb": (120, 113, 108), "font_title": "Georgia", "font_body": "Calibri",
        "ui_accent": "#b91c1c", "ui_bg": "#fdfbf7"
    },

    # ── 2. ENGINEERING, REFINERY & INDUSTRIAL (8-14) ──
    "refinery_crude_amber": {
        "id": "refinery_crude_amber",
        "name": "Refinery CDU Amber & Flame",
        "category": "Refinery",
        "description": "Distillation units, furnaces, and hydrocarbons theme with warm amber heat glow.",
        "bg_title_rgb": (30, 20, 15), "bg_content_rgb": (24, 18, 16),
        "title_text_rgb": (255, 237, 213), "body_text_rgb": (254, 215, 170),
        "accent_rgb": (249, 115, 22), "accent_bar_rgb": (194, 65, 12),
        "table_header_bg": (154, 52, 18), "table_row_alt1": (45, 28, 22), "table_row_alt2": (30, 20, 15),
        "footer_text_rgb": (170, 130, 110), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f97316", "ui_bg": "#fff7ed"
    },
    "mechanical_steel_blue": {
        "id": "mechanical_steel_blue",
        "name": "Mechanical Rotary & Steel",
        "category": "Engineering",
        "description": "Pumps, compressors, turbines, and mechanical integrity inspection reports.",
        "bg_title_rgb": (18, 30, 48), "bg_content_rgb": (22, 36, 56),
        "title_text_rgb": (240, 248, 255), "body_text_rgb": (210, 225, 240),
        "accent_rgb": (56, 189, 248), "accent_bar_rgb": (2, 132, 199),
        "table_header_bg": (3, 105, 161), "table_row_alt1": (30, 50, 75), "table_row_alt2": (22, 36, 56),
        "footer_text_rgb": (125, 155, 180), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#38bdf8", "ui_bg": "#f0f9ff"
    },
    "pipeline_cad_dark": {
        "id": "pipeline_cad_dark",
        "name": "CAD Blueprint & Piping P&ID",
        "category": "Engineering",
        "description": "Technical drafting dark blueprint with CAD blue grid and bright cyan annotations.",
        "bg_title_rgb": (10, 25, 45), "bg_content_rgb": (13, 31, 54),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (200, 230, 255),
        "accent_rgb": (0, 210, 255), "accent_bar_rgb": (0, 150, 220),
        "table_header_bg": (0, 90, 150), "table_row_alt1": (20, 45, 75), "table_row_alt2": (13, 31, 54),
        "footer_text_rgb": (100, 160, 210), "font_title": "Consolas", "font_body": "Calibri",
        "ui_accent": "#00d2ff", "ui_bg": "#0a192d"
    },
    "chemical_catalyst": {
        "id": "chemical_catalyst",
        "name": "Chemical Synthesis & Catalyst",
        "category": "Chemical",
        "description": "Polymer, catalyst, reagents, and petrochemical process lab tracking.",
        "bg_title_rgb": (25, 20, 38), "bg_content_rgb": (32, 26, 48),
        "title_text_rgb": (245, 235, 255), "body_text_rgb": (225, 210, 245),
        "accent_rgb": (168, 85, 247), "accent_bar_rgb": (126, 34, 206),
        "table_header_bg": (107, 33, 168), "table_row_alt1": (48, 38, 70), "table_row_alt2": (32, 26, 48),
        "footer_text_rgb": (160, 140, 185), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#a855f7", "ui_bg": "#faf5ff"
    },
    "power_grid_high_voltage": {
        "id": "power_grid_high_voltage",
        "name": "High Voltage & Substation",
        "category": "Electrical",
        "description": "Electrical telemetry, transformer diagnostics, and power grid stability briefs.",
        "bg_title_rgb": (15, 25, 30), "bg_content_rgb": (20, 32, 40),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (210, 235, 245),
        "accent_rgb": (250, 204, 21), "accent_bar_rgb": (202, 138, 4),
        "table_header_bg": (13, 148, 136), "table_row_alt1": (30, 48, 60), "table_row_alt2": (20, 32, 40),
        "footer_text_rgb": (120, 160, 180), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#facc15", "ui_bg": "#fefce8"
    },
    "boiler_steam_thermal": {
        "id": "boiler_steam_thermal",
        "name": "Boiler & Steam Utility Thermal",
        "category": "Thermal",
        "description": "Steam distribution, thermal heat recovery, and boiler efficiency calculations.",
        "bg_title_rgb": (35, 22, 18), "bg_content_rgb": (42, 28, 24),
        "title_text_rgb": (255, 240, 235), "body_text_rgb": (240, 215, 205),
        "accent_rgb": (239, 68, 68), "accent_bar_rgb": (185, 28, 28),
        "table_header_bg": (153, 27, 27), "table_row_alt1": (60, 38, 32), "table_row_alt2": (42, 28, 24),
        "footer_text_rgb": (175, 135, 125), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#ef4444", "ui_bg": "#fef2f2"
    },
    "automation_scada_neon": {
        "id": "automation_scada_neon",
        "name": "DCS & SCADA Automation",
        "category": "Automation",
        "description": "PLC ladder logic, Yokogawa/Honeywell DCS trips, and real-time sensor loops.",
        "bg_title_rgb": (12, 18, 24), "bg_content_rgb": (16, 24, 32),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (195, 220, 235),
        "accent_rgb": (34, 197, 94), "accent_bar_rgb": (13, 148, 136),
        "table_header_bg": (15, 118, 110), "table_row_alt1": (25, 40, 52), "table_row_alt2": (16, 24, 32),
        "footer_text_rgb": (110, 150, 175), "font_title": "Consolas", "font_body": "Calibri",
        "ui_accent": "#22c55e", "ui_bg": "#101820"
    },

    # ── 3. SAFETY, HSE, OISD & ENVIRONMENT (15-21) ──
    "emerald_industrial": {
        "id": "emerald_industrial",
        "name": "Emerald Safety & Ecology",
        "category": "Safety",
        "description": "Refinery HSE, environment, sustainability, and plant reliability theme.",
        "bg_title_rgb": (10, 35, 25), "bg_content_rgb": (18, 38, 32),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (210, 240, 225),
        "accent_rgb": (22, 163, 74), "accent_bar_rgb": (16, 185, 129),
        "table_header_bg": (16, 120, 75), "table_row_alt1": (22, 48, 40), "table_row_alt2": (16, 36, 30),
        "footer_text_rgb": (130, 175, 155), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#16a34a", "ui_bg": "#f0fdf4"
    },
    "crimson_alert": {
        "id": "crimson_alert",
        "name": "Crimson Emergency & Critical Incident",
        "category": "Safety",
        "description": "High-urgency theme for incident investigation, fire alarms, and HAZOP.",
        "bg_title_rgb": (35, 10, 15), "bg_content_rgb": (38, 18, 22),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (240, 215, 220),
        "accent_rgb": (225, 29, 72), "accent_bar_rgb": (239, 68, 68),
        "table_header_bg": (159, 18, 57), "table_row_alt1": (50, 25, 30), "table_row_alt2": (35, 15, 20),
        "footer_text_rgb": (180, 140, 150), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#e11d48", "ui_bg": "#fff1f2"
    },
    "hazard_warning_yellow": {
        "id": "hazard_warning_yellow",
        "name": "Caution & Hazard Safety Yellow",
        "category": "Safety",
        "description": "High-visibility OSHA & OISD warning matrix with contrast hazard bars.",
        "bg_title_rgb": (25, 24, 18), "bg_content_rgb": (32, 30, 22),
        "title_text_rgb": (254, 240, 138), "body_text_rgb": (253, 230, 138),
        "accent_rgb": (234, 179, 8), "accent_bar_rgb": (202, 138, 4),
        "table_header_bg": (161, 98, 7), "table_row_alt1": (48, 45, 30), "table_row_alt2": (32, 30, 22),
        "footer_text_rgb": (180, 165, 110), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#eab308", "ui_bg": "#fefce8"
    },
    "gas_detection_toxic": {
        "id": "gas_detection_toxic",
        "name": "Toxic Gas & H2S Matrix",
        "category": "Safety",
        "description": "Atmospheric telemetry, LEL monitoring, oxygen depletion, and ppm logging.",
        "bg_title_rgb": (20, 30, 28), "bg_content_rgb": (25, 38, 35),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (205, 235, 230),
        "accent_rgb": (20, 184, 166), "accent_bar_rgb": (13, 148, 136),
        "table_header_bg": (15, 118, 110), "table_row_alt1": (35, 52, 48), "table_row_alt2": (25, 38, 35),
        "footer_text_rgb": (130, 170, 165), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#14b8a6", "ui_bg": "#f0fdfa"
    },
    "fire_brigade_crimson": {
        "id": "fire_brigade_crimson",
        "name": "Fire & Water Foam Network",
        "category": "Safety",
        "description": "Hydrant pressure tests, deluge valves, and fire pump drill records.",
        "bg_title_rgb": (40, 12, 16), "bg_content_rgb": (48, 16, 20),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (245, 210, 215),
        "accent_rgb": (244, 63, 94), "accent_bar_rgb": (225, 29, 72),
        "table_header_bg": (190, 18, 60), "table_row_alt1": (65, 24, 30), "table_row_alt2": (48, 16, 20),
        "footer_text_rgb": (190, 145, 150), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f43f5e", "ui_bg": "#fff1f2"
    },
    "zero_harm_light": {
        "id": "zero_harm_light",
        "name": "Zero Harm & ESG (Light)",
        "category": "Safety",
        "description": "Clean white and forest green ESG sustainability and statutory board reporting.",
        "bg_title_rgb": (240, 253, 244), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (20, 83, 45), "body_text_rgb": (22, 101, 52),
        "accent_rgb": (22, 163, 74), "accent_bar_rgb": (34, 197, 94),
        "table_header_bg": (21, 128, 61), "table_row_alt1": (240, 253, 244), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 150, 120), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#16a34a", "ui_bg": "#ffffff"
    },
    "marine_terminal_ocean": {
        "id": "marine_terminal_ocean",
        "name": "Single Point Mooring (SPM) Ocean",
        "category": "Marine",
        "description": "Offshore crude tanker berthing, SPM pressure lines, and marine safety.",
        "bg_title_rgb": (12, 28, 48), "bg_content_rgb": (16, 36, 60),
        "title_text_rgb": (240, 250, 255), "body_text_rgb": (200, 230, 250),
        "accent_rgb": (56, 189, 248), "accent_bar_rgb": (14, 165, 233),
        "table_header_bg": (2, 132, 199), "table_row_alt1": (25, 50, 80), "table_row_alt2": (16, 36, 60),
        "footer_text_rgb": (120, 160, 195), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#38bdf8", "ui_bg": "#f0f9ff"
    },

    # ── 4. FINANCIAL, GRM & COMMERCIAL (22-28) ──
    "gold_apex": {
        "id": "gold_apex",
        "name": "Apex Gold & Margin Review",
        "category": "Financial",
        "description": "Gross refining margin (GRM), product crack spreads, and budget reviews.",
        "bg_title_rgb": (25, 20, 10), "bg_content_rgb": (35, 30, 20),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (245, 235, 215),
        "accent_rgb": (217, 119, 6), "accent_bar_rgb": (245, 158, 11),
        "table_header_bg": (146, 64, 14), "table_row_alt1": (45, 38, 25), "table_row_alt2": (30, 25, 15),
        "footer_text_rgb": (180, 165, 140), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#d97706", "ui_bg": "#fffbeb"
    },
    "emerald_profit_ledger": {
        "id": "emerald_profit_ledger",
        "name": "Profit Ledger & EBITDA",
        "category": "Financial",
        "description": "Quarterly P&L, operational expense (OPEX), and revenue benchmarks.",
        "bg_title_rgb": (15, 30, 22), "bg_content_rgb": (20, 40, 30),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (215, 245, 230),
        "accent_rgb": (34, 197, 94), "accent_bar_rgb": (22, 163, 74),
        "table_header_bg": (21, 128, 61), "table_row_alt1": (28, 55, 42), "table_row_alt2": (20, 40, 30),
        "footer_text_rgb": (130, 175, 150), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#22c55e", "ui_bg": "#f0fdf4"
    },
    "wallstreet_classic_light": {
        "id": "wallstreet_classic_light",
        "name": "Wall Street Classic Light",
        "category": "Financial",
        "description": "Classic crisp banking look with navy tables and crimson loss indicators.",
        "bg_title_rgb": (255, 255, 255), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (15, 23, 42), "body_text_rgb": (30, 41, 59),
        "accent_rgb": (2, 132, 199), "accent_bar_rgb": (15, 23, 42),
        "table_header_bg": (15, 23, 42), "table_row_alt1": (241, 245, 249), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139), "font_title": "Georgia", "font_body": "Calibri",
        "ui_accent": "#0284c7", "ui_bg": "#ffffff"
    },
    "capex_copper": {
        "id": "capex_copper",
        "name": "CAPEX & Asset Valuation Copper",
        "category": "Financial",
        "description": "Heavy machinery valuation, depreciation, and expansion capital expenditures.",
        "bg_title_rgb": (32, 22, 18), "bg_content_rgb": (40, 28, 22),
        "title_text_rgb": (255, 240, 230), "body_text_rgb": (240, 215, 200),
        "accent_rgb": (217, 119, 6), "accent_bar_rgb": (180, 83, 9),
        "table_header_bg": (146, 64, 14), "table_row_alt1": (55, 38, 30), "table_row_alt2": (40, 28, 22),
        "footer_text_rgb": (175, 145, 130), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#d97706", "ui_bg": "#fffbeb"
    },
    "crude_futures_nymex": {
        "id": "crude_futures_nymex",
        "name": "Brent & NYMEX Trading Desk",
        "category": "Financial",
        "description": "Crude basket price index, hedging strategy, and import parity pricing.",
        "bg_title_rgb": (14, 20, 28), "bg_content_rgb": (18, 26, 36),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (205, 225, 240),
        "accent_rgb": (16, 185, 129), "accent_bar_rgb": (59, 130, 246),
        "table_header_bg": (30, 64, 175), "table_row_alt1": (26, 38, 52), "table_row_alt2": (18, 26, 36),
        "footer_text_rgb": (120, 150, 175), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#10b981", "ui_bg": "#121826"
    },
    "procurement_slate_amber": {
        "id": "procurement_slate_amber",
        "name": "Vendor Tendering & Contracts",
        "category": "Financial",
        "description": "GeM portal bids, contractor tender evaluations, and PO tracking.",
        "bg_title_rgb": (248, 250, 252), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (15, 23, 42), "body_text_rgb": (51, 65, 85),
        "accent_rgb": (217, 119, 6), "accent_bar_rgb": (217, 119, 6),
        "table_header_bg": (30, 41, 59), "table_row_alt1": (241, 245, 249), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#d97706", "ui_bg": "#ffffff"
    },
    "insurance_mbd_claims": {
        "id": "insurance_mbd_claims",
        "name": "Machinery Insurance & Loss Adjusting",
        "category": "Financial",
        "description": "Industrial all-risk (IAR) policy endorsement, claims, and surveyor reports.",
        "bg_title_rgb": (20, 32, 45), "bg_content_rgb": (26, 42, 58),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (215, 235, 250),
        "accent_rgb": (14, 165, 233), "accent_bar_rgb": (2, 132, 199),
        "table_header_bg": (3, 105, 161), "table_row_alt1": (35, 55, 75), "table_row_alt2": (26, 42, 58),
        "footer_text_rgb": (130, 165, 190), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#0ea5e9", "ui_bg": "#f0f9ff"
    },

    # ── 5. AI, TECHNOLOGY & DIGITAL (29-35) ──
    "midnight_cyan": {
        "id": "midnight_cyan",
        "name": "Midnight Tech & AI",
        "category": "Technology",
        "description": "Futuristic deep obsidian background with neon cyan highlights.",
        "bg_title_rgb": (11, 15, 25), "bg_content_rgb": (17, 24, 39),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (203, 213, 225),
        "accent_rgb": (6, 182, 212), "accent_bar_rgb": (14, 165, 233),
        "table_header_bg": (14, 116, 144), "table_row_alt1": (30, 41, 59), "table_row_alt2": (15, 23, 42),
        "footer_text_rgb": (148, 163, 184), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#06b6d4", "ui_bg": "#f0f9ff"
    },
    "cyber_security_matrix": {
        "id": "cyber_security_matrix",
        "name": "OT Cyber Security & Air-Gap",
        "category": "Technology",
        "description": "Air-gapped enclave integrity, zero trust, firewall rules, and CISO audit.",
        "bg_title_rgb": (8, 20, 15), "bg_content_rgb": (12, 26, 20),
        "title_text_rgb": (240, 255, 245), "body_text_rgb": (190, 240, 210),
        "accent_rgb": (34, 197, 94), "accent_bar_rgb": (22, 163, 74),
        "table_header_bg": (20, 83, 45), "table_row_alt1": (18, 40, 30), "table_row_alt2": (12, 26, 20),
        "footer_text_rgb": (100, 165, 130), "font_title": "Consolas", "font_body": "Consolas",
        "ui_accent": "#22c55e", "ui_bg": "#0a1f14"
    },
    "deepseek_neural_purple": {
        "id": "deepseek_neural_purple",
        "name": "Neural Reasoning & Deep Inference",
        "category": "Technology",
        "description": "Large language model weights, GPU VRAM telemetry, and local token throughput.",
        "bg_title_rgb": (18, 12, 35), "bg_content_rgb": (24, 16, 45),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (230, 215, 250),
        "accent_rgb": (168, 85, 247), "accent_bar_rgb": (147, 51, 234),
        "table_header_bg": (126, 34, 206), "table_row_alt1": (38, 26, 68), "table_row_alt2": (24, 16, 45),
        "footer_text_rgb": (155, 135, 185), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#a855f7", "ui_bg": "#faf5ff"
    },
    "quantum_electric_violet": {
        "id": "quantum_electric_violet",
        "name": "Quantum Electric Violet",
        "category": "Technology",
        "description": "High-tech computing, predictive algorithms, and machine learning models.",
        "bg_title_rgb": (15, 10, 30), "bg_content_rgb": (20, 14, 40),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (220, 210, 245),
        "accent_rgb": (139, 92, 246), "accent_bar_rgb": (99, 102, 241),
        "table_header_bg": (79, 70, 229), "table_row_alt1": (32, 22, 60), "table_row_alt2": (20, 14, 40),
        "footer_text_rgb": (140, 125, 175), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#8b5cf6", "ui_bg": "#140e28"
    },
    "data_lakehouse_azure": {
        "id": "data_lakehouse_azure",
        "name": "Data Lakehouse Azure",
        "category": "Technology",
        "description": "SQL databases, enterprise ETL pipelines, telemetry ingestion, and analytics.",
        "bg_title_rgb": (15, 28, 45), "bg_content_rgb": (20, 36, 58),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (210, 230, 250),
        "accent_rgb": (14, 165, 233), "accent_bar_rgb": (2, 132, 199),
        "table_header_bg": (3, 105, 161), "table_row_alt1": (28, 48, 75), "table_row_alt2": (20, 36, 58),
        "footer_text_rgb": (120, 155, 185), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#0ea5e9", "ui_bg": "#f0f9ff"
    },
    "devops_terminal_green": {
        "id": "devops_terminal_green",
        "name": "DevOps Terminal & CI/CD",
        "category": "Technology",
        "description": "Server uptime, Docker microservices, git commits, and shell automation.",
        "bg_title_rgb": (10, 15, 12), "bg_content_rgb": (14, 20, 16),
        "title_text_rgb": (74, 222, 128), "body_text_rgb": (187, 247, 208),
        "accent_rgb": (34, 197, 94), "accent_bar_rgb": (22, 163, 74),
        "table_header_bg": (20, 83, 45), "table_row_alt1": (20, 32, 24), "table_row_alt2": (14, 20, 16),
        "footer_text_rgb": (100, 155, 120), "font_title": "Consolas", "font_body": "Consolas",
        "ui_accent": "#4ade80", "ui_bg": "#0a0f0c"
    },
    "silicon_dark_matte": {
        "id": "silicon_dark_matte",
        "name": "Silicon Microarchitecture",
        "category": "Technology",
        "description": "Hardware diagnostics, edge inference devices, and GPU cluster health.",
        "bg_title_rgb": (22, 22, 24), "bg_content_rgb": (28, 28, 30),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (212, 212, 216),
        "accent_rgb": (244, 63, 94), "accent_bar_rgb": (161, 161, 170),
        "table_header_bg": (63, 63, 70), "table_row_alt1": (39, 39, 42), "table_row_alt2": (28, 28, 30),
        "footer_text_rgb": (113, 113, 122), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f43f5e", "ui_bg": "#18181b"
    },

    # ── 6. STATUTORY, AUDIT & COMPLIANCE (36-42) ──
    "peso_explosive_cert": {
        "id": "peso_explosive_cert",
        "name": "PESO Statutory & Explosives",
        "category": "Compliance",
        "description": "Petroleum & Explosives Safety Org statutory license renewal and compliance.",
        "bg_title_rgb": (255, 253, 245), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (120, 53, 15), "body_text_rgb": (69, 26, 3),
        "accent_rgb": (194, 65, 12), "accent_bar_rgb": (194, 65, 12),
        "table_header_bg": (146, 64, 14), "table_row_alt1": (254, 243, 199), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (140, 100, 60), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#c2410c", "ui_bg": "#fffbeb"
    },
    "oisd_standard_105": {
        "id": "oisd_standard_105",
        "name": "OISD-STD-105 Work Permit",
        "category": "Compliance",
        "description": "Official Oil Industry Safety Directorate Form A/B work permits and checklists.",
        "bg_title_rgb": (245, 247, 250), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (30, 58, 138), "body_text_rgb": (30, 41, 59),
        "accent_rgb": (220, 38, 38), "accent_bar_rgb": (30, 58, 138),
        "table_header_bg": (30, 58, 138), "table_row_alt1": (241, 245, 249), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#dc2626", "ui_bg": "#ffffff"
    },
    "iso_55001_asset": {
        "id": "iso_55001_asset",
        "name": "ISO 55001 Asset Management",
        "category": "Compliance",
        "description": "Standardized asset reliability management, lifecycle costing, and audits.",
        "bg_title_rgb": (18, 32, 45), "bg_content_rgb": (24, 40, 56),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (210, 230, 245),
        "accent_rgb": (16, 185, 129), "accent_bar_rgb": (14, 165, 233),
        "table_header_bg": (3, 105, 161), "table_row_alt1": (32, 52, 72), "table_row_alt2": (24, 40, 56),
        "footer_text_rgb": (120, 155, 180), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#10b981", "ui_bg": "#f0fdf4"
    },
    "cpcb_environment_audit": {
        "id": "cpcb_environment_audit",
        "name": "CPCB / SPCB Emission Audit",
        "category": "Compliance",
        "description": "Central Pollution Control Board stack emissions, SOx/NOx, and effluent water.",
        "bg_title_rgb": (16, 34, 26), "bg_content_rgb": (22, 42, 32),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (215, 245, 225),
        "accent_rgb": (34, 197, 94), "accent_bar_rgb": (22, 163, 74),
        "table_header_bg": (21, 128, 61), "table_row_alt1": (30, 56, 42), "table_row_alt2": (22, 42, 32),
        "footer_text_rgb": (125, 170, 145), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#22c55e", "ui_bg": "#f0fdf4"
    },
    "legal_affidavit_formal": {
        "id": "legal_affidavit_formal",
        "name": "Legal Affidavit & Statutory Council",
        "category": "Compliance",
        "description": "High-formality legal briefs, regulatory arbitration, and statutory affidavits.",
        "bg_title_rgb": (250, 248, 244), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (28, 25, 23), "body_text_rgb": (68, 64, 60),
        "accent_rgb": (120, 53, 15), "accent_bar_rgb": (120, 53, 15),
        "table_header_bg": (41, 37, 36), "table_row_alt1": (245, 240, 235), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (120, 113, 108), "font_title": "Georgia", "font_body": "Calibri",
        "ui_accent": "#78350f", "ui_bg": "#faf8f4"
    },
    "internal_audit_matrix": {
        "id": "internal_audit_matrix",
        "name": "CAG & Internal Audit Matrix",
        "category": "Compliance",
        "description": "Compliance checklists, observations, non-conformance reports, and closures.",
        "bg_title_rgb": (241, 245, 249), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (15, 23, 42), "body_text_rgb": (51, 65, 85),
        "accent_rgb": (225, 29, 72), "accent_bar_rgb": (51, 65, 85),
        "table_header_bg": (30, 41, 59), "table_row_alt1": (241, 245, 249), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (100, 116, 139), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#e11d48", "ui_bg": "#ffffff"
    },
    "risk_register_heat_map": {
        "id": "risk_register_heat_map",
        "name": "Enterprise Risk Register & Heat Map",
        "category": "Compliance",
        "description": "5x5 Likelihood vs Severity risk scoring matrix and residual risk plans.",
        "bg_title_rgb": (24, 18, 22), "bg_content_rgb": (30, 22, 28),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (235, 215, 225),
        "accent_rgb": (244, 63, 94), "accent_bar_rgb": (225, 29, 72),
        "table_header_bg": (159, 18, 57), "table_row_alt1": (42, 30, 38), "table_row_alt2": (30, 22, 28),
        "footer_text_rgb": (160, 135, 150), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f43f5e", "ui_bg": "#fff1f2"
    },

    # ── 7. CREATIVE, MODERN & PRESENTATION SHOWCASE (43-48) ──
    "sunset_gradient_vibes": {
        "id": "sunset_gradient_vibes",
        "name": "Sunset Warm Horizon",
        "category": "Creative",
        "description": "Warm gradient aesthetic from deep magenta to golden peach.",
        "bg_title_rgb": (35, 15, 30), "bg_content_rgb": (42, 18, 36),
        "title_text_rgb": (255, 240, 245), "body_text_rgb": (250, 215, 230),
        "accent_rgb": (251, 146, 60), "accent_bar_rgb": (219, 39, 119),
        "table_header_bg": (157, 23, 77), "table_row_alt1": (55, 25, 48), "table_row_alt2": (42, 18, 36),
        "footer_text_rgb": (180, 135, 160), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#fb923c", "ui_bg": "#fdf2f8"
    },
    "monochrome_high_contrast": {
        "id": "monochrome_high_contrast",
        "name": "Monochrome Stark Contrast",
        "category": "Creative",
        "description": "Pure black and stark white high-contrast format for maximum readability.",
        "bg_title_rgb": (0, 0, 0), "bg_content_rgb": (10, 10, 10),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (240, 240, 240),
        "accent_rgb": (255, 255, 255), "accent_bar_rgb": (180, 180, 180),
        "table_header_bg": (40, 40, 40), "table_row_alt1": (25, 25, 25), "table_row_alt2": (10, 10, 10),
        "footer_text_rgb": (150, 150, 150), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#ffffff", "ui_bg": "#000000"
    },
    "cosmic_nebula": {
        "id": "cosmic_nebula",
        "name": "Cosmic Deep Space Nebula",
        "category": "Creative",
        "description": "Deep interstellar navy with stellar cyan and soft violet glow.",
        "bg_title_rgb": (10, 12, 28), "bg_content_rgb": (15, 18, 38),
        "title_text_rgb": (255, 255, 255), "body_text_rgb": (215, 225, 250),
        "accent_rgb": (56, 189, 248), "accent_bar_rgb": (168, 85, 247),
        "table_header_bg": (67, 56, 202), "table_row_alt1": (25, 28, 55), "table_row_alt2": (15, 18, 38),
        "footer_text_rgb": (135, 145, 180), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#38bdf8", "ui_bg": "#0a0c1c"
    },
    "mint_fresh_startup": {
        "id": "mint_fresh_startup",
        "name": "Mint Fresh Modern Startup",
        "category": "Creative",
        "description": "Clean mint green with modern typography for pitch decks and new initiatives.",
        "bg_title_rgb": (240, 253, 250), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (17, 94, 89), "body_text_rgb": (15, 118, 110),
        "accent_rgb": (13, 148, 136), "accent_bar_rgb": (20, 184, 166),
        "table_header_bg": (13, 148, 136), "table_row_alt1": (240, 253, 250), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (90, 150, 140), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#0d9488", "ui_bg": "#f0fdfa"
    },
    "copper_roast_vintage": {
        "id": "copper_roast_vintage",
        "name": "Copper Artisan & Foundry",
        "category": "Creative",
        "description": "Warm metallic copper and rich charcoal for metallurgy and materials.",
        "bg_title_rgb": (30, 24, 20), "bg_content_rgb": (38, 30, 26),
        "title_text_rgb": (255, 245, 235), "body_text_rgb": (240, 220, 205),
        "accent_rgb": (234, 88, 12), "accent_bar_rgb": (194, 65, 12),
        "table_header_bg": (154, 52, 18), "table_row_alt1": (50, 40, 34), "table_row_alt2": (38, 30, 26),
        "footer_text_rgb": (170, 140, 125), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#ea580c", "ui_bg": "#261e1a"
    },
    "lavender_luxury_soft": {
        "id": "lavender_luxury_soft",
        "name": "Soft Lavender & Silk",
        "category": "Creative",
        "description": "Gentle lavender tones with deep plum text for human resources & culture briefs.",
        "bg_title_rgb": (250, 245, 255), "bg_content_rgb": (255, 255, 255),
        "title_text_rgb": (88, 28, 135), "body_text_rgb": (107, 33, 168),
        "accent_rgb": (147, 51, 234), "accent_bar_rgb": (192, 132, 252),
        "table_header_bg": (126, 34, 206), "table_row_alt1": (245, 235, 255), "table_row_alt2": (255, 255, 255),
        "footer_text_rgb": (140, 110, 170), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#9333ea", "ui_bg": "#faf5ff"
    },

    # ── 8. SPECIALIZED SCIENTIFIC & OPERATIONAL (49-50) ──
    "drilling_offshore_deepwater": {
        "id": "drilling_offshore_deepwater",
        "name": "Deepwater Offshore & Subsea",
        "category": "Upstream",
        "description": "Subsea wellhead pressure, blowout preventer (BOP) tests, and riser tension.",
        "bg_title_rgb": (8, 22, 38), "bg_content_rgb": (12, 30, 50),
        "title_text_rgb": (240, 250, 255), "body_text_rgb": (200, 230, 245),
        "accent_rgb": (14, 165, 233), "accent_bar_rgb": (2, 132, 199),
        "table_header_bg": (3, 105, 161), "table_row_alt1": (20, 44, 70), "table_row_alt2": (12, 30, 50),
        "footer_text_rgb": (110, 150, 180), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#0ea5e9", "ui_bg": "#0c1e32"
    },
    "turnaround_shutdown_matrix": {
        "id": "turnaround_shutdown_matrix",
        "name": "Major Turnaround (M&I) Critical Path",
        "category": "Maintenance",
        "description": "Refinery major turnaround schedule, Gantt milestones, and blinding progress.",
        "bg_title_rgb": (28, 22, 18), "bg_content_rgb": (34, 28, 22),
        "title_text_rgb": (255, 245, 235), "body_text_rgb": (240, 225, 210),
        "accent_rgb": (249, 115, 22), "accent_bar_rgb": (234, 88, 12),
        "table_header_bg": (194, 65, 12), "table_row_alt1": (48, 38, 30), "table_row_alt2": (34, 28, 22),
        "footer_text_rgb": (170, 145, 130), "font_title": "Calibri", "font_body": "Calibri",
        "ui_accent": "#f97316", "ui_bg": "#fff7ed"
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


def list_all_ppt_styles() -> List[Dict[str, Any]]:
    """Returns a list of all 50 available presentation styles with metadata."""
    return list(PPT_THEMES.values())


def resolve_ppt_style(style_input: Any) -> Dict[str, Any]:
    """
    Resolves the presentation style from the 50 predefined styles or dynamic palettes.
    Matches direct keys or fuzzy domain keywords automatically.
    """
    if isinstance(style_input, str):
        style_key = style_input.strip().lower()
        if style_key in PPT_THEMES:
            return PPT_THEMES[style_key]

        # Intelligent Keyword Fuzzy Matcher
        if any(w in style_key for w in ["fire", "flame", "hot work", "burner", "cdu", "crude"]):
            return PPT_THEMES["refinery_crude_amber"]
        if any(w in style_key for w in ["pump", "turbine", "compressor", "vibration", "mechanical"]):
            return PPT_THEMES["mechanical_steel_blue"]
        if any(w in style_key for w in ["safety", "green", "hse", "eco", "environment", "oisd"]):
            return PPT_THEMES["emerald_industrial"]
        if any(w in style_key for w in ["danger", "hazard", "red", "emergency", "incident", "alarm"]):
            return PPT_THEMES["crimson_alert"]
        if any(w in style_key for w in ["finance", "gold", "margin", "money", "budget", "grm"]):
            return PPT_THEMES["gold_apex"]
        if any(w in style_key for w in ["ai", "neural", "deepseek", "llm", "inference"]):
            return PPT_THEMES["deepseek_neural_purple"]
        if any(w in style_key for w in ["cyber", "security", "air-gap", "firewall", "ciso"]):
            return PPT_THEMES["cyber_security_matrix"]
        if any(w in style_key for w in ["scada", "plc", "dcs", "automation", "sensors"]):
            return PPT_THEMES["automation_scada_neon"]
        if any(w in style_key for w in ["light", "white", "corporate", "clean", "audit", "cag"]):
            return PPT_THEMES["clean_corporate_light"]
        if any(w in style_key for w in ["legal", "court", "law", "affidavit"]):
            return PPT_THEMES["legal_affidavit_formal"]
        if any(w in style_key for w in ["offshore", "marine", "spm", "tanker", "ocean"]):
            return PPT_THEMES["marine_terminal_ocean"]
        if any(w in style_key for w in ["chemical", "polymer", "catalyst", "reagent"]):
            return PPT_THEMES["chemical_catalyst"]
        if any(w in style_key for w in ["turnaround", "shutdown", "m&i", "overhaul"]):
            return PPT_THEMES["turnaround_shutdown_matrix"]

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
