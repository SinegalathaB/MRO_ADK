
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
</head>
<body>

  <h1>🛠️ Intelligent Workflow Automation for Machinery Repair Operations using Agentic AI</h1>
  <blockquote>Transforming static machinery data into dynamic, autonomous maintenance decisions using multi-agent orchestration with Google ADK.</blockquote>

  <h2>🚩 Problem Statement</h2>
  <p>
    Machine maintenance in industrial environments remains reactive, inefficient, and data-disconnected. Failures are often detected post-incident,
    spare part availability is unclear, and supplier evaluation is mostly manual. Training schedules are static and not tailored to real-time needs.
  </p>

  <h2>📦 Codebase</h2>
  <p>
    <strong>Repository:</strong> <a href="https://github.com/SinegalathaB/MRO_ADK">SinegalathaB/MRO_ADK</a><br>
    An AI-powered platform using intelligent agents to automate risk detection, maintenance planning, and inventory optimization in real-time.
  </p>

<h2>🎥 Demo</h2>
[MRO_Demo_Video.webm](https://github.com/user-attachments/assets/3c7fd676-61d8-4a53-abad-78a639fa861b)


  <h2>🧠 Overview</h2>
  <p>
    The <strong>Machine Repair Operations Dashboard</strong> is a Streamlit-based platform powered by <strong>Google ADK</strong> (Agent Development Kit). 
    It integrates machine logs, SOPs, inventory levels, and supplier data to:
  </p>
  <ul>
    <li>Detect risks and failures</li>
    <li>Optimize maintenance planning</li>
    <li>Recommend procurement strategies</li>
    <li>Enhance decision-making via AI agents</li>
  </ul>

  <h2>📐 Architecture Diagram</h2>
![MRO_TECHARCH](https://github.com/user-attachments/assets/a8742f04-b408-4121-9d8c-4598164d4504)


  <h2>⚙️ Agentic Workflow</h2>
  <p>The platform uses a <strong>multi-stage, agent-driven workflow</strong>:</p>
  <ol>
    <li><strong>Stage 1 – Risk Extraction:</strong> Analyze SOPs, logs, and historical records for risks and patterns.</li>
    <li><strong>Stage 2 – Maintenance Planning:</strong> Schedule tasks based on workforce/budget constraints; generate executive reports.</li>
    <li><strong>Stage 3 – Spare Part Management:</strong> Evaluate inventory and suppliers; recommend optimal procurement.</li>
  </ol>
  <p>Each agent performs a key task autonomously and contributes to a seamless, intelligent system.</p>

  <h2>🧩 Module Breakdown</h2>
  <h3>🔹 App.py – Main Controller</h3>
  <ul>
    <li>Loads data files (CSV, Excel)</li>
    <li>Orchestrates multi-agent execution via Google ADK</li>
    <li>Saves structured results for dashboard rendering</li>
  </ul>

  <h3>🔹 ResponseProcessing.py – Agent Output Handler</h3>
  <ul>
    <li>Cleans agent outputs</li>
    <li>Converts results into structured formats (JSON, DataFrame)</li>
  </ul>

  <h3>🔹 SummarizationTool.py – Alert Generator</h3>
  <ul>
    <li>Runs summary agents in parallel</li>
    <li>Produces risk, stock, and supplier alerts</li>
  </ul>

  <h3>🔹 adk_riskAnalysisWorkflow.py – Risk Analysis Engine</h3>
  <ul>
    <li>Identifies risk levels</li>
    <li>Filters and visualizes log data</li>
  </ul>

  <h3>🔹 adk_inventoryTool.py – Inventory & Supplier Analyzer</h3>
  <ul>
    <li>Detects low stock for high-risk parts</li>
    <li>Selects best supplier using weighted scoring</li>
  </ul>

  <h3>🔹 pages/Spare Parts And Inventory.py – Inventory UI</h3>
  <ul>
    <li>Dedicated inventory visualization with agent alerts</li>
  </ul>

  <h3>🔹 pages/Maintenance.py – Maintenance Planning</h3>
  <ul>
    <li>User inputs budget and labor availability</li>
    <li>LLM agent generates optimized maintenance plan</li>
    <li>Recommendations and alerts rendered in the UI</li>
  </ul>

  <h2>📊 Input Data Summary</h2>
  <table border="1">
    <tr><th>Dataset</th><th>Format</th><th>Purpose</th></tr>
    <tr><td>Line_components.csv</td><td>CSV</td><td>Component metadata</td></tr>
    <tr><td>Historical_data.csv</td><td>CSV</td><td>Historical failure records</td></tr>
    <tr><td>Digital_log.csv</td><td>CSV</td><td>Live operational logs</td></tr>
    <tr><td>Inventory.xlsx</td><td>Excel</td><td>Current stock levels</td></tr>
    <tr><td>Suppliers.xlsx</td><td>Excel</td><td>Supplier details & metrics</td></tr>
  </table>

  <h2>🤖 Agent Ecosystem</h2>
  <table border="1">
    <tr><th>Agent Type</th><th>Agents Included</th></tr>
    <tr><td>Risk Identification</td><td>HighRiskIdentificationAgent, part_usage_agent</td></tr>
    <tr><td>Historical Analysis</td><td>HistoricalAnalysisAgent, FailureSummaryAgent</td></tr>
    <tr><td>Log Analysis</td><td>LogFilterAgent, FailureSummaryAgent</td></tr>
    <tr><td>Stock Intelligence</td><td>LowStockPartsAgent</td></tr>
    <tr><td>Supplier Evaluation</td><td>SupplierInfoAgent, BestSupplierSelectorAgent</td></tr>
    <tr><td>Summary Generation</td><td>HighRiskPartsSummaryAgent, DigitalLogSummaryAgent</td></tr>
    <tr><td>Maintenance Planning</td><td>MaintenancePlanAgent</td></tr>
  </table>

  <h2>🖥 Visualization & UI</h2>
  <ul>
    <li><strong>Dynamic Alert Panel:</strong> Updates in real-time based on agent outputs</li>
    <li><strong>Plots & Graphs:</strong> Created using Matplotlib or static PNGs</li>
    <li><strong>Multi-page Navigation:</strong> Inventory and maintenance pages under <code>/pages</code></li>
  </ul>

  <h2>🔁 Application Flow</h2>
  <ol>
    <li>Load CSV/Excel data files</li>
    <li>Run agent pipelines to detect risks, optimize schedules, evaluate inventory</li>
    <li>Save results as pickle files for UI rendering</li>
    <li>Display results in an interactive Streamlit dashboard</li>
  </ol>

  <h2>✅ Conclusion</h2>
  <p>
    This platform brings <strong>intelligence and autonomy</strong> to traditional machine repair operations. 
    By combining <strong>multi-agent orchestration</strong> with real-time data and an intuitive dashboard, 
    the system helps teams make confident, data-backed decisions—even under constraints.
  </p>

  <h2>🖼 Screenshots</h2>

![image](https://github.com/user-attachments/assets/887ea1a9-de79-43ac-9add-2d009344f40c)
![image](https://github.com/user-attachments/assets/e2867aa3-615d-497f-9908-9a531b4535f5)
![image](https://github.com/user-attachments/assets/9aee2a2f-58db-48d9-a3f3-5c5dbf3840c5)
![image](https://github.com/user-attachments/assets/4614a6db-5d48-4a75-ad79-af9c7b3cc562)
![image](https://github.com/user-attachments/assets/930b439c-a26e-4330-a66c-66fede722f67)
![image](https://github.com/user-attachments/assets/492b4257-7824-4e8a-976b-155c3852067e)
![image](https://github.com/user-attachments/assets/f8b2afbf-9075-4fec-9a29-fa1e71545f6b)
![image](https://github.com/user-attachments/assets/0fdf7bb8-635c-45c1-84ce-391ad40ff6e2)
![image](https://github.com/user-attachments/assets/9bc2e8fe-02e1-4a32-8384-fbb767fafcd7)
![image](https://github.com/user-attachments/assets/0a707ba0-1b80-4056-889b-5ebfe50fcf05)


</body>
</html>
