PROBLEM STATEMENT 

Graphic 1, Picture 

Codebase Repository : SinegalathaB/MRO_ADK: Intelligent workflow automation for Machinery Repair Operations using ADK. Includes multi-agent orchestration for analyzing maintenance data, inventory, logs, and supplier details. 

Demo Video Link: MRO Demo Video · Streamlit 

 

Overview 

The Machine Repair Operations Dashboard is an interactive, intelligent maintenance and supply chain platform developed with Streamlit and powered by Google ADK (Agent Development Kit). The system integrates equipment data, logs, inventory information, and supplier performance into a unified dashboard for real-time monitoring, failure risk detection, maintenance planning, and procurement decision-making. 

 

 

 

Architecture Diagram 

 

Agentic Workflow 
 

The system uses intelligent agents to improve equipment safety and maintenance efficiency. In Stage 1, tools extract risks, parameters, and past issues from SOPs and logs. Stage 2 optimizes maintenance operations under budget/labor constraints , followed by scheduling and executive reporting. Stage 3 handles part replacement by checking inventory, finding suppliers, and recommending the best option. Each agent automates key decisions—risk detection, maintenance planning, and procurement—to reduce failures and optimize resources. 

 

PictureTechnical Architecture of MRO 

Module Breakdown 

🔹 App.py – Main Controller 

Description: 

Serves as the backbone of the application. It handles data ingestion, agent execution, and result serialization. It supports asynchronous agent orchestration and outputs data ready for UI rendering.  

Responsibilities: 

Load CSV and Excel datasets. 

Execute multiple LLM agents using Google ADK. 

Manage session and user context for pipeline consistency. 

Save structured results to disk for UI consumption. 

Shape 

🔹 ResponseProcessing.py – Agent Output Handler 

Description: 

Handles post-processing of agent outputs into consistent, clean, and structured formats like JSON and Pandas DataFrames. 

Responsibilities: 

Cleans malformed agent outputs. 

Converts JSON strings into structured Python data. 

Extracts tables and summaries from multi-agent outputs. 

Prepares final data for UI rendering. 

Shape 

🔹 SummarizationTool.py – Alert Generation System 

Description: 

Defines a collection of alert-generating agents that produce summarized insights for users based on complex operational data. 

Capabilities: 

Generates alerts for high-risk components, stock issues, and supplier performance. 

Executes all summary agents in parallel for efficiency. 

Saves unified outputs for dashboard usage. 

Shape 

🔹 adk_riskAnalysisWorkflow.py – Risk Assessment Engine 

Description: 

Constructs a comprehensive, multi-agent workflow for identifying and analyzing high-risk machinery components using sequential and parallel agents. 

Highlights: 

Identifies and ranks risk based on failure and usage patterns. 

Filters logs and compiles visual insights. 

Evaluates current inventory and suggests mitigations. 

Shape 

🔹 adk_inventoryTool.py – Supplier & Inventory Intelligence 

Description: 

Focuses on identifying low-stock critical parts and evaluates multiple supplier options based on quality, cost, and delivery metrics. 

Key Outcomes: 

Low stock detection among high-risk components. 

Supplier mapping and selection using a weighted scoring system. 

Shape 

🔹 pages/Spare Parts And Inventory.py – Inventory UI Page 

Description: 

Implements a dedicated page in the dashboard to focus on spare parts and inventory health. It complements the main dashboard with additional alert-driven data views. 

Shape 

🔹 pages/Maintenance.py – Maintenance Planning Assistant 

Description: 

This module provides an interactive maintenance planning system. It allows users to input resource constraints (budget and labor) and generates optimized maintenance plans through an LLM-based agent. 

Key Components: 

Google ADK: Powers the LLM agent (maintenance_plan_agent) responsible for generating maintenance plans. 

Streamlit: Renders an intuitive UI for input and displaying recommendations. 

Agent Input Schema: 

analysis_summary: Pre-optimization component-level analytics. 

full_schedule: Post-optimization recommendations (decisions, risk levels). 

post_optimization_summary: Condensed list of components needing immediate attention. 

Agent Output Schema: 

Alerts: Short alerts summarizing key decisions. 

Details: Overview of affected components and actions. 

Recommended_Actions: Concrete, prioritized steps for maintenance execution. 

User Interaction: 

Users specify a budget and daily labor availability. 

Based on constraints, the agent outputs a structured maintenance plan. 

Results are presented clearly in the dashboard for operational execution. 

Shape 

📊 Input Data Summary 

Dataset 

Format 

Purpose 

Line_components_new.csv 

CSV 

Component metadata 

Historical_data.csv 

CSV 

Historical part failure records 

Digital_log.csv 

CSV 

Real-time operational logs 

Inventory.xlsx 

Excel 

Current stock and quantities 

Suppliers.xlsx 

Excel 

Supplier attributes and records 

Shape 

🤖 Agent Ecosystem 

Agent Type 

Agents Included 

Risk Identification 

HighRiskIdentificationAgent, part_usage_agent 

Historical Analysis 

HistoricalAnalysisAgent, FailureSummaryAgent 

Digital log analysis 

LogFilterAgent, FailureSummaryAgent 

Stock Intelligence 

LowStockPartsAgent 

Supplier Evaluation 

SupplierInfoAgent, BestSupplierSelectorAgent 

Summary Generation 

HighRiskPartsSummaryAgent, DigitalLogSummaryAgent, etc. 

Maintenance Planning 

MaintenancePlanAgent  

Shape 

🖼 Visualization & User Interface 

Plots & Charts: Visual summaries of high-risk parts are rendered using saved PNGs or generated dynamically with Matplotlib. 

Dynamic Alert Panel: Alerts update based on user interaction and agent outputs. 

Inventory & Maintenance Pages: Organized via Streamlit’s multi-page support under /pages. 

Shape 

🔁 Application Flow 

Data Load: Application reads raw data from all relevant files. 

Agent Execution: Modular agent workflows assess risks, stock issues, and generate summaries. 

Persistence: All results are saved in pickle files for UI loading. 

User Interface: Users access dashboards to explore analytics, maintenance plans, and part-level data. 

Shape 

✅ Conclusion 

This intelligent dashboard transforms static operational data into a live decision-support system using cutting-edge AI agents, interactive interfaces, and structured pipelines. The addition of maintenance planning makes the solution actionable and resource-aware, empowering maintenance teams to optimize outcomes even under constraints. 

 

Screenshots: 

 

A screenshot of a web page

Description automatically generated, Picture 

 

A screenshot of a web page

Description automatically generated, Picture 

 

A screenshot of a computer

Description automatically generated, Picture 

 

Picture 1, Picture 

 

A screenshot of a computer

Description automatically generated, Picture 

 

A screenshot of a graph

Description automatically generated, Picture 

 

A screenshot of a computer

Description automatically generated, Picture 

 

A screenshot of a computer

Description automatically generated, Picture 

 

A screenshot of a computer

Description automatically generated, Picture 
