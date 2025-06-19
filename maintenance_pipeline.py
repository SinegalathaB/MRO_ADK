# maintenance_pipeline.py

import pandas as pd
import numpy as np
from pulp import (
    LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus
)

# -------------------------------
# Class: MaintenanceOptimizer
# -------------------------------

class MaintenanceOptimizer:
    def __init__(self, alpha=0.0, include_manpower_constraint=False, manpower_limit=None):
        """
        Initializes the maintenance optimizer.
        """
        self.alpha = alpha
        self.include_manpower_constraint = include_manpower_constraint
        self.manpower_limit = manpower_limit

    def optimize_schedule(self, risk_df: pd.DataFrame, budget: float,
                          cost_col: str = "cost",
                          fail_prob_col: str = "failure_probability",
                          risk_impact_col: str = "risk_impact",
                          labor_col: str = "labor_hours") -> pd.DataFrame:
        """
        Runs the maintenance optimization model using linear programming.
        """
        if cost_col not in risk_df.columns or fail_prob_col not in risk_df.columns:
            raise ValueError(f"Missing required columns: {cost_col}, {fail_prob_col}.")

        if risk_impact_col not in risk_df.columns:
            risk_df[risk_impact_col] = 1.0

        df = risk_df.copy()
        problem = LpProblem("MaintenanceOptimization", LpMinimize)

        # Binary decision variable for each equipment
        df["var"] = [LpVariable(f"x_{eid}", cat=LpBinary) for eid in df["equipment_id"]]

        # Objective: Minimize total expected risk
        objective_terms = []
        for _, row in df.iterrows():
            x_var = row["var"]
            p_fail = row[fail_prob_col]
            imp = row[risk_impact_col]

            risk_if_not = p_fail * imp
            risk_if_maint = self.alpha * p_fail * imp

            objective_terms.append(risk_if_not * (1 - x_var) + risk_if_maint * x_var)

        problem += lpSum(objective_terms), "TotalRisk"

        # Budget constraint
        problem += lpSum(row[cost_col] * row["var"] for _, row in df.iterrows()) <= budget

        # Optional manpower constraint
        if self.include_manpower_constraint and labor_col in df.columns and self.manpower_limit is not None:
            problem += lpSum(row[labor_col] * row["var"] for _, row in df.iterrows()) <= self.manpower_limit

        # Solve the LP
        problem.solve()

        # Extract results
        df["maintain"] = [int(var.varValue) for var in df["var"]]
        df["decision"] = df["maintain"].map({1: "Maintain", 0: "Skip"})
        df["optimized_risk"] = df.apply(
            lambda row: self.alpha * row[fail_prob_col] * row[risk_impact_col]
            if row["maintain"] == 1
            else row[fail_prob_col] * row[risk_impact_col], axis=1
        )

        # Assign maintenance order
        df["maintenance_order"] = None
        maintained_sorted = df[df["maintain"] == 1].sort_values(by="optimized_risk").copy()
        maintained_sorted["maintenance_order"] = range(1, len(maintained_sorted) + 1)
        df.update(maintained_sorted)

        df.drop(columns=["var"], inplace=True)
        df["solution_status"] = LpStatus[problem.status]
        df["total_optimized_risk"] = df["optimized_risk"].sum()

        return df

# -------------------------------
# Function: local_analysis
# -------------------------------

def local_analysis(df: pd.DataFrame) -> dict:
    """
    Performs local analysis on failure probabilities and risks.
    """
    return {
        "total_equipment": len(df),
        "avg_failure_probability": float(df["failure_probability"].mean() if "failure_probability" in df.columns else 0),
        "high_risk_count": int((df["failure_probability"] > 0.7).sum() if "failure_probability" in df.columns else 0),
        "total_unoptimized_risk": float((df["failure_probability"] * df.get("risk_impact", 1.0)).sum()),
    }

# -------------------------------
# Function: ingest_data
# -------------------------------

def ingest_data(file_path: str) -> pd.DataFrame:
    """
    Loads maintenance data from a CSV file.
    """
    return pd.read_csv(file_path)

# -------------------------------
# Function: local_optimization
# -------------------------------

