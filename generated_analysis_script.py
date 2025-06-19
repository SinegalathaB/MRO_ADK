import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

def analyze_historical_data(high_risk_parts, data_file):
    """
    Analyzes historical data for specified parts and generates line plots for each parameter.

    Args:
        high_risk_parts (list): A list of dictionaries, where each dictionary contains 'part' and 'line' keys.
        data_file (str): The path to the CSV file containing the historical data.

    Returns:
        dict: A dictionary mapping each 'part_line_parameter' identifier to its saved image file path.
    """
    # Create plots directory if it doesn't exist, and clear it if it does
    plots_dir = "plots/"
    if os.path.exists(plots_dir):
        shutil.rmtree(plots_dir)
    os.makedirs(plots_dir, exist_ok=True)

    # Load the historical data
    try:
        df = pd.read_csv(data_file)
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_file}")
        return {}
    except pd.errors.EmptyDataError:
        print(f"Error: Data file is empty at {data_file}")
        return {}

    # Dictionary to store the file paths of the generated plots
    plot_paths = {}

    for part_info in high_risk_parts:
        part_name = part_info["part"]
        #line_name = part_info["line"]

        # Filter the historical data to match the current part and line
        #filtered_df = df[(df["Part"] == part_name) & (df["Line"] == line_name)]
        filtered_df = df[df["Part"] == part_name]
        if filtered_df.empty:
            print(f"No data found for part: {part_name}")
            continue

        # Iterate through each unique Parameter
        for parameter in filtered_df["Parameter"].unique():
            parameter_df = filtered_df[filtered_df["Parameter"] == parameter].copy()
            if parameter_df.empty:
                print(f"No data found for parameter: {parameter} of part: {part_name} and line: {line_name}")
                continue

            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot the data
            ax.plot(parameter_df["Cycle"], parameter_df["Value"], marker='o', linestyle='-', label=parameter)

            # Add horizontal lines for expected value range
            if not parameter_df["Expected_value_min"].isnull().all() and not parameter_df["Expected_value_max"].isnull().all():
                min_val = parameter_df["Expected_value_min"].iloc[0]
                max_val = parameter_df["Expected_value_max"]