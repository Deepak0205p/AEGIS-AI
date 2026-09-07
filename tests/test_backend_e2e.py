"""
End-to-End Integration Verification Test Suite.
Tests all endpoints, modes, database persistence, sandbox execution, and deliverable builders.
"""

import sys
import os
import json
import unittest
from pathlib import Path

# Set offline environment variables
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_NO_USAGE_STATS"] = "1"

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import MODEL_NAME, OLLAMA_HOST
from backend.router import route_message
from backend.sandbox import execute_python_sandbox
from backend.deliverables import build_docx, build_xlsx, build_pptx
from backend.db import init_db, save_message, get_chat_history, save_file_record, get_file_record
from fastapi.testclient import TestClient
from backend.main import app


class BackendEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Tests GET /api/health."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["ollama_connected"])
        self.assertEqual(data["model"], MODEL_NAME)

    def test_02_router_keywords(self):
        """Tests heuristic router keyword/regex matching."""
        # Code keywords
        route, kw = route_message("Can you debug this python script for me?")
        self.assertEqual(route, "code")
        self.assertIn(kw, ["python", "script", "debug"])
        
        route, kw = route_message("Write an algorithm to sort array")
        self.assertEqual(route, "code")
        self.assertIn(kw, ["algorithm", "array"])

        # Docs keywords
        route, kw = route_message("Please draft a docx memo for manager approval")
        self.assertEqual(route, "docs")
        self.assertIn(kw, ["docx", "memo", "draft", "approval"])

        # Excel keywords
        route, kw = route_message("Build an excel sheet with table data")
        self.assertEqual(route, "excel")
        self.assertIn(kw, ["excel", "sheet", "table data"])

        # PPT keywords
        route, kw = route_message("Create a slide presentation deck for the meeting")
        self.assertEqual(route, "ppt")
        self.assertIn(kw, ["presentation", "slides", "deck"])

        # Default Chat
        route, kw = route_message("What is the current temperature in boiler 2?")
        self.assertEqual(route, "chat")

    def test_03_sandbox_execution(self):
        """Tests Python sandbox execution (stdlib + numpy + openpyxl)."""
        code = (
            "import numpy as np\n"
            "arr = np.array([10.0, 20.0, 30.0])\n"
            "print(f'MEAN_RESULT={np.mean(arr):.1f}')\n"
        )
        res = execute_python_sandbox(code)
        self.assertTrue(res["success"], f"Sandbox error: {res['stderr']}")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("MEAN_RESULT=20.0", res["stdout"])

    def test_04_deliverable_builders(self):
        """Tests docx, xlsx, pptx file builders."""
        plan = {
            "title": "Industrial Turbine Inspection",
            "filename": "turbine_inspection.docx",
            "blocks": [
                {"type": "heading", "text": "Operating Metrics", "level": 1},
                {"type": "paragraph", "text": "The high pressure turbine underwent vibration analysis."},
                {"type": "bullets", "items": ["Vibration: 2.1 mm/s", "Pressure: 15.4 bar"]},
                {
                    "type": "table",
                    "title": "Sensor Telemetry",
                    "rows": [
                        ["Timestamp", "Temp (°C)", "Vibration (mm/s)"],
                        ["08:00", "340.5", "1.9"],
                        ["12:00", "352.1", "2.1"],
                        ["16:00", "348.0", "2.0"]
                    ]
                }
            ]
        }
        
        # 1. Test DOCX
        fid, fname, fpath = build_docx(plan, "test_chat_deliverable")
        self.assertTrue(Path(fpath).exists())
        self.assertTrue(fpath.stat().st_size > 0)
        
        # 2. Test XLSX
        fid_x, fname_x, fpath_x = build_xlsx(plan, "test_chat_deliverable")
        self.assertTrue(Path(fpath_x).exists())
        self.assertTrue(fpath_x.stat().st_size > 0)
        
        # 3. Test PPTX
        fid_p, fname_p, fpath_p = build_pptx(plan, "test_chat_deliverable")
        self.assertTrue(Path(fpath_p).exists())
        self.assertTrue(fpath_p.stat().st_size > 0)

    def test_05_db_and_history(self):
        """Tests MySQL message persistence and history API."""
        chat_id = "test_history_session"
        save_message(chat_id, "user", "What is the speed of pump 1?", "chat")
        save_message(chat_id, "assistant", "Pump 1 is running at 1450 RPM.", "chat")
        
        resp = self.client.get(f"/api/history/{chat_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["chat_id"], chat_id)
        self.assertGreaterEqual(data["count"], 2)
        self.assertEqual(data["messages"][0]["content"], "What is the speed of pump 1?")


if __name__ == "__main__":
    unittest.main()
