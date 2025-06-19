from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import json
import pandas as pd
import pickle
import asyncio
from read_env import *

with open("high_risk_parts_data.pkl", "rb") as f:
    high_risk_parts_data = pickle.load(f)

print(high_risk_parts_data)

APP_NAME = "machine_repair_ops"
USER_ID = "repair_user_01"
SESSION_ID = "repair_session_01"
GEMINI_MODEL_2_FLASH = "gemini-2.0-flash"
GEMINI_MODEL_1_5_FLASH = "gemini-1.5-flash"
GEMINI_MODEL_2_5_FLASH_PREVIEW = "gemini-2.5-flash-preview-05-20"
GEMINI_MODEL_2_FLASH_LITE = "gemini-2.0-flash-lite"
GEMINI_MODEL_2_5_PRO_PREVIEW = "gemini-2.5-pro-preview-06-05"


low_stock_agent = LlmAgent(
    name="LowStockPartsAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a supply chain analyst.

Using the input list `high_risk_parts` (each with keys 'part', 'age', 'max_age', 'line') and `Inventory` dataset:
- For each part in `high_risk_parts`, find its stock from the `Inventory` data (match where 'Part' equals `part`).
- Identify parts in high_risk_parts where stock is less than 5.
- Don't consider low stock on whole data. Only take the parts present in high_risk_parts list
- Return a JSON list of such part names.

Return the result as a JSON array like this:
[
  {
    "part": "<Part Name>",
    "stock": <remaining stock count>
  },
  ...
]

Example output:
[
  {
    "part": "Pump 1",
    "stock": 3
  },
  {
    "part": "Valve 3",
    "stock": 1
  }
]
""",
    output_key="low_stock_parts"
)

supplier_info_agent = LlmAgent(
    name="SupplierInfoAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a supplier data assistant.

Given a list of part names (`low_stock_parts`) and the dataset `Suppliers`:
- For each part, find all matching rows from `Suppliers` where the 'Part' matches the part name.
- Return a dictionary in JSON where each part name maps to a list of supplier records (as dictionaries).

Return the result in the following format:
{
  "<Part Name>": [
    {
      "Part": "<Part Name>",
      "Supplier": "<Supplier Name>",
      "Supplier_location": "<Location>",
      "Procurement_cost": <Cost>,
      "MOQ": <Minimum Order Quantity>,
      "Lead_time_days": <Lead Time>,
      "Transportation_cost": <Cost>,
      "Historical_OTD": <On Time Delivery Rate>,
      "Historical_quality_rate": <Quality Rate>
    },
    ...
  ],
  ...
}

Example output:
{
  "2nd Stage Feed Screw": [
    {
      "Part": "2nd Stage Feed Screw",
      "Supplier": "Supplier 1",
      "Supplier_location": "China",
      "Procurement_cost": 900,
      "MOQ": 6,
      "Lead_time_days": 12,
      "Transportation_cost": 200,
      "Historical_OTD": 0.81,
      "Historical_quality_rate": 0.9
    }
  ],
  "Control Valve": [
    {
      "Part": "Control Valve",
      "Supplier": "Supplier A",
      "Supplier_location": "Germany",
      "Procurement_cost": 620,
      "MOQ": 3,
      "Lead_time_days": 10,
      "Transportation_cost": 150,
      "Historical_OTD": 0.95,
      "Historical_quality_rate": 0.93
    },
    {
      "Part": "Control Valve",
      "Supplier": "Supplier B",
      "Supplier_location": "India",
      "Procurement_cost": 600,
      "MOQ": 5,
      "Lead_time_days": 9,
      "Transportation_cost": 180,
      "Historical_OTD": 0.92,
      "Historical_quality_rate": 0.9
    }
  ]
}
""",
    output_key="supplier_info"
)

best_supplier_agent = LlmAgent(
    name="BestSupplierSelectorAgent",
    model=GEMINI_MODEL_2_FLASH,
    instruction="""
You are an intelligent supplier ranking system.

You are given a dictionary `supplier_info` where:
- Each key is a part name
- Each value is a list of suppliers for that part, each supplier has:
    - Historical_OTD (on-time delivery, 0-1)
    - Historical_quality_rate (0-1)
    - Procurement_cost (float)
    - Transportation_cost (float)
    - MOQ (minimum order quantity)
    - Lead_time_days (int)
    - Supplier (string)

For each supplier, calculate the score using:
  Score =
    (Historical_OTD * 0.20) +
    (Historical_quality_rate * 0.20) +
    (Procurement_cost * 0.25) +
    (Transportation_cost * 0.10) +
    (MOQ * 0.10) +
    (Lead_time_days * 0.15)

Pick the supplier with the **highest** score as the best supplier for each part.
Return a JSON object mapping each part name to its best supplier.

Format your output as:
{
  "<Part Name>": {
    "Part": "<Part Name>",
    "Supplier": "<Supplier Name>",
    "Supplier_location": "<Location>",
    "Procurement_cost": <Cost>,
    "MOQ": <MOQ>,
    "Lead_time_days": <Days>,
    "Transportation_cost": <Cost>,
    "Historical_OTD": <Value>,
    "Historical_quality_rate": <Value>,
    "Score": <Final Computed Score>
  },
  ...
}

Example output:
{
  "2nd Stage Feed Screw": {
    "Part": "2nd Stage Feed Screw",
    "Supplier": "Supplier 1",
    "Supplier_location": "China",
    "Procurement_cost": 900,
    "MOQ": 6,
    "Lead_time_days": 12,
    "Transportation_cost": 200,
    "Historical_OTD": 0.81,
    "Historical_quality_rate": 0.9,
    "Score": 0.2 * 0.81 + 0.2 * 0.9 + 0.25 * 900 + 0.1 * 200 + 0.1 * 6 + 0.15 * 12
  }
}
""",
    output_key="best_suppliers"
)

