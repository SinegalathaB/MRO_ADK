import pandas as pd
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json
from read_env import *
import pickle
import asyncio
import re

# Constants
GEMINI_MODEL_2_FLASH = "gemini-2.0-flash"
APP_NAME = "machine_repair_ops"
USER_ID = "repair_user_01"
SESSION_ID = "repair_session_01"

high_risk_part_summary_alert_agent = LlmAgent(
    name="HighRiskPartsSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are an intelligent analytics assistant for operations.

Given a table called `high_risk_parts` with the following columns:
- 'part'
- 'age'
- 'max_age'
- 'line'
- 'part_usage'

Your task is to generate both a **business summary** and a **short alert message**:

1. **Business Summary (2 lines max):**
   - Mention how many parts are at high risk.
   - Explain the reason (e.g., aging close to max_age).
   - Keep it concise, executive-friendly, and avoid raw table dumps.

2. **Alert Message (6 words or fewer):**
   - Format: `"X Parts at High Risk"`

Return the result in the following JSON format:
```json
{
  "summary": "Short 2-line summary goes here.",
  "alert": "X Parts at High Risk"
}
Only return valid JSON.
""",
output_key="summary_and_alert"
)


digital_log_summary_alert_agent = LlmAgent(
    name="DigitalLogSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a maintenance performance intelligence assistant.

Given a list called `digital_log_data` with the following fields for each part:
- part: Name of the machine component
- failures: Number of failures
- repairs: Number of repairs
- replacements: Number of replacements
- maintenance_due: Number of upcoming scheduled maintenances
- summary: One-line maintenance status (already provided)

Perform the following two tasks:

1. **Summary (2–3 lines)**:
   - Highlight parts with frequent failures, high repair-to-failure ratios, or under-maintenance.
   - Suggest maintenance action where needed.
   - Keep the summary formal, concise, and meant for plant managers.

2. **Alert Message (6 words or fewer)**:
   - Focus on critical parts or situations.
   - Format ideas: 
     - "Critical Failures Detected"
     - "Under-Maintained Part Alert"
     - "High Failure Rate: XYZ Part"
     - Avoid full sentences.

Return your response strictly in this JSON format:
```json
{
  "summary": "<2-3 line summary here>",
  "alert": "<6-word alert here>"
}
Only return valid JSON. Avoid listing all parts or full data dumps.
""",
output_key="summary_and_alert"
)

high_risk_threshold_summary_alert_agent = LlmAgent(
    name="HighRiskPartsThresholdSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a professional maintenance insights assistant.

You are given a dataset called `historicaldata` containing historical sensor readings for high-risk machine parts. Each row includes:
- Part: Name of the part
- Parameter: Sensor parameter being tracked
- Value: Actual observed value
- Expected_value_min: Minimum acceptable value
- Expected_value_max: Maximum acceptable value

Some parts have exceeded thresholds—either upper, lower, or both.

Your task is two-fold:

1. **Summary (2–3 lines)**:
   - Mention the part and parameter that breached thresholds.
   - Include how many cycles it breached and whether the values were mostly too high, too low, or fluctuated both ways.
   - Recommend checking or replacing parts with significant breaches.
   - Tone must be formal, concise, and suitable for maintenance planning.

2. **Alert Message (max 6 words)**:
   - Focused and suitable for dashboards.
   - Format examples:
     - "Threshold Breach: Pump Temperature"
     - "Param Alert: Rotor Vibration"
     - "Sensor Spike: Oil Pressure"

Return your response strictly in the following JSON format:
```json
{
  "summary": "<summary text>",
  "alert": "<6-word alert message>"
}
Respond only with valid JSON. Avoid listing all rows or full tables.
""",
output_key="summary_and_alert"
)

low_stock_summary_alert_agent = LlmAgent(
    name="LowStockSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a professional inventory intelligence assistant.

You are given a table named `parts_with_low_stocks`, which contains:
- `part_name`: Name of the part
- `stock`: Current stock level (always < 5)

Your task is to return two key outputs:

1. **Summary (2–3 lines)**:
   - State how many parts have critically low stock.
   - Highlight parts with stock levels of 1 or 0 as urgent.
   - Recommend immediate restocking to prevent operational or production delays.
   - Tone must be clear, formal, and suitable for supply chain executives.

2. **Alert Message (max 6 words)**:
   - Short, actionable message for dashboards.
   - Format examples:
     - "Urgent Restock: 7 Parts"
     - "Critical Inventory Alert"
     - "Low Stock: Gear Assemblies"

Return both in **valid JSON format** like this:
```json
{
  "summary": "<summary text>",
  "alert": "<6-word alert message>"
}
Respond only with the JSON output. Do not include tables or any other explanatory text.
""",
output_key="summary_and_alert"
)


supplier_summary_alert_agent = LlmAgent(
    name="SupplierPerformanceSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a strategic sourcing and procurement expert.

You are given a table `supplier_performance_data` with the following columns:
- `Part`: Name of the part
- `Supplier`: Name of the supplier
- `Historical_OTD`: On-Time Delivery rate (0–1)
- `Historical_quality_rate`: Quality performance rate (0–1)

Your task is to produce two outputs:

1. **Summary (2–3 lines)**:
   - Compare suppliers for each part on delivery and quality.
   - Highlight best-performing suppliers, single-supplier dependencies, or suppliers needing improvement.
   - Recommend supplier diversification or improvement areas where necessary.
   - Keep the tone formal, suitable for procurement leaders and supply chain managers.

2. **Alert Message (max 6 words)**:
   - Business-relevant, actionable alert.
   - Examples:
     - "Supplier Risk: Quality Concerns Noted"
     - "Top Supplier Identified: Bearings"
     - "Diversify Supply for Gearbox"

Return your response in **JSON format** like this:
```json
{
  "summary": "<2–3 line business summary>",
  "alert": "<short alert message>"
}
Respond only with the JSON output. Do not repeat the table or any additional explanation.
""",
output_key="summary_and_alert"
)

best_supplier_summary_alert_agent = LlmAgent(
    name="BestSupplierSummaryAgent",
    model="gemini-2.0-flash-lite",
    instruction="""
You are a procurement intelligence analyst.

You are provided with a table `best_supplier_data` with the following columns:
- `Part`: Name of the part
- `Supplier`: Name of the top-performing supplier
- `Historical_quality_rate`: Quality rate (0–1)
- `Score`: Composite score for evaluating supplier performance

Your task is to produce two outputs:

1. **Summary (2 lines)**:
   - Identify the top-performing supplier for each part based on score and quality.
   - Highlight why these suppliers stand out (e.g., exceptional quality, high overall score).
   - Tone should be strategic and tailored for executive sourcing decisions.

2. **Alert Message (≤6 words)**:
   - Short, business-relevant, and action-oriented.
   - Examples:
     - "Top Suppliers Identified for All Parts"
     - "High Quality Vendors Confirmed"
     - "Exceptional Supplier Performance Noted"

Return your output in the following JSON format:
```json
{
  "summary": "<2-line executive summary>",
  "alert": "<short alert message>"
}
Respond only with the JSON output. Do not include the table or additional commentary.
""",
output_key="summary_and_alert"
)


summarization_parallel_alert_agent = ParallelAgent(
    name="ParallelSummaryAgent",
    sub_agents=[
        high_risk_part_summary_alert_agent,
        high_risk_threshold_summary_alert_agent,
        low_stock_summary_alert_agent,
        supplier_summary_alert_agent,
        best_supplier_summary_alert_agent,
        digital_log_summary_alert_agent
    ]
)


async def run_summary_and_alert_pipeline(filename):
    # filename = "processed_responses_Sanitization_Line_2.pkl"
    with open(filename, "rb") as f:
        responses = pickle.load(f)

    # Extract and convert data
    hish_risk_part_df = responses['high_risk_parts_data']
    hish_risk_part_json = hish_risk_part_df.to_dict(orient='records')

    digital_log_df = responses['digital_log']
    digital_log_json = digital_log_df.to_dict(orient='records')

    low_stock_parts_df = responses["low_stock_parts"]
    low_stock_parts_json = low_stock_parts_df.to_dict(orient='records')

    supplier_info_df = responses['supplier_info']
    supplier_info_json = supplier_info_df.to_dict(orient='records')

    best_supplier_df = responses['best_supplier']
    best_supplier_json = best_supplier_df.to_dict(orient='records')

    def get_exceeded_parameter_dataframe(high_risk_parts: pd.DataFrame, historical_data_path: str) -> pd.DataFrame:
        historical_df = pd.read_csv(historical_data_path)
        exceeded_rows = []

        for _, part_row in high_risk_parts.iterrows():
            part_name = part_row['part']
            part_data = historical_df[historical_df['Part'] == part_name]
            parameters = part_data['Parameter'].dropna().unique()

            for parameter in parameters:
                param_df = part_data[part_data['Parameter'] == parameter]
                exceeded_df = param_df[
                    (param_df['Value'] < param_df['Expected_value_min']) |
                    (param_df['Value'] > param_df['Expected_value_max'])
                ]
                if not exceeded_df.empty:
                    exceeded_rows.append(exceeded_df)

        return pd.concat(exceeded_rows, ignore_index=True) if exceeded_rows else pd.DataFrame()

    parameter_range_exceeded_df = get_exceeded_parameter_dataframe(
        hish_risk_part_df, r"datasets\Historical_data.csv"
    )
    parameter_range_exceeded_json = parameter_range_exceeded_df.to_dict(orient='records')

    async def getSummaryofAgent():
        session_service = InMemorySessionService()
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        # runner = Runner(agent=summarization_parallel_agent, app_name=APP_NAME, session_service=session_service)
        runner = Runner(agent=summarization_parallel_alert_agent, app_name=APP_NAME, session_service=session_service)

        content = types.Content(
            role="user",
            parts=[
                types.Part(text=json.dumps({"high_risk_parts": hish_risk_part_json})),
                types.Part(text=json.dumps({"historicaldata": parameter_range_exceeded_json})),
                types.Part(text=json.dumps({"parts_with_low_stocks": low_stock_parts_json})),
                types.Part(text=json.dumps({"supplier_performance_data": supplier_info_json})),
                types.Part(text=json.dumps({"best_supplier_data": best_supplier_json})),
                types.Part(text=json.dumps({"digital_log_data": digital_log_json}))
            ]
        )

        agent_summaries = {}
        async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
            if hasattr(event, "content") and event.content and event.content.parts:
                agent_name = event.author
                for part in event.content.parts:
                    if part.text:
                        # Extract JSON block from markdown-style code block
                        match = re.search(r'```json\s*(\{.*?\})\s*```', part.text, re.DOTALL)
                        if match:
                            try:
                                json_data = json.loads(match.group(1))
                                agent_summaries[agent_name] = json_data
                            except json.JSONDecodeError:
                                print(f"Failed to decode JSON for agent: {agent_name}")
        # print(agent_summaries)

        return agent_summaries

    result = await getSummaryofAgent()
    print("RESULT***",result)


    alert_input_list = []
    for i in result:
        if i == "HighRiskPartsSummaryAgent":
            alert_input_list.append(["HighRiskPartsSummaryAgent", hish_risk_part_df, hish_risk_part_json, result[i]['summary'], result[i]['alert']])
        elif i == "HighRiskPartsThresholdSummaryAgent":
            alert_input_list.append(["HighRiskPartsThresholdSummaryAgent", parameter_range_exceeded_df, parameter_range_exceeded_json, result[i]['summary'], result[i]['alert']])
        elif i == "LowStockSummaryAgent":
            alert_input_list.append(["LowStockSummaryAgent", low_stock_parts_df, low_stock_parts_json, result[i]['summary'], result[i]['alert']])
        elif i == "SupplierPerformanceSummaryAgent":
            alert_input_list.append(["SupplierPerformanceSummaryAgent", supplier_info_df, supplier_info_json, result[i]['summary'], result[i]['alert']])
        elif i == "BestSupplierSummaryAgent":
            alert_input_list.append(["BestSupplierSummaryAgent", best_supplier_df, best_supplier_json, result[i]['summary'], result[i]['alert']])
        elif i == "digital_log_summary_agent":
            alert_input_list.append(["digital_log_summary_agent", digital_log_df, digital_log_json, result[i]['summary'], result[i]['alert']])
    print(alert_input_list)
    # final_result_summary_alert = await get_alert_notifications(alert_input_list)

    final_ui_processed_filename = f"final_ui_{filename}"
    with open(final_ui_processed_filename, "wb") as f:
        pickle.dump(alert_input_list, f)

    return final_ui_processed_filename
# async def main():
#     filename = "processed_responses_Sanitization_Line_2.pkl"
#     result_file = await run_summary_and_alert_pipeline(filename)
#     print(f"Summary and alert results saved to: {result_file}")

# # Run the async function
# asyncio.run(main())