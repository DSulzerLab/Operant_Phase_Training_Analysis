from pathlib import Path
import numpy as np
from scipy import signal, optimize
import pandas as pd

from phase_utils import filter_range

# Apply low-pass filter to smooth calcium data
def lowpass_filter(bout_calcium_data: np.ndarray, time: np.ndarray):
    elapsed_time = (time[-1] - time[0]) / 1000
    sr = int(bout_calcium_data.shape[0] / elapsed_time)
    b, a = signal.butter(2, 2, fs = sr)
    bout_calcium_filtered = signal.filtfilt(b, a, bout_calcium_data)
    return bout_calcium_filtered

# Compute AUC on calcium data for bout
def bout_auc(bout_calcium_data: np.ndarray, time: np.ndarray):
    # Adjust filtered data to minimum point in bout and compute AUC
    bout_calcium_filtered = lowpass_filter(bout_calcium_data, time)
    bout_calcium_filtered -= bout_calcium_filtered.min()
    auc = np.trapz(bout_calcium_filtered, dx = 1)
    return auc

# Compute pre-bout calcium slope
def bout_slope(bout_calcium: pd.DataFrame, bout: pd.DataFrame):
    # Adjust time index
    bout_calcium_adjusted = bout_calcium.copy()
    bout_calcium_adjusted.index /= 1000

    pre_bout_calcium = filter_range(bout_calcium_adjusted, [bout['Start'] / 1000 - 0.5, bout['Start'] / 1000])
    pre_bout_rise = pre_bout_calcium['Values'].iloc[-1] - pre_bout_calcium['Values'].iloc[0]
    pre_bout_rate = pre_bout_calcium.index[-1] - pre_bout_calcium.index[0]
    return pre_bout_rise / pre_bout_rate

# Simple function to model an exponential curve
def exp_curve(t, A, B, C):
    return A * np.exp(B * t) + C

# Compute pre-bout calcium exponential rise/decay rate
def bout_exprate(bout_calcium: pd.DataFrame, bout: pd.DataFrame):
    # Adjust time index
    bout_calcium_adjusted = bout_calcium.copy()
    bout_calcium_adjusted.index /= 1000

    pre_bout_calcium = filter_range(bout_calcium_adjusted, [bout['Start'] / 1000 - 0.5, bout['Start'] / 1000])
    t = pre_bout_calcium.index.to_numpy()
    t -= t[0]
    y = pre_bout_calcium['Values'].to_numpy()
    params, _ = optimize.curve_fit(exp_curve, t, y, maxfev=10000)
    A, B, C = params
    return B

# Compute t 1/2 of calcium trace
def bout_t_onehalf(bout_calcium_data: np.ndarray, time: np.ndarray):
    # Apply low-pass filter to smooth data
    bout_calcium_filtered = lowpass_filter(bout_calcium_data, time)
    bout_calcium_filtered -= bout_calcium_filtered.min()

    # Filter calcium that comes after max point
    y = bout_calcium_filtered[np.argmax(bout_calcium_filtered):]
    t = time[np.argmax(bout_calcium_filtered):] / 1000
    t -= t[0]

    # Compute exponential decay factor
    custom_exp_decay = lambda t, K: exp_curve(t, np.max(y), -K, 0)
    params, _ = optimize.curve_fit(custom_exp_decay, t, y, maxfev = 10000)

    # Compute t 1/2 from decay factor
    K = params[0]
    t_onehalf = np.log(2) / K 

    return t_onehalf   

# Compute adjusted max calcium based on first value
def bout_max(bout_calcium_data: np.ndarray):
    bout_calcium_adjusted = bout_calcium_data - bout_calcium_data[0]
    return bout_calcium_adjusted.max()

# Compute various metrics on calcium bout     
def main(arduino_stats: Path, sheet: str, calcium: Path):
    # Import mouse stats and calcium data
    mouse_stats = pd.read_excel(arduino_stats, sheet_name = f'{sheet} Bouts')
    calcium_data = pd.read_excel(calcium, sheet_name = None, index_col = 'Time')

    # For each bout
    metrics = {
        'AUC Metric': [], 
        'Pre-Bout Calcium Slope': [], 
        'Pre-Bout Calcium ExpRate': [],
        't One-Half': [],
        'Max Calcium': []
    }
    for index, bout in mouse_stats.iterrows():
        # Retrieve corresponding calcium data for bout
        bout_calcium = calcium_data[f'Bout {index + 1}']
        bout_calcium_data = bout_calcium['Values'].to_numpy()
        bout_time = bout_calcium.index.to_numpy()

        # Compute metrics
        metrics['AUC Metric'].append(bout_auc(bout_calcium_data, bout_time))
        metrics['Pre-Bout Calcium Slope'].append(bout_slope(bout_calcium, bout))
        metrics['Pre-Bout Calcium ExpRate'].append(bout_exprate(bout_calcium, bout))
        metrics['t One-Half'].append(bout_t_onehalf(bout_calcium_data, bout_time))
        metrics['Max Calcium'].append(bout_max(bout_calcium_data))
    
    # Create new data frame with updated metrics
    metrics_frame = pd.DataFrame(metrics, index = mouse_stats.index)
    mouse_stats[metrics_frame.columns] = metrics_frame
    with pd.ExcelWriter(arduino_stats, mode = 'a', engine = 'openpyxl', if_sheet_exists = 'replace') as writer:
        mouse_stats.to_excel(writer, sheet_name = f'{sheet} Bouts', index = False)

# Path to the directories containing the Arduino and calcium data
arduino_dir = Path('parsed_data')
arduino_stats_dir = Path('stats')
calcium_dir = Path('parsed_data')

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
            # Construct the corresponding calcium file path
            calcium_file = calcium_dir / f'phase {phase}' / f'{sheet}.xlsx'
            
            # Check if the calcium file exists before processing
            if calcium_file.exists():
                arduino_stats_file = arduino_stats_dir / f'phase {phase}' / f'{arduino_file.stem}-reward.xlsx'
                print(f"Processing Arduino file: {arduino_stats_file}, Sheet: {sheet}, Calcium file: {calcium_file}")
                main(arduino_stats_file, sheet, calcium_file)
            else:
                print(f"Calcium file not found for {sheet} in phase {phase}")
