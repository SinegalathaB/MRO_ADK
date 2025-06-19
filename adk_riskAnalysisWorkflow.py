import asyncio
import json
import pandas as pd
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from adk_inventoryTool import low_stock_agent, supplier_info_agent, best_supplier_agent
from sample_final import analysis_summary, full_schedule, clean_summary, parallel_agent
from sop_qna_tool import part_usage_agent
# from DataLoadAgent import load_line_components_agent,load_digital_logs_agent, load_historical_agent, load_inventory_agent, load_supplier_agent
import subprocess
from read_env import *
import pickle 

# --- App Configuration ---
APP_NAME = "machine_repair_ops"
USER_ID = "repair_user_01"
SESSION_ID = "repair_session_01"
GEMINI_MODEL_2_FLASH = "gemini-2.0-flash"
GEMINI_MODEL_1_5_FLASH = "gemini-1.5-flash"
GEMINI_MODEL_2_5_FLASH_PREVIEW = "gemini-2.5-flash-preview-05-20"
GEMINI_MODEL_2_FLASH_LITE = "gemini-2.0-flash-lite"
GEMINI_MODEL_1_5_FLASH_8B = "gemini-1.5-flash-8b"

# --- Agents ---
high_risk_agent = LlmAgent(
    name="HighRiskIdentificationAgent",
    model=GEMINI_MODEL_2_FLASH_LITE,
    instruction="""
    You are a maintenance expert.
    Using the 'LineComponents' CSV content, identify parts in the specified 'line_name' sanitation line
    that have a failure_probability > 0.90.
    Limit the high risk parts only to the given sanitation line
    Return a list of high-risk parts including:
    - part
    - age
    - max_age
    - line
    Output as JSON.
    [
    {
        "part": "<Part Name>",
        "age": "<age of part>",
        "max_age": "<max_age_of_part>",
        "line": "<sanitation_line_name>"
    },
    ...
    ]
    """,
    output_key="high_risk_parts"
)

historical_analysis_agent = LlmAgent(
    name="HistoricalAnalysisAgent",
    model=GEMINI_MODEL_2_FLASH_LITE,
    instruction="""
You are a Python data analysis agent. Generate Python code that performs the following tasks:

- Use the `high_risk_parts` list (containing part, line, age, and max_age information) and the dataset located at `datasets/Historical_data.csv`.
- Don't use other parts which is not present in input `high_risk_parts` list
- Please only use passed input `high_risk_parts` for graph
- For each entry in `high_risk_parts`:
    - Extract the `part` and `line` values.
    - Filter the historical data to match the current `part` and `line`.
    - For each unique `Parameter` in the filtered data:
        - Generate a line plot with:
            - X-axis: Cycle
            - Y-axis: Value
            - title : part_name_line_name_parameter
            - Horizontal lines for Expected_value_min and Expected_value_max
            - Legends, axis labels, title, grid, and annotated data point values
-Save each generated plot as an image in a directory named plots/, using the filename format:
`part_name_line_name_parameter.png` (replace spaces with underscores)
-Before saving, ensure that the plots/ directory is cleared of all existing files to avoid mixing old and new data.
- Ensure the `plots/` directory is created if it does not exist.
- Return a dictionary mapping each `part_line_parameter` identifier to its saved image file path from the function.
- Execute the function with passing the variable high_risk_parts from previous tool
- assign passed input `high_risk_parts` value for high_risk_parts variable

**Important**:
- The function you define should be executed at the end of the code using the `high_risk_parts` variable.
- **Do not comment out the function call. Make sure it runs.**

Use only the following Python libraries: `pandas`, `matplotlib`, and `os`.

Return a JSON object with two keys:
1. "code" - A string containing the full generated Python code.
2. "high_risk_parts" - The same input list, but each item must exclude the 'line' or 'sanitation_line' field. Include only 'part', 'age', and 'max_age'.
"""
,
    output_key="historical_summary"
)

