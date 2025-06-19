import streamlit as st
import pandas as pd
import asyncio
import json
import os
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import numpy as np

# Assuming maintenance_pipeline.py is in the same directory
from maintenance_pipeline import run_pipeline, post_optimization_schedule

# Set pandas display options
pd.set_option('display.max_columns', None)

# --- Configuration ---
APP_NAME = "maintenance_app"
USER_ID = "user_1"
SESSION_ID = "session_001"
GEMINI_MODEL = "gemini-2.0-flash" # Consider using gemini-1.5-flash or gemini-1.5-pro for better performance if needed

# --- Google API Key (ensure this is handled securely in a real application) ---
# For demonstration purposes, setting directly. In production, use Streamlit secrets or environment variables.
# os.environ["GOOGLE_API_KEY"] = "AIzaSyDLy8LHHPUyomure9V7KxLKhBDSfsv22Lw"
# It's highly recommended to use Streamlit secrets for your API key:
# Go to your Streamlit app, then Settings -> Secrets, and add GOOGLE_API_KEY = "your_api_key_here"
os.environ["GOOGLE_API_KEY"]="AIzaSyDLy8LHHPUyomure9V7KxLKhBDSfsv22Lw"

# --- Pydantic Models ---
class MaintenanceAgentInput(BaseModel):
    analysis_summary: Dict[str, Any] = Field(
        ...,
        description="Summary of the the equipment level data before its optimized for maintenance"
    )
    full_schedule: List[Dict[str, Any]] = Field(
        ...,
        description="List of per-equipment dicts with post-optimization fields (decision(maintain/skip),maintenance_order, optimized_risk, etc.)"
    )
    post_optimization_summary: Dict[str, Any] = Field(description="Concise Summary of equipments that need to be maintained")

class MaintenanceAgentOutput(BaseModel):
    Alerts: str = Field(description="Short crisp inputs that the user needs to be alerted about.")
    Details: str = Field(description="Concise Summary of equipments that need to be maintained")
    Recommended_Actions: str = Field(description="Recommended next steps")

# --- Maintenance Plan Agent Definition ---
maintenance_plan_agent = LlmAgent(
    name="MaintenancePlanAgent",
    model=GEMINI_MODEL,
    instruction="""You are a maintenance plan summary expert.Your have three inputs- 'analysis_summary','full_schedule' and 'post_optimization_summary'.Come up with a general summary using 'analysis_summary'(keys like total_equipment,avg_failure_probability,high_risk_count and total_unoptimized_risk)
    In 'full_schedule' you have the following-
    For each piece of equipment (identified by equipment_id), you know its age, how many times it’s been 
    maintained (maintenance_count), the cost and labor hours required for maintenance, its risk_impact and 
    failure_probability. Subject to overall budget(fixed) and manpower limits, you now also know exactly which units 
    to maintain or skip, and an optimized_risk score for each equipment_id.
    In 'post_optimization_summary',you are given details of equipments that have been identified for maintenance for fixed labour limits 

    Your job is to review the maintenance plan details and give a structured output involving three things:
    1.Alerts -  Alerts should include information such as equipments that need to be maintained,at risk etc.
    2.Details - Give a crisp summary based on all the information available and any insights that you can derive.
    3.Recommended_Actions - Using only the information available come up with the recommended next steps.
    
    Alerts,Details and Recommended_Actions must be in form of numbered points.
        """,
    description="Generates maintenance plan summary analysis based on detailed post-optimization data.",
    input_schema=MaintenanceAgentInput,
    output_schema=MaintenanceAgentOutput
)

# --- Function to run the agent asynchronously ---
async def run_maintenance_agent(analysis_summary, full_schedule, post_optimization_summary):
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    runner = Runner(agent=maintenance_plan_agent, app_name=APP_NAME, session_service=session_service)

    # Convert numpy types in summary to standard Python types for JSON serialization
    summary_for_json = {}
    for k, v in post_optimization_summary.items():
        if isinstance(v, (np.integer, np.floating)): # Handle both int and float numpy types
            v = int(v) if isinstance(v, np.integer) else float(v)
        summary_for_json[k] = v

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=json.dumps({"analysis_summary": analysis_summary})),
            types.Part(text=json.dumps({"full_schedule": full_schedule})),
            types.Part(text=json.dumps({"post_optimization_summary": summary_for_json})) # Changed key to match input_schema
        ]
    )

    responses = []
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if hasattr(event, 'content') and hasattr(event.content, 'parts'):
            for part in event.content.parts:
                if hasattr(part, 'text'):
                    responses.append(part.text)
    return responses

