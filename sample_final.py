# === Imports ===
import os
import json
import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from maintenance_pipeline import run_pipeline, post_optimization_schedule
from read_env import *

pd.set_option('display.max_columns', None)

APP_NAME = "maintenance_app"
USER_ID = "user_1"
SESSION_ID = "session_001"
GEMINI_MODEL = "gemini-2.0-flash"
DATASET_PATH = "datasets/synthetic_limited_line_equipment_data_with_maps.csv"
BUDGET = 7000
LABOR_LIMITS = {
    "DAY+1": 20,
    "DAY+2": 25,
    "DAY+3": 15,
    "DAY+4": 10
}

# === Input Schemas ===
class MaintenanceAgentInput(BaseModel):
    analysis_summary: Dict[str, Any] = Field(
        ..., description="Summary of the equipment-level data before optimization."
    )
    full_schedule: List[Dict[str, Any]] = Field(
        ..., description="List of post-optimization per-equipment maintenance decisions."
    )

class PostOptAgentInput(BaseModel):
    summary: Dict[str, Any] = Field(
        ..., description="Summary of the post-optimization schedule."
    )

# === LLM Agents ===
maintenance_plan_agent = LlmAgent(
    name="MaintenancePlanAgent",
    model=GEMINI_MODEL,
    instruction=(
        "You are a maintenance plan summary expert. Use 'analysis_summary' and 'full_schedule' to provide "
        "an insightful summary. Mention total_equipment, avg_failure_probability, high_risk_count, "
        "total_unoptimized_risk, and insights from optimized_risk scores, cost, labor_hours, etc."
    ),
    description="Generates overall maintenance plan summary.",
    input_schema=MaintenanceAgentInput,
    output_key="maintenance_plan_for_all"
)

post_optimization_agent = LlmAgent(
    name="PostOptimizationAgent",
    model=GEMINI_MODEL,
    instruction=(
        "You are provided with a post-optimization summary. Generate a concise executive overview "
        "including cost impact, ROI projections, labor efficiency, and other key insights."
    ),
    description="Generates summary for the optimized maintenance schedule.",
    input_schema=PostOptAgentInput,
    output_key="maintenance_details_of_maintained"
)

# === Agent Orchestration ===
parallel_agent = ParallelAgent(
    name="ParallelMaintenanceAgent",
    sub_agents=[maintenance_plan_agent, post_optimization_agent],
    description="Runs maintenance summary and post-optimization agents in parallel."
)

# === Pipeline Execution ===
results = run_pipeline(DATASET_PATH, BUDGET)
analysis_summary = results["analysis_summary"]
full_schedule = results["full_schedule"]
plan_schedule_df = results["plan_schedule_df"]
post_optimization_results = post_optimization_schedule(plan_schedule_df, LABOR_LIMITS)
post_summary = post_optimization_results["summary"]
clean_summary = {k: (int(v) if isinstance(v, np.integer) else v) for k, v in post_summary.items()}

