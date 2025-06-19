import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def historical_performance_analysis(high_risk_parts, file_path="datasets/Historical_data.csv"):
    """
    Analyzes historical performance data for high-risk parts and generates plots.
 
    Args:
        high_risk_parts (list): A list of high-risk parts from the previous tool.
        file_path (str): The path to the Historical_data.csv file.
 
    Returns:
        dict: A dictionary containing the paths to the generated plots for each part.
    """
    try:
        df = pd.read_csv(file_path)
        print("Historical Data")
        # print(df)
        results = {}
        for part_data in high_risk_parts:
            part = part_data['part']
            line = part_data['line']
            part_df = df[(df['Line'] == line) & (df['Part'] == part)]
            print("Part Data")
            print(part_df)
            if part_df.empty:
                print(f"No data found for part '{part}' on line '{line}'. Skipping.")
                continue
 
            parameters = part_df['Parameter'].unique()
            num_params = len(parameters)
            fig, axes = plt.subplots(num_params, 1, figsize=(12, 6 * num_params))
            fig.suptitle(f"Historical Performance for Part '{part}' on Line '{line}'")
 
            plot_paths = []
            for i, param in enumerate(parameters):
                param_df = part_df[part_df['Parameter'] == param].sort_values(by='Date')
                if param_df.empty:
                    print(f"No data found for parameter '{param}' for part '{part}' on line '{line}'. Skipping.")
                    continue
 
                ax = axes[i] if num_params > 1 else axes
                ax.plot(param_df['Value'], param_df['Value'], label='Actual Value', marker='o')
                ax.axhline(y=param_df['Expected_value_min'].iloc[0], color='r', linestyle='--', label='Expected Min')
                ax.axhline(y=param_df['Expected_value_max'].iloc[0], color='g', linestyle='--', label='Expected Max')
                ax.set_xlabel('Date')
                ax.set_ylabel('Value')
                ax.set_title(f'Parameter: {param}')
                ax.legend()
                ax.grid(True)
                plt.xticks(rotation=45)
                plt.show()
 
            plt.tight_layout(rect=[0, 0.03, 1, 0.97])
            plot_filename = f"{part.replace(' ', '_')}_{line.replace(' ', '_')}_historical_performance.png"
            plot_path = os.path.join("plots", plot_filename)
            os.makedirs("plots", exist_ok=True)
            plt.savefig(plot_path)
            plt.close(fig)
            plot_paths.append(plot_path)
 
            results[part] = plot_paths
 
        return results
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}