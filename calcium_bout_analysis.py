from pathlib import Path
import numpy as np
from scipy import signal, optimize
import pandas as pd

from phase_utils import filter_range

# Set which time column to use: 'Time' or 'Original_Time'
time_column = 'Original_Time'  # Or 'Original_Time' if preferred

# Compute AUC on calcium data for bout
def bout_auc(bout_calcium_data: np.ndarray, time: np.ndarray):
    # Apply low-pass filter to smooth data
    elapsed_time = time[-1] - time[0]
    sr = int(bout_calcium_data.shape[0] / elapsed_time)
    b, a = signal.butter(2, 2, fs=sr)
    bout_calcium_filtered = signal.filtfilt(b, a, bout_calcium_data)

    # Adjust filtered data to minimum point in bout and compute AUC
    bout_calcium_filtered -= bout_calcium_filtered.min()
    auc = np.trapz(bout_calcium_filtered, dx=1)
    return auc

# Compute pre-bout calcium slope
def bout_slope(bout_calcium: pd.DataFrame):
    # Extract data for the first 0.5 seconds
    pre_bout_calcium = bout_calcium[bout_calcium.index <= 0.5]

    # Check if pre_bout_calcium contains data
    if pre_bout_calcium.empty:
        return np.nan

    # Calculate slope if data exists
    pre_bout_rise = pre_bout_calcium['AIN01'].iloc[-1] - pre_bout_calcium['AIN01'].iloc[0]
    pre_bout_rate = pre_bout_calcium.index[-1] - pre_bout_calcium.index[0]
    return pre_bout_rise / pre_bout_rate

# Simple function to model an exponential curve
def exp_curve(t, A, B, C):
    return A * np.exp(B * t) + C

# Compute pre-bout calcium exponential rise/decay rate
def bout_exprate(bout_calcium: pd.DataFrame):
    # Extract data for the first 0.5 seconds
    pre_bout_calcium = bout_calcium[bout_calcium.index <= 0.5]

    # Check if pre_bout_calcium contains data
    if pre_bout_calcium.empty:
        return np.nan

    # Perform exponential curve fitting
    t = pre_bout_calcium.index.to_numpy()
    t -= t[0]
    y = pre_bout_calcium['AIN01'].to_numpy()
    params, _ = optimize.curve_fit(exp_curve, t, y, maxfev=10000)
    A, B, C = params
    return B

# Compute adjusted max calcium based on first value
def bout_max(bout_calcium_data: np.ndarray):
    bout_calcium_adjusted = bout_calcium_data - bout_calcium_data[0]
    return bout_calcium_adjusted.max()

# Compute various metrics on calcium bout     
def main(arduino_stats: Path, sheet: str, calcium_bout_file: Path):
    try:
        # Import mouse stats and calcium bout-specific data
        mouse_stats = pd.read_excel(arduino_stats, sheet_name=f'{sheet} Bouts')
        calcium_data = pd.read_excel(calcium_bout_file, sheet_name=None, index_col=time_column)

        # Check if calcium data for bouts exists
        if f'Bout 1' not in calcium_data.keys():
            print(f"No bout data found for {sheet}. Skipping.")
            return  # Skip if no bouts are available

        # For each bout
        metrics = {
            'AUC Metric': [], 
            'Pre-Bout Calcium Slope': [], 
            'Pre-Bout Calcium ExpRate': [],
            'Max Calcium': []
        }
        for index, bout in mouse_stats.iterrows():
            # Retrieve corresponding calcium data for bout
            bout_calcium = calcium_data.get(f'Bout {index + 1}')
            if bout_calcium is None or bout_calcium.empty:
                # If bout calcium data is missing, append NaNs for each metric
                metrics['AUC Metric'].append(np.nan)
                metrics['Pre-Bout Calcium Slope'].append(np.nan)
                metrics['Pre-Bout Calcium ExpRate'].append(np.nan)
                metrics['Max Calcium'].append(np.nan)
                continue

            bout_calcium_data = bout_calcium['AIN01'].to_numpy()
            bout_time = bout_calcium.index.to_numpy()

            # Compute metrics
            metrics['AUC Metric'].append(bout_auc(bout_calcium_data, bout_time))
            metrics['Pre-Bout Calcium Slope'].append(bout_slope(bout_calcium))
            metrics['Pre-Bout Calcium ExpRate'].append(bout_exprate(bout_calcium))
            metrics['Max Calcium'].append(bout_max(bout_calcium_data))
        
        # Create new data frame with updated metrics
        metrics_frame = pd.DataFrame(metrics, index=mouse_stats.index)
        mouse_stats[metrics_frame.columns] = metrics_frame
        
        # Attempt to write to Excel
        with pd.ExcelWriter(arduino_stats, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            mouse_stats.to_excel(writer, sheet_name=f'{sheet} Bouts', index=False)

    except Exception as e:
        print(f"Error occurred while processing {sheet}: {e}")

# Path to the directories containing the Arduino and calcium data
arduino_dir = Path('parsed_data')
arduino_stats_dir = Path('stats')
calcium_dir = Path('stats')  # Updated to point to bout-specific calcium files

# Iterate through each phase folder in the Arduino data directory
for phase_folder in arduino_dir.glob('phase *'):
    phase = phase_folder.name.split()[-1]

    # Iterate through each Arduino file in the phase folder
    for arduino_file in phase_folder.glob('phase*.xlsx'):
        # Load the Excel file to get the sheet names (mouse IDs)
        with pd.ExcelFile(arduino_file) as xls:
            sheets = xls.sheet_names

        # Iterate through each sheet name (mouse ID) in the Arduino file
        for sheet in sheets:
            # Construct the path to the bout-specific calcium file
            calcium_bout_file = calcium_dir / f'phase {phase}' / f'{sheet}_bouts.xlsx'
            
            # Check if the bout file exists before processing
            if calcium_bout_file.exists():
                arduino_stats_file = arduino_stats_dir / f'phase {phase}' / f'{arduino_file.stem}-reward.xlsx'
                print(f"Processing Arduino file: {arduino_stats_file}, Sheet: {sheet}, Calcium file: {calcium_bout_file}")
                main(arduino_stats_file, sheet, calcium_bout_file)
            else:
                print(f"Calcium bout file not found for {sheet} in phase {phase}. Skipping.")
