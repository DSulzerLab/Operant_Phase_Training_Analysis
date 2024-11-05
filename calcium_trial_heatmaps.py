import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Define the main directory containing the phase subfolders
data_dir = Path('trials')
phase_folders = ['phase 1', 'phase 2', 'phase 3']  # List of phase subfolders

# Loop through each phase folder
for phase in phase_folders:
    # Define specific paths for data input and output for the current phase
    input_dir = data_dir / phase
    save_dir = data_dir / f'plots {phase}'

    # Create the save directory if it doesn't exist
    save_dir.mkdir(parents=True, exist_ok=True)

    # Loop through all .xlsx files in the current phase folder
    for file_path in input_dir.glob('*.xlsx'):
        # Load the Excel file
        data = pd.read_excel(file_path)
        
        # Define time and cut the data to 1220 samples
        time = data['Time'][:1220]  # x-axis (first column)
        traces = data.iloc[:1220, 1:]  # all other columns

        # Adjust x-axis tick labels (from -2 to 8 seconds with 2-second intervals)
        x_ticks = np.linspace(-2, 8, 6)  # x-axis label points [-2, 0, 2, 4, 6, 8]
        x_tick_positions = np.linspace(0, 1220, 6)  # positions for these labels (based on sample size)

        # Plot 1: Heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(traces.T, cmap='cividis', cbar_kws={'label': 'Signal Intensity'}, yticklabels=False)
        plt.xticks(ticks=x_tick_positions, labels=x_ticks, rotation=45)
        # Add a red dotted line at the 0-second mark
        plt.axvline(x=244, color='#D55E00', linestyle='--', label='cue starts')
        plt.xlabel('Time (s)')
        plt.title(f'Heatmap of Traces - {file_path.stem}')
        plt.tight_layout()
        plt.savefig(save_dir / f'heatmap_{file_path.stem}.png')
        plt.close()

        # Plot 2: Normalized Heatmap
        normalized_traces = traces.div(traces.max(axis=0), axis=1)  # normalize each trace to its maximum
        plt.figure(figsize=(10, 6))
        sns.heatmap(normalized_traces.T, cmap='cividis', cbar_kws={'label': 'Normalized Signal'}, yticklabels=False)
        plt.xticks(ticks=x_tick_positions, labels=x_ticks, rotation=45)
        plt.axvline(x=244, color='#D55E00', linestyle='--', label='cue starts')
        plt.xlabel('Time (s)')
        plt.title(f'Normalized Heatmap of Traces - {file_path.stem}')
        plt.tight_layout()
        plt.savefig(save_dir / f'normalized_heatmap_{file_path.stem}.png')
        plt.close()

        # Calculate the average trace and standard deviation across columns (traces)
        mean_trace = traces.mean(axis=1, skipna=True)  # average for each row (i.e., across all traces)
        std_trace = traces.std(axis=1, skipna=True)  # standard deviation for each row

        # Plot the average trace and standard deviation
        plt.plot(time, mean_trace, label='Average Trace', color='#0072B2')
        plt.fill_between(time, mean_trace - std_trace, mean_trace + std_trace, color='#0072B2', alpha=0.3, label='Standard Deviation')

        # Add a red dotted line at the 0-second mark
        plt.axvline(x=0, color='#D55E00', linestyle='--', label='cue starts')

        # Add a light green rectangle between 0 and 5 seconds at the top of the plot
        plt.axvspan(0, 5, ymin=0.95, ymax=1.0, color='lightgreen', alpha=0.2, label='Reward Availability')

        # Labels and title
        plt.xlabel('Time (s)')
        plt.ylabel('dF/F')  # Adjust this based on what you're plotting
        plt.title(f'Average Trace with Standard Deviation - {file_path.stem}')

        # Move the legend outside of the plot
        plt.legend(loc='upper right', bbox_to_anchor=(1, 1))

        # Finalize and save the plot
        plt.tight_layout()
        plt.savefig(save_dir / f'average_trace_{file_path.stem}.png', bbox_inches='tight')  # Ensure the legend fits in the plot
        plt.close()

    print(f"Plots for {phase} saved to {save_dir}")