def local_optimization(df: pd.DataFrame, budget: float) -> pd.DataFrame:
    """
    Runs the optimization algorithm on the ingested data.
    """
    optimizer = MaintenanceOptimizer(alpha=0.0, include_manpower_constraint=True, manpower_limit=5000)
    return optimizer.optimize_schedule(
        risk_df=df,
        budget=budget,
        cost_col="cost",
        fail_prob_col="failure_probability",
        risk_impact_col="risk_impact",
        labor_col="labor_hours"
    )

# -------------------------------
# Function: run_pipeline
# -------------------------------

def run_pipeline(file_path: str, budget: float) -> dict:
    """
    Orchestrates the ingestion, analysis, and optimization pipeline.
    """
    df = ingest_data(file_path)
    analysis = local_analysis(df)
    schedule_df = local_optimization(df, budget)

    maintained_df = schedule_df[schedule_df["maintain"] == 1].sort_values(by="maintenance_order")

    plan_summary = {
        "maintenance_schedule": maintained_df.to_dict(orient="records"),
        "optimized_risk": float(schedule_df["total_optimized_risk"].iloc[0]) if len(schedule_df) else 0.0,
        "solution_status": schedule_df["solution_status"].iloc[0] if len(schedule_df) else "Unknown",
    }

    return {
        "analysis_summary": analysis,
        "plan_summary": plan_summary,
        "plan_schedule_df": maintained_df,
        "full_schedule": schedule_df.to_dict(orient="records")
    }

# -------------------------------
# Function: post_optimization_schedule
# -------------------------------

def post_optimization_schedule(df: pd.DataFrame, labor_available_per_day: dict) -> dict:
    """
    Assigns optimized maintenance schedule based on labor constraints and utilization.
    """
    df = df.copy()

    # Simulate utilization if missing
    if "utilization_pct" not in df.columns:
        df["utilization_pct"] = np.random.uniform(0.6, 0.9, len(df)).round(2)

    df["allowed_days"] = df["utilization_pct"].apply(
        lambda u: ["DAY+1", "DAY+2", "DAY+3", "DAY+4"] if u < 0.7 else ["DAY+2", "DAY+3"]
    )

    df["downtime_hours"] = df.get("downtime_hours", df["labor_hours"] * 1.5)
    df["production_per_hour"] = df.get("production_per_hour", np.random.uniform(80, 150, len(df)).round(2))
    df["unit_price"] = df.get("unit_price", np.random.uniform(9.0, 15.0, len(df)).round(2))

    df["scheduled_day"] = None
    df["expected_revenue_loss"] = 0.0
    labor_left = labor_available_per_day.copy()

    maintained_df = df[df["maintain"] == 1].sort_values(by="maintenance_order")

    for idx, row in maintained_df.iterrows():
        assigned = False
        for day in row["allowed_days"]:
            if labor_left.get(day, 0) >= row["labor_hours"]:
                labor_left[day] -= row["labor_hours"]
                df.at[idx, "scheduled_day"] = day
                df.at[idx, "expected_revenue_loss"] = row["downtime_hours"] * row["production_per_hour"] * row["unit_price"]
                assigned = True
                break
        if not assigned:
            df.at[idx, "scheduled_day"] = "Unassigned"
            df.at[idx, "expected_revenue_loss"] = row["downtime_hours"] * row["production_per_hour"] * row["unit_price"]

    summary = {
        "total_revenue_loss": df["expected_revenue_loss"].sum(),
        "total_maintenance_cost": (df["cost"] * df["maintain"]).sum(),
        "total_optimized_risk": df["optimized_risk"].iloc[0] if "optimized_risk" in df.columns else None,
        "solution_status": df["solution_status"].iloc[0] if "solution_status" in df.columns else "Unknown",
        "labor_remaining_per_day": labor_left,
        "maintenance_count": int(df["maintain"].sum()),
        "scheduled_maintenance_details": df[[
            "equipment_id", "line", "component", "maintain", "scheduled_day", "labor_hours",
            "downtime_hours", "production_per_hour", "unit_price",
            "expected_revenue_loss", "optimized_risk"
        ]].to_dict(orient="records")
    }

    return {
        "schedule_df": df,
        "summary": summary
    }