code_json_cleaner_agent = LlmAgent(
    name="CodeJsonCleanerAgent",
    model=GEMINI_MODEL_2_FLASH,
    instruction="""
You are a JSON formatting assistant.

Your task is to take a JSON-like input object with two fields:
- "code": a multiline Python code block (can contain unescaped newlines or quotes),
- "high_risk_parts": a list of dictionaries.

Clean and return a **valid JSON object** with:
1. The "code" string properly escaped (i.e., convert line breaks to \\n, escape quotes),
2. The "high_risk_parts" array retained exactly as-is.

**Important Rules**:
- Do not return markdown backticks (no ```).
- The final output must be a valid JSON object.
- Escape newline characters (`\n`) and quotes in the "code" block as required by JSON.
- Please use single quotes in all places whenever required
- If the "code" contains indentation or multi-line logic, preserve it by encoding it into a valid JSON string.
- The function you define should be executed at the end of the code using the `high_risk_parts` variable.
- **Do not comment out the function call. Make sure it runs.**

**Example Input**:
{
  "code": "def foo():\n    print(\"bar\")",
  "high_risk_parts": [
    { "part": "X", "age": 12, "max_age": 20, "line": "Line 1" }
  ]
}

**Example Output**:
{
  "code": "def foo():\\n    print(\\\"bar\\\")",
  "high_risk_parts": [
    { "part": "X", "age": 12, "max_age": 20, "line": "Line 1" }
  ]
}
"""
)


log_filter_agent = LlmAgent(
    name="LogFilterAgent",
    model=GEMINI_MODEL_1_5_FLASH,
    instruction="""
You are a log filtering assistant.

Your task is to:
- Take a list of 'high_risk_parts'.
- Take the full 'DigitalLogs' dataset.

For each part in 'high_risk_parts', filter and collect **only** the records from DigitalLogs where the 'Part' column exactly matches the part name.

Return the result as a JSON array like this:
[
  {
    "part": "<Part Name>",
    "data": [<filtered DigitalLogs records for this part>]
  },
  ...
]
"""
)


failure_summary_agent = LlmAgent(
    name="FailureSummaryAgent",
    model=GEMINI_MODEL_1_5_FLASH_8B,
    instruction="""
You are a digital log analyst.

You will analyze pre-filtered part-level failure data using:
- A list of objects with 'part' and its corresponding filtered log 'data'.

For each object:
- Count **failures** as the number of items in 'data'.
- Count **repairs** where 'Action_taken' is exactly 'Fixed the part'.
- Count **replacements** where 'Action_taken' is exactly 'Replaced with spare parts'.
- Count **maintenance_due** where 'Recommended_action' is exactly 'Maintenance'.

Return a JSON array like:
[
  {
    "part": "<Part Name>",
    "failures": <number>,
    "repairs": <number>,
    "replacements": <number>,
    "maintenance_due": <number>,
    "log_records": [<repeat the same filtered data for visibility>],
    "summary": "Based on the log data, the part '<Part Name>' has failed X times — Y times repaired, Z times replaced and M times scheduled maintenance."
  },
  ...
]
"""
)

# Step 1: Initial agent
initial_agent = SequentialAgent(
    name="HighRiskAgent",
    sub_agents=[high_risk_agent,part_usage_agent]
)

plot_agent = SequentialAgent(
    name="PlotGraphAgent",
    sub_agents=[historical_analysis_agent, code_json_cleaner_agent]
)

digitalLog_agent = SequentialAgent(
    name="DigitalLogAgent",
    sub_agents=[log_filter_agent, failure_summary_agent]
)

inventory_agent = SequentialAgent(
    name="InventoryAgent",
    sub_agents=[low_stock_agent, supplier_info_agent, best_supplier_agent]
)

# Step 2: Parallel agents (use high_risk_agent output)
parallel_agent_1 = ParallelAgent(
    name="ParallelInsightsAgent",
    sub_agents=[plot_agent, digitalLog_agent, inventory_agent]
)

pipeline_agent = SequentialAgent(
    name="AgentPipeline",
    sub_agents=[initial_agent, parallel_agent_1]
)

final_pipeline_agent = ParallelAgent(
    name="FinalPipelineAgent",
    sub_agents=[pipeline_agent, parallel_agent]
)