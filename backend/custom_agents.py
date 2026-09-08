"""
Custom Agent Registry & Agentic Workflow Orchestrator.
Allows operators and engineers to create, customize, and execute personalized AI agents.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.config import logger

class CustomAgent(BaseModel):
    id: str
    name: str
    avatar: str = "🤖"
    role: str
    description: str
    system_prompt: str
    workflow_mode: str = "sequential_agentic"  # sequential_agentic | direct_fast | autonomous_loop
    tools: List[str] = Field(default_factory=lambda: ["rag", "sandbox", "deliverables", "chemicals"])
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_template: bool = False
    author: str = "Operator"

# Starter Templates
DEFAULT_TEMPLATES = [
    CustomAgent(
        id="template-cdu-yield-auditor",
        name="CDU Yield & Margin Auditor",
        avatar="⚡",
        role="Process Optimization Specialist",
        description="Analyzes Crude Distillation Unit assay yields, furnace skin temps, and calculates gross refining margins (GRM).",
        system_prompt="You are the CDU Yield & Margin Auditor agent. Your objective is to audit distillation yields, calculate volumetric fractions, and flag any skin temperature deviations exceeding 420°C. When performing yield math, write and execute precise Python calculations. Ground all operational guidelines strictly in MRPL/OISD standards.",
        workflow_mode="sequential_agentic",
        tools=["rag", "sandbox", "deliverables"],
        is_template=True,
        author="System Template"
    ),
    CustomAgent(
        id="template-hse-shift-summarizer",
        name="HSE Shift & Incident Logger",
        avatar="🛡️",
        role="HSE Safety Auditor & Compliance Lead",
        description="Audits Hot Work & Confined Space permits, validates OISD-STD-105 compliance, and generates shift handoff reports.",
        system_prompt="You are the HSE Shift & Incident Logger agent. Your objective is to verify safety permits, inspect gas testing thresholds (H2S < 10 ppm, LEL = 0%), and compile structured shift handover summaries with timestamped action items. Always cite referenced safety standards.",
        workflow_mode="sequential_agentic",
        tools=["rag", "chemicals", "deliverables"],
        is_template=True,
        author="System Template"
    ),
    CustomAgent(
        id="template-vibration-reliability-eng",
        name="Equipment Reliability & Vibration Eng",
        avatar="⚙️",
        role="Mechanical Reliability Engineer",
        description="Assesses centrifugal pump vibration spectra (ISO 10816), bearing temperatures, and computes MTBF metrics.",
        system_prompt="You are the Equipment Reliability & Vibration Engineer. Your goal is to evaluate pump vibration velocity (mm/s RMS), check ISO 10816-3 Zone alarms, and run hydrodynamic or MTBF calculations using the Python Sandbox. Generate formal inspection summaries.",
        workflow_mode="sequential_agentic",
        tools=["rag", "sandbox", "deliverables"],
        is_template=True,
        author="System Template"
    ),
    CustomAgent(
        id="template-pid-isa-inspector",
        name="P&ID Instrument & ISA-5.1 Tag Inspector",
        avatar="🔬",
        role="Instrumentation & Process Automation Lead",
        description="Extracts and verifies P&ID instrument loop tags (PT, TT, FT, ESDV), loop interlocks, and fail-safe actions.",
        system_prompt="You are the P&ID Instrument & ISA-5.1 Inspector. Your objective is to parse P&ID diagrams, verify tag nomenclatures, and check that emergency shutdown valves (ESDV) are properly specified with fail-closed (FC) safety positions.",
        workflow_mode="direct_fast",
        tools=["rag", "deliverables"],
        is_template=True,
        author="System Template"
    )
]

# In-memory storage with templates
_agents_store: Dict[str, CustomAgent] = {t.id: t for t in DEFAULT_TEMPLATES}

def get_all_agents() -> List[CustomAgent]:
    return list(_agents_store.values())

def get_agent_by_id(agent_id: str) -> Optional[CustomAgent]:
    return _agents_store.get(agent_id)

def create_or_update_agent(agent: CustomAgent) -> CustomAgent:
    _agents_store[agent.id] = agent
    logger.info(f"[AGENTS] Saved custom agent: id={agent.id} name='{agent.name}' by author='{agent.author}'")
    return agent

def delete_agent(agent_id: str) -> bool:
    if agent_id in _agents_store:
        del _agents_store[agent_id]
        logger.info(f"[AGENTS] Deleted custom agent: id={agent_id}")
        return True
    return False

def get_system_temporal_context_block() -> str:
    """Returns authoritative live system date, time, and shift context."""
    now = datetime.now()
    hour = now.hour
    
    if 6 <= hour < 14:
        shift_name = "Morning Shift (Shift-A: 06:00 - 14:00 HRS)"
    elif 14 <= hour < 22:
        shift_name = "Evening Shift (Shift-B: 14:00 - 22:00 HRS)"
    else:
        shift_name = "Night Shift (Shift-C: 22:00 - 06:00 HRS)"
        
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%H:%M:%S IST")
    iso_str = now.isoformat()
    
    return (
        "=== LIVE SYSTEM TEMPORAL CONTEXT ===\n"
        f"- Current System Date: {date_str}\n"
        f"- Current System Time: {time_str}\n"
        f"- Active Plant Shift: {shift_name}\n"
        f"- ISO Timestamp: {iso_str}\n"
        "- TEMPORAL GROUNDING RULE: Whenever the user asks for the current date, time, year, month, or shift handover timing, "
        "OR when writing Python scripts/deliverable reports requiring timestamps, ALWAYS utilize the authoritative live system time provided above. "
        "In Python code, you can also directly call `from datetime import datetime; now = datetime.now()`.\n"
        "====================================="
    )
