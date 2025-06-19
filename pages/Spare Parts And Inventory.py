import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib

from SummarizationTool import run_summary_and_alert_pipeline
import streamlit as st
import pandas as pd
import pickle
import json
import os
from PIL import Image
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from adk_riskAnalysisWorkflow import final_pipeline_agent,code_json_cleaner_agent
from sample_final import analysis_summary, full_schedule, clean_summary
import subprocess
from read_env import *
import asyncio
from ResponseProcessing import preprocessingResponse

df = pd.read_csv("datasets/Line_components_new.csv")
unique_lines = df['line'].dropna().unique().tolist()
print(unique_lines)
unique_lines = unique_lines[1:]
print(unique_lines)


APP_NAME = "machine_repair_ops"
USER_ID = "repair_user_01"
SESSION_ID = "repair_session_01"

async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    runner = Runner(agent=final_pipeline_agent, app_name=APP_NAME, session_service=session_service)

    # Load datasets
    line_components_df = pd.read_csv("datasets/Line_components_new.csv")
    historical_df = pd.read_csv("datasets/Historical_data.csv")
    digital_log_df = pd.read_csv("datasets/Digital_log.csv")
    inventory_df = pd.read_excel("datasets/Inventory.xlsx")
    supplier_df = pd.read_excel("datasets/Suppliers.xlsx")

    components = line_components_df.to_dict(orient='records')
    historical = historical_df.to_dict(orient='records')
    digital = digital_log_df.to_dict(orient='records')
    Inventory = inventory_df.to_dict(orient='records')
    Supplier = supplier_df.to_dict(orient='records')

    for selected_line in unique_lines:
        print("SELECTED LINE", selected_line)

        content = types.Content(
            role="user",
            parts=[
                types.Part(text=f"line_name: {selected_line}"),
                types.Part(text=json.dumps({"LineComponents": components})),
                types.Part(text=json.dumps({"HistoricalData": historical})),
                types.Part(text=json.dumps({"DigitalLogs": digital})),
                types.Part(text=json.dumps({"Inventory": Inventory})),
                types.Part(text=json.dumps({"Supplier": Supplier})),
                types.Part(text=json.dumps({"analysis_summary": analysis_summary})),
                types.Part(text=json.dumps({"full_schedule": full_schedule})),
                types.Part(text=json.dumps({"summary": clean_summary}))
            ]
        )

        responses = [None] * 11
        AGENT_INDEX_MAP = {
            "HighRiskIdentificationAgent": 0,
            "CodeJsonCleanerAgent": 2,
            "LogFilterAgent": 3,
            "FailureSummaryAgent": 4,
            "LowStockPartsAgent": 5,
            "SupplierInfoAgent": 6,
            "BestSupplierSelectorAgent": 7,
            "HistoricalAnalysisAgent": 1,
            "MaintenancePlanAgent": 8,
            "PostOptimizationAgent": 9,
            "part_usage_agent": 10
        }

        async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
            agent_name = getattr(event, "author", "UnknownAgent")
            response_text = ""
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text + "\n"
            if agent_name in AGENT_INDEX_MAP:
                responses[AGENT_INDEX_MAP[agent_name]] = response_text.strip()

        safe_line_name = selected_line.replace(" ", "_")
        filename = f"responses_{safe_line_name}.pkl"

        with open(filename, "wb") as f:
            pickle.dump(responses, f)

        # Call your preprocessing function
        processed_response_pickle_file_name = await preprocessingResponse(filename)
        final_ui_pickle_file_path = await run_summary_and_alert_pipeline(processed_response_pickle_file_name)
        return final_ui_pickle_file_path

# --- Page Configuration ---
# st.set_page_config(layout="wide")

