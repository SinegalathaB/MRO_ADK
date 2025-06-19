import pandas as pd
import pickle
import subprocess
import json
import asyncio
from google.adk.runners import Runner
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from adk_riskAnalysisWorkflow import code_json_cleaner_agent
from plotexception import historical_performance_analysis
from google.genai import types
from read_env import *

# Constants
GEMINI_MODEL_2_FLASH = "gemini-2.0-flash"
APP_NAME = "machine_repair_ops"
USER_ID = "repair_user_01"
SESSION_ID = "repair_session_01"
# Global session service

# Agent definition
json_cleaner_agent = LlmAgent(
    name="CodeJsonCleanerAgent",
    model=GEMINI_MODEL_2_FLASH,
    instruction="""
You will be given a text input that looks like JSON but may contain formatting issues, such as:
- trailing commas,
- missing quotes around keys or string values,
- single quotes instead of double quotes,
- incorrect brackets or braces.

Your task is to:
✔ Clean and correct the input so that it becomes a **valid JSON string**.
✔ Ensure that the output can be parsed successfully using `json.loads()` in Python.
✔ Do not perform any other transformation — just return the corrected JSON as text.
"""
)

# JSON cleaning runner
async def json_cleaner_runner(json_text):
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=json_cleaner_agent, app_name=APP_NAME, session_service=session_service)
    user_content = types.Content(role='user', parts=[types.Part(text=json_text)])
    response_text = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=user_content):
        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text + "\n"
    
    return response_text.strip()

async def code_json_cleaner_runner(json_text):
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=code_json_cleaner_agent, app_name=APP_NAME, session_service=session_service)
    user_content = types.Content(role='user', parts=[types.Part(text=json.dumps(json_text))])
    response_text = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=user_content):
        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text + "\n"
    
    return response_text.strip()

# Helper to parse potentially dirty JSON
async def safe_json_parse(text, index=None):
    try:
        return json.loads(text)
    except:
        print(f"❌ JSONDecodeError at index {index}, running cleaner agent...")
        cleaned = await json_cleaner_runner(text)
        cleaned = cleaned.strip("```json\n").strip("```")
        return json.loads(cleaned)
    
async def safe_code_json_parse(text, index=None):
    try:
        return json.loads(text)
    except:
        print(f"❌ JSONDecodeError at index {index}, running cleaner agent...")
        cleaned = await code_json_cleaner_runner(text)
        cleaned = cleaned.strip("```json\n").strip("```")
        try:
            return json.loads(cleaned)
        except Exception as e:
            print(f"Still failed to decode JSON after cleaning: {e}")

# Processors
async def process_high_risk_parts(responses):
    data = responses[0].strip("```json\n").strip("```")
    part_usage = responses[10].strip("```json\n").strip("```")

    high_risk_parts = pd.DataFrame(await safe_json_parse(data, index=0))
    part_usage_info = pd.DataFrame(await safe_json_parse(part_usage, index=10))

    high_risk_parts['part_usage'] = part_usage_info['part_usage']
    print("HIGH RISK PARTS")
    print(high_risk_parts, "\n")
    return high_risk_parts

async def process_plot_code(high_risk_parts_data, responses):
    data = responses[2].strip("```json\n").strip("```")
    print("Data***",data)
    
    try:
        data = json.loads(data)
        python_code = data["code"].strip("```python\n").strip("```")
        print(python_code)
        script_path = "generated_analysis_script.py"
        with open(script_path, "w") as f:
            f.write(python_code)
        subprocess.run(["python", script_path], check=True)
    except:
        try:
            plot_data = await safe_code_json_parse(data, index=2)
            print(plot_data)
            python_code = plot_data["code"].strip("```python\n").strip("```")
            
            script_path = "generated_analysis_script.py"
            with open(script_path, "w") as f:
                f.write(python_code)
            
            subprocess.run(["python", script_path], check=True)
        except:
            print("Final exception called")
            historical_performance_analysis(high_risk_parts_data)

    print("🧠 Cleaned Python Code:")
    print(python_code, "\n")
    return python_code

async def process_digital_log(responses):
    data = responses[4].strip("```json\n").strip("```")
    digital_log = pd.DataFrame(await safe_json_parse(data, index=4))
    digital_log.drop(columns=['log_records'], inplace=True)
    print("DIGITAL LOG DETAILS")
    print(digital_log, "\n")
    return digital_log

async def process_low_stock_parts(responses):
    data = responses[5].strip("```json\n").strip("```")
    low_stock = pd.DataFrame(await safe_json_parse(data, index=5))
    print("LOW STOCK PARTS")
    print(low_stock, "\n")
    return low_stock

async def process_supplier_info(responses):
    data = responses[6].strip("```json\n").strip("```")
    supplier_info = await safe_json_parse(data, index=6)
    print(supplier_info)
    merged_data = []
    for part_entries in supplier_info.values():
        merged_data.extend(part_entries)
    merged_supplier_info = pd.DataFrame(merged_data)
    print("SUPPLIER INFO")
    print(merged_supplier_info, "\n")
    return merged_supplier_info

async def process_best_supplier(responses):
    # Clean the JSON block
    data = responses[7].strip("```json\n").strip("```")
    print("BEST SUPPLIER (Raw JSON)")
    print(data, "\n")

    # Parse the JSON content
    parsed = await safe_json_parse(data, index=7)

    # Convert each inner dictionary to a list and then to a DataFrame
    part_list = []
    for part_name, part_info in parsed.items():
        part_list.append(part_info)

    # Now create a proper DataFrame
    best_supplier_info = pd.DataFrame(part_list)

    print("✅ BEST SUPPLIER DataFrame")
    print(best_supplier_info)

    return best_supplier_info

# Orchestrator
async def preprocessingResponse(filename):
    with open(filename, "rb") as f:
        responses = pickle.load(f)

    high_risk_parts_data = await process_high_risk_parts(responses)
    plot_code = await process_plot_code(high_risk_parts_data,responses)  # not returned if not needed
    digital_log = await process_digital_log(responses)
    low_stock_parts = await process_low_stock_parts(responses)
    supplier_info = await process_supplier_info(responses)
    best_supplier = await process_best_supplier(responses)
    processed_response = {
        "high_risk_parts_data": high_risk_parts_data,
        "digital_log": digital_log,
        "low_stock_parts": low_stock_parts,
        "supplier_info": supplier_info,
        "best_supplier": best_supplier
    }
    processed_filename = f"processed_{filename}"
    with open(processed_filename, "wb") as f:
            pickle.dump(processed_response, f)
    return processed_filename

# # # Run everything
# if __name__ == "__main__":
#     print(asyncio.run(preprocessingResponse("responses.pkl")))
