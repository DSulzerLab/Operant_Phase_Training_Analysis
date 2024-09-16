from pathlib import Path
import numpy as np
from scipy import stats, optimize, signal
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from phase_utils import filter_range, lick_reward_split

# Basic line plot of each lick bout
def lick_bout_plot(arduino: Path, arduino_stats: Path, sheet: str, calcium: Path):
    # Import bout statistics and calcium data
    arduino_data = pd.read_excel(arduino, index_col = 'Time', sheet_name = sheet)
    mouse_stats = pd.read_excel(arduino_stats, sheet_name = f'{sheet} Bouts')
    calcium_data = pd.read_excel(calcium, sheet_name = None, index_col = 'Time')

    # Convert time index into seconds for easier plotting
    arduino_data.index /= 1000
    for trial in calcium_data:
        calcium_data[trial].index /= 1000
    mouse_stats["Start"] /= 1000
    mouse_stats["End"] /= 1000

    # Get licks and rewards
    licks = arduino_data['# of Licks'].dropna()
    rewards = arduino_data['Reward'].dropna()

    # Split licks into rewarding/non-rewarding
    licks_rewarded, licks_not_rewarded = lick_reward_split(rewards, licks)

    # Set up output directories
    dir_tree = '/'.join(arduino_stats.parts[1:-1])
    output_dir = Path(f'plots/{dir_tree}/{calcium.stem}/bouts')
    output_dir.mkdir(parents = True, exist_ok = True)

    # Get maximum point in calcium data
    max_calcium = np.max([calcium_data[trial]['Values'].max() for trial in calcium_data])

    # For each bout
    for index, bout in mouse_stats.iterrows():
        # Retrieve corresponding calcium data for bout
        bout_calcium = calcium_data[f'Bout {index + 1}']

        # Ensure at least 0.5s of data is available
        start = bout['Start']
        end = bout['End'] + 0.5

        # Extract rewarded and non-rewarded licks
        licks_rewarded_bout = filter_range(licks_rewarded, [start, end])
        licks_not_rewarded_bout = filter_range(licks_not_rewarded, [start, end])

        # Compute time points
        time = bout_calcium.index - start

        # Plot calcium
        plt.figure()
        plt.plot(time, bout_calcium['Values'], color = '#218BFF')

        # Mark licks (if any)
        plt.scatter(licks_rewarded_bout.index - start, np.ones(licks_rewarded_bout.shape[0]) * max_calcium + 0.5, marker = '|', color = '#DD7815', label = 'Rewarding Licks')
        plt.scatter(licks_not_rewarded_bout.index - start, np.ones(licks_not_rewarded_bout.shape[0]) * max_calcium + 0.5, marker = '|', color = '#000000', label = 'Non-Rewarding Licks')

        plt.xlabel('Time (s)')
        plt.ylabel(r"$\Delta F/F$")
        plt.xlim(-0.5, end - start)
        plt.ylim(top = max_calcium + 1)
        plt.savefig(output_dir / f'bout{index}.png', dpi = 600)
        plt.close()

# Simple function to model an exponential curve
def exp_curve(t, A, B, C):
    return A * np.exp(B * t) + C

# Scatter plot of # of licks against max peak amplitude of calcium
def lick_bout_scatter(arduino: Path, arduino_stats: Path, sheet: str, calcium: Path):
    # Import bout statistics and calcium data
    arduino_data = pd.read_excel(arduino, index_col = 'Time', sheet_name = sheet)
    mouse_stats = pd.read_excel(arduino_stats, sheet_name = f'{sheet} Bouts')
    calcium_data = pd.read_excel(calcium, sheet_name = None, index_col = 'Time')

    # Convert time index into seconds for easier plotting
    arduino_data.index /= 1000
    for trial in calcium_data:
        calcium_data[trial].index /= 1000
    mouse_stats["Start"] /= 1000
    mouse_stats["End"] /= 1000

    # Set up output directories
    dir_tree = '/'.join(arduino_stats.parts[1:-1])
    output_dir = Path(f'plots/{dir_tree}/{calcium.stem}/bout_scatter')
    output_dir.mkdir(parents = True, exist_ok = True)

    # For each combination of features
    features = [x for x in mouse_stats.columns[3:] if 'Rewarding' not in x] 
    for i in range(len(features) - 1):
        xfeature = features[i]
        for j in range(i + 1, len(features)):
            yfeature = features[j]
            # Determine correlation coefficient
            features_frame = mouse_stats[[xfeature, yfeature, 'Rewarding']]
            rewarding_features = features_frame[features_frame['Rewarding']].dropna()
            non_rewarding_features = features_frame[~features_frame['Rewarding']].dropna()
            if rewarding_features.shape[0] > 0:
                rewarding_corr_coef, _ = np.round(stats.pearsonr(rewarding_features[xfeature], rewarding_features[yfeature]), 2)
            if non_rewarding_features.shape[0] > 0:
                non_rewarding_corr_coef, _ = np.round(stats.pearsonr(non_rewarding_features[xfeature], non_rewarding_features[yfeature]), 2)

            lm = sns.lmplot(features_frame, x = xfeature, y = yfeature, hue = 'Rewarding', col = 'Rewarding', palette = {True: '#DD7815', False: '#000000'})
            fig = lm.figure

            if non_rewarding_features.shape[0] > 0:
                ax1 = fig.axes[0]
                ax1.set_title(r'Non-Rewarding Bouts $(R^2 = ' + str(non_rewarding_corr_coef) + r'$)')
            if rewarding_features.shape[0] > 0:
                ax2 = fig.axes[-1]
                ax2.set_title(r'Rewarding Bouts $(R^2 = ' + str(rewarding_corr_coef) + r'$)')

            name = f'{xfeature}-{yfeature}'
            
            plt.tight_layout()
            plt.savefig(output_dir / f'{name}.png', dpi = 600)
            plt.close()

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
                lick_bout_plot(arduino_file, arduino_stats_file, sheet, calcium_file)
                lick_bout_scatter(arduino_file, arduino_stats_file, sheet, calcium_file)
            else:
                print(f"Calcium file not found for {sheet} in phase {phase}")