# --- Custom CSS for Theming ---
st.markdown("""
<style>
    /* Core App Colors */
    .stApp {
        background-color: #F0F2F6; /* Light Gray for the main app background */
    }

    /* Main Title Style */
    .st-emotion-cache-183lzff {
        color: #2c3e50; /* Darker shade for title */
        font-weight: bold;
    }

    /* Sidebar Styling */
    .st-emotion-cache-16txtl3 {
        background-color: #708090; /* Slate Gray */
        padding: 1.5rem;
    }

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] .st-emotion-cache-1b0udgb {
        color: #FFFFFF; /* White text for sidebar headers */
    }
    
    /* Expander styling in the sidebar */
    .st-emotion-cache-p5msec {
        background-color: #4682B4; /* Steel Blue */
        border-radius: 0.5rem;
    }

    .st-emotion-cache-p5msec summary {
        color: #FFFFFF;
        font-weight: bold;
    }
    
    /* CTA Button Styling */
    .stButton>button {
        background-color: #FF8C00; /* Industrial Orange */
        color: #FFFFFF; /* White text */
        border: none;
        border-radius: 0.3rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #E57C00; /* Slightly darker orange on hover */
    }

    /* Headers in the main panel */
    h1, h2, h3 {
        color: #4682B4; /* Steel Blue for main panel headers */
    }
    
    /* Subheader Styling */
    .st-emotion-cache-1xarl3l {
        color: #2c3e50; /* Dark blue-gray for subheaders */
    }

    /* Markdown and Text Styling */
    .stMarkdown {
        color: #34495e; /* Dark gray for text */
    }
    
    /* DataFrame Styling */
    .stDataFrame {
        border: 2px solid #4682B4; /* Steel Blue border for dataframes */
        border-radius: 0.5rem;
    }
            
    .alerts-header {
    font-size: 1.5rem;        /* Big text */
    font-weight: 700;       /* Extra bold */
    color: black !important;
    margin-bottom: 1rem;
}

</style>
""", unsafe_allow_html=True)


st.title("Machine Repair Operations")


if 'final_filename' not in st.session_state:
    with st.spinner("Running pipeline... please wait."):
        # In a real scenario, main() would be defined and run.
        # For this example, we'll simulate it.
        filename = asyncio.run(main())
        # filename = "final_ui_processed_responses_Sanitization_Line_2.pkl" # Simulated filename
        st.session_state.final_filename = filename
else:
    filename = st.session_state.final_filename


# Set a non-interactive backend for Matplotlib
matplotlib.use('Agg')

# --- Data Loading and Processing ---
processed_dict = {}
corresponding_sanitation_line_name = "Default_Sanitation_Line"

try:
    corresponding_sanitation_line_name = filename.replace("final_ui_processed_responses_", "").replace(".pkl", "")

    with open(filename, "rb") as f:
        responses = pickle.load(f)

    for item in responses:
        if len(item) >= 5:
            key = item[0]
            value = [item[1], item[3], item[4]] # df_details, summary_text, alert_title
            processed_dict[key] = value
        else:
            print(f"Skipping item due to insufficient length: {item}")

except (FileNotFoundError, pickle.UnpicklingError) as e:
    st.error(f"An error occurred: {e}. Could not load or create the data file.")
    st.stop()

# --- UPDATED: Define the specific order for the alerts ---
key_order = [
    "HighRiskPartsSummaryAgent",
    "HighRiskPartsThresholdSummaryAgent",
    "digital_log_summary_agent",
    "LowStockSummaryAgent",
    "SupplierPerformanceSummaryAgent",
    "BestSupplierSummaryAgent"
]

# --- Streamlit App UI ---

# UPDATED: Set the default selected key based on the specified order
if 'selected_key' not in st.session_state:
    # Find the first key from your desired order that exists in the processed data
    default_key = next((key for key in key_order if key in processed_dict), None)
    
    # If no key from the order list is found, fall back to the first key in the dictionary
    if default_key is None and processed_dict:
        default_key = list(processed_dict.keys())[0]
        
    st.session_state.selected_key = default_key
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] h1 {
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# UPDATED: Iterate through the ordered list to display buttons
with st.sidebar:
    st.markdown('<div class="alerts-header">Alerts</div>', unsafe_allow_html=True)
    with st.expander(corresponding_sanitation_line_name, expanded=True):
        # Loop through the predefined key_order list
        for key in key_order:
            # Check if the key exists in your data before creating a button
            if key in processed_dict:
                value = processed_dict[key]
                alert_message = value[2]  # This is the alert_title
                if st.button(alert_message, key=key, use_container_width=True):
                    st.session_state.selected_key = key

# --- Main Panel for Details ---
selected_key = st.session_state.selected_key

if selected_key is None or not processed_dict:
    st.info("No data available to display.")
else:
    selected_data = processed_dict[selected_key]
    df_details, summary_text, alert_title = selected_data
    
    st.header(f"{alert_title}")
    st.markdown("---")
    
    st.subheader("Summary")
    st.markdown(f'<div style="background-color: #eaf2f8; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #4682B4;">{summary_text}</div>', unsafe_allow_html=True)
    
    st.subheader("Details")
    if isinstance(df_details, pd.DataFrame):
        st.dataframe(df_details)
    else:
        st.write("Details data is not in a valid DataFrame format.")

    # --- Visualization Section (Conditional) ---
    if selected_key == "HighRiskPartsThresholdSummaryAgent":
        st.markdown("---")
        st.subheader("📊 Visualizations")

        high_risk_parts_df = processed_dict.get('HighRiskPartsSummaryAgent', [pd.DataFrame()])[0]

        if high_risk_parts_df.empty or "part" not in high_risk_parts_df.columns:
            st.warning("High-risk parts list not found. Cannot display visualizations.")
        else:
            plot_dir = "plots"
            try:
                if not os.path.isdir(plot_dir):
                    raise FileNotFoundError("The 'plots' directory was not found.")

                for part in high_risk_parts_df["part"]:
                    st.markdown(f"### 📌 {part}")
                    sanitized_part = part.replace(" ", "_")
                    sanitized_line = corresponding_sanitation_line_name.replace(" ", "_")
                    
                    matching_files = [f for f in os.listdir(plot_dir)
                                      if f.startswith(f"{sanitized_part}_{sanitized_line}") and f.endswith(".png")]

                    if not matching_files:
                        st.info(f"No plots found in the '{plot_dir}/' directory for {part}")
                    else:
                        for file in matching_files:
                            image_path = os.path.join(plot_dir, file)
                            image = Image.open(image_path)
                            st.image(image, caption=file.replace("_", " ").replace(".png", ""), use_container_width=True)

            except (FileNotFoundError, ImportError):
                st.info(f"Could not find local `plots` directory. Displaying simulated visualizations instead.")
                
                for part in high_risk_parts_df["part"]:
                    st.markdown(f"### 📌 {part}")
                    
                    fig, ax = plt.subplots(facecolor='#F0F2F6') # Match app background
                    x = np.linspace(0, 10, 100)
                    y_noise = np.random.randn(100) * 0.5
                    y_base = 20 if "Seal" in part else 35
                    y = y_base + np.sin(x) + y_noise
                    
                    ax.plot(x, y, label='Simulated Sensor Reading', color='#4682B4', linewidth=2)
                    ax.axhline(y=y_base + 1.5, color='#FF8C00', linestyle='--', label='Upper Threshold')
                    ax.axhline(y=y_base - 1.5, color='#FF8C00', linestyle='--', label='Lower Threshold')
                    
                    ax.set_title(f'Parameter Trend for {part}', color='#2c3e50')
                    ax.set_xlabel('Time (Hours)', color='#2c3e50')
                    ax.set_ylabel('Vibration/Pressure Reading', color='#2c3e50')
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.legend()
                    ax.tick_params(colors='#2c3e50')
                    
                    simulated_filename = f"{part.replace(' ', '_')}_{corresponding_sanitation_line_name}_Trend.png"
                    st.pyplot(fig)
                    st.caption(f"Simulated plot for: {simulated_filename}")
                    plt.close(fig)

