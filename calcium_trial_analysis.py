import pandas as pd
import numpy as np
from scipy.integrate import simps
from pathlib import Path
from scipy.stats import linregress

# Define the root directory containing all phase folders
root_dir = Path('trials')

# Set the fixed peak index for 0 seconds (244th value in the series)
peak_index = 244

# Function to calculate metrics for a given file
def calculate_metrics(file_path, output_dir):
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Set time column as index
    time = df['Time'].values
    df = df.set_index('Time')

    # Initialize an output dictionary to store metrics for each trial
    output_data = {
        'Trial': [], 
        'Amplitude': [], 
        'AUC': [], 
        'Rate of Increase': [], 
        'Decay': [], 
        'Amplitude (Z-Score)': [], 
        'Amplitude (Normalized)': []
    }

    # Loop through each trial (column)
    for trial in df.columns:
        calcium_trace = df[trial].values

        # Calculate amplitude as the value at the fixed index (244th value, corresponding to 0 seconds)
        amplitude = calcium_trace[peak_index]

        # Calculate AUC (using Simpson's rule for numerical integration from 0 to 8 seconds)
        auc = simps(calcium_trace[peak_index:], time[peak_index:])

        # Calculate rate of increase (slope between the range from -2 seconds to 0 seconds)
        pre_peak_calcium = calcium_trace[:peak_index]
        pre_peak_time = time[:peak_index]
        rate_of_increase = (pre_peak_calcium[-1] - pre_peak_calcium[0]) / (pre_peak_time[-1] - pre_peak_time[0])

        # Calculate decay (difference between peak and the last value after the peak)
        post_peak_calcium = calcium_trace[peak_index:]
        decay = amplitude - post_peak_calcium[-1]

        # Calculate z-score for amplitude (using pre-peak values for normalization)
        mean_pre_peak = np.mean(pre_peak_calcium)
        std_pre_peak = np.std(pre_peak_calcium)
        z_score_amplitude = (amplitude - mean_pre_peak) / std_pre_peak if std_pre_peak != 0 else np.nan

        # Calculate amplitude after normalizing the trace between 0 and 1
        min_trace = np.min(calcium_trace)
        max_trace = np.max(calcium_trace)
        normalized_amplitude = (amplitude - min_trace) / (max_trace - min_trace) if max_trace != min_trace else np.nan

        # Store the results in the output dictionary
        output_data['Trial'].append(trial)
        output_data['Amplitude'].append(amplitude)
        output_data['AUC'].append(auc)
        output_data['Rate of Increase'].append(rate_of_increase)
        output_data['Decay'].append(decay)
        output_data['Amplitude (Z-Score)'].append(z_score_amplitude)
        output_data['Amplitude (Normalized)'].append(normalized_amplitude)

    # Convert the dictionary to a DataFrame
    output_df = pd.DataFrame(output_data)

    # Define output file path
    output_file = output_dir / f"{file_path.stem}_metrics.xlsx"

    # Save the results to an Excel file
    output_df.to_excel(output_file, index=False)
    print(f"Metrics for {file_path.name} saved to {output_file}")

# Function to analyze each metrics file and compute the required values
def analyze_metrics_file(file_path):
    # Load the metrics file
    df = pd.read_excel(file_path)

    # Initialize results dictionary to store aggregated metrics
    results = {
        'File': file_path.stem,
        'Average Amplitude': np.nanmean(df['Amplitude']),
        'Average AUC': np.nanmean(df['AUC']),
        'Average Rate of Increase': np.nanmean(df['Rate of Increase']),
        'Average Decay': np.nanmean(df['Decay']),
        'Average Amplitude (Z-Score)': np.nanmean(df['Amplitude (Z-Score)']),
        'Average Amplitude (Normalized)': np.nanmean(df['Amplitude (Normalized)']),
        'Std Amplitude': np.nanstd(df['Amplitude']),
        'Std AUC': np.nanstd(df['AUC']),
        'Std Rate of Increase': np.nanstd(df['Rate of Increase']),
        'Std Decay': np.nanstd(df['Decay']),
        'Std Amplitude (Z-Score)': np.nanstd(df['Amplitude (Z-Score)']),
        'Std Amplitude (Normalized)': np.nanstd(df['Amplitude (Normalized)']),
        'First Amplitude': df['Amplitude'].iloc[0] if pd.notna(df['Amplitude'].iloc[0]) else np.nan,
        'Last Amplitude': df['Amplitude'].iloc[-1] if pd.notna(df['Amplitude'].iloc[-1]) else np.nan,
        'First AUC': df['AUC'].iloc[0] if pd.notna(df['AUC'].iloc[0]) else np.nan,
        'Last AUC': df['AUC'].iloc[-1] if pd.notna(df['AUC'].iloc[-1]) else np.nan,
        'First Rate of Increase': df['Rate of Increase'].iloc[0] if pd.notna(df['Rate of Increase'].iloc[0]) else np.nan,
        'Last Rate of Increase': df['Rate of Increase'].iloc[-1] if pd.notna(df['Rate of Increase'].iloc[-1]) else np.nan,
        'First Decay': df['Decay'].iloc[0] if pd.notna(df['Decay'].iloc[0]) else np.nan,
        'Last Decay': df['Decay'].iloc[-1] if pd.notna(df['Decay'].iloc[-1]) else np.nan
    }

    # Compute rate of change (slope) for each metric using linear regression over trials
    trials = np.arange(1, len(df) + 1)  # Trial numbers (1, 2, 3, ...)
    
    for metric in ['Amplitude', 'AUC', 'Rate of Increase', 'Decay', 'Amplitude (Z-Score)', 'Amplitude (Normalized)']:
        # Drop NaN values for this metric
        valid_trials = ~np.isnan(df[metric])
        if valid_trials.sum() > 1:  # Only perform regression if more than one valid data point
            slope, _, _, _, _ = linregress(trials[valid_trials], df[metric][valid_trials])
            results[f'{metric} Rate of Change'] = slope
        else:
            results[f'{metric} Rate of Change'] = np.nan  # If not enough valid points, set to NaN

    return results

# Process each phase folder
for phase in ['phase 1', 'phase 2', 'phase 3']:
    input_dir = root_dir / phase
    output_dir = root_dir / f'metrics_output_{phase}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each Excel file in the input directory
    for file in input_dir.glob('*.xlsx'):
        calculate_metrics(file, output_dir)

    # Summarize all metrics files in the output directory for the current phase
    summary_data = []
    for file in output_dir.glob('*.xlsx'):
        file_summary = analyze_metrics_file(file)
        summary_data.append(file_summary)

    # Convert the summary data to a DataFrame and save it as an Excel file
    summary_output_file = root_dir / f'metrics_summary_{phase}.xlsx'
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(summary_output_file, index=False)
    print(f"Summary of metrics for {phase} saved to {summary_output_file}")