# --- Streamlit UI ---
# st.set_page_config(layout="wide", page_title="Maintenance Planning Dashboard")

st.title("⚙️ Equipment Maintenance Planning Dashboard")

st.markdown("""
This application helps in optimizing maintenance schedules based on budget and labor constraints.
Input your desired budget and daily labor limits to generate a tailored maintenance plan summary.
""")

st.sidebar.header("Configuration")

# User inputs for budget and labor limits
st.sidebar.subheader("Budget and Labor Limits")
budget_limit = st.sidebar.slider("Select Budget Limit", min_value=1000, max_value=20000, value=7000, step=500)

st.sidebar.markdown("Define daily labor limits:")
labor_limits = {}
labor_limits["DAY+1"] = st.sidebar.number_input("Labor Limit Day + 1", min_value=0, value=20, step=1)
labor_limits["DAY+2"] = st.sidebar.number_input("Labor Limit Day + 2", min_value=0, value=25, step=1)
labor_limits["DAY+3"] = st.sidebar.number_input("Labor Limit Day + 3", min_value=0, value=15, step=1)
labor_limits["DAY+4"] = st.sidebar.number_input("Labor Limit Day + 4", min_value=0, value=10, step=1)


# Path to the CSV file (adjust if necessary for deployment)
# Using a relative path for better portability if the CSV is in the same directory as the script.
DATA_PATH = "synthetic_limited_line_equipment_data_with_maps.csv" # Ensure this file is present

if not os.path.exists(DATA_PATH):
    st.error(f"Data file not found: {DATA_PATH}. Please make sure the CSV is in the same directory as the script.")
else:
    if st.sidebar.button("Generate Maintenance Plan"):
        with st.spinner("Generating maintenance plan... This may take a moment."):
            try:
                # Run the initial pipeline
                results = run_pipeline(DATA_PATH, budget_limit)
                analysis_summary = results["analysis_summary"]
                full_schedule = results["full_schedule"]
                plan_schedule_df = results["plan_schedule_df"]

                # Run post-optimization schedule
                result_post = post_optimization_schedule(plan_schedule_df, labor_limits)
                post_optimization_summary = result_post["summary"]

                # Run the LLM agent
                agent_responses = asyncio.run(run_maintenance_agent(
                    analysis_summary,
                    full_schedule,
                    post_optimization_summary
                ))

                st.subheader("📊 Maintenance Plan Summary")

                # Display the agent's output
                if agent_responses:
                    try:
                        # The agent returns a list of strings, each string might be a JSON object
                        # We need to parse each and combine if necessary, or just take the first valid one.
                        parsed_response = {}
                        for res_str in agent_responses:
                            try:
                                json_res = json.loads(res_str)
                                # Assuming the agent's output is directly the Pydantic model's JSON
                                if "Alerts" in json_res and "Details" in json_res and "Recommended_Actions" in json_res:
                                    parsed_response = json_res
                                    break # Found the complete response
                            except json.JSONDecodeError:
                                st.warning(f"Could not decode JSON from agent response part: {res_str[:100]}...") # Show a snippet
                                continue

                        if parsed_response:
                            st.info(f"**Alerts:**\n{parsed_response.get('Alerts', 'No alerts generated.')}")
                            st.write(f"**Details:**\n{parsed_response.get('Details', 'No details generated.')}")
                            st.success(f"**Recommended Actions:**\n{parsed_response.get('Recommended_Actions', 'No recommended actions generated.')}")
                        else:
                            st.error("The agent did not return a valid structured response.")
                            st.write("Raw agent responses:")
                            for res in agent_responses:
                                st.text(res)

                    except Exception as e:
                        st.error(f"Error processing agent response: {e}")
                        st.write("Raw agent responses:", agent_responses)
                else:
                    st.warning("No response received from the Maintenance Plan Agent.")

                st.subheader("Details of Equipment Scheduled for Maintenance")
                st.dataframe(results["plan_schedule_df"])

                st.subheader("Post-Optimization Schedule Details")
                st.dataframe(result_post["schedule_df"])

            except Exception as e:
                st.error(f"An error occurred during pipeline execution: {e}")
                st.exception(e) # Display full traceback for debugging

    else:
        st.info("Adjust the budget and labor limits in the sidebar and click 'Generate Maintenance Plan' to see the results.")

st.markdown("---")
# st.caption("Developed using Google ADK and Streamlit.")