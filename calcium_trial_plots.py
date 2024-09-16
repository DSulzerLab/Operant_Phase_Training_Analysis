from pathlib import Path
import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt

from phase_utils import filter_range, lick_reward_split

# Basic line plot of each trial
# Includes markings for cue period, lever press, and licks
def trial_plot(arduino: Path, sheet: str, calcium: Path):
    # Import Arduino log and calcium trace data
    arduino_data = pd.read_excel(arduino, index_col = 'Time', sheet_name = sheet)
    calcium_data = pd.read_excel(calcium, index_col = 'Time', sheet_name = None)

    # Convert time index into seconds for easier plotting
    arduino_data.index /= 1000
    
    # Get number of trials in data
    cues = arduino_data['Cue'].dropna()
    cue_on = cues[cues == 'On']
    cue_off = cues[cues == 'Off']
    num_trials = cue_on.shape[0]

    # Get licks and rewards
    licks = arduino_data['# of Licks'].dropna()
    rewards = arduino_data['Reward'].dropna()

    # Get lever press data if Phase 3
    if 'phase 3' in arduino.stem:
        presses = arduino_data['Lever Press'].dropna()
        # Remove rewards that are printed with presses
        press_reward = [x for x in rewards.index if np.min(np.abs(presses.index - x)) < 0.005]
        rewards = rewards.loc[rewards.index.difference(press_reward)]
    
    # Split licks into rewarding/non-rewarding
    licks_rewarded, licks_not_rewarded = lick_reward_split(rewards, licks)

    # Set up output directories
    dir_tree = '/'.join(arduino.parts[1:-1])
    output_dir = Path(f'plots/{dir_tree}/{calcium.stem}/trials')
    output_dir.mkdir(parents = True, exist_ok = True)

    # Get maximum point in calcium data
    max_calcium = np.max([calcium_data[trial]['Values'].max() for trial in calcium_data])

    # For each trial
    for trial in range(num_trials):
        # Mark cue on and cue off times
        cue_on_time = cue_on.index[trial]
        cue_off_time = cue_off.index[trial]

        # Retrieve calcium data and adjust index
        calcium_trial = calcium_data[f'Trial {trial + 1}']
        calcium_trial.index /= 1000 

        # If past the first trial
        if trial > 0:
            # Prepend data from previous two seconds
            prev_trial = calcium_data[f'Trial {trial}']
            trial_twosec = filter_range(prev_trial, [cue_on_time - 2, cue_on_time])
            calcium_trial = pd.concat((trial_twosec, calcium_trial))
            data_start = cue_on_time - 2
            axis_start = -2
            tick_start = -2
        else:
            data_start = cue_on_time
            axis_start = -0.5 # For a bit of padding
            tick_start = 0

        # Mark end range of plot based on trial duration
        if trial + 1 < num_trials:
            data_end = cue_on.index[trial + 1]
            axis_end = data_end - cue_on_time
        else:
            data_end = arduino_data.index[-1]
            axis_end = data_end - cue_on_time
        
        # Extract rewarded and non-rewarded licks
        licks_rewarded_trial = filter_range(licks_rewarded, [data_start, data_end])
        licks_not_rewarded_trial = filter_range(licks_not_rewarded, [data_start, data_end])
        
        # Create range for calcium plot starting from data
        x = calcium_trial.index - cue_on_time

        # Extract calcium trace
        calcium_trace = calcium_trial['Values']

        # Create line plot
        plt.figure()
        plt.plot(x, calcium_trace, color = '#218BFF')

        # Mark cue start and duration
        plt.axvline(0, color = '#000000', linestyle = '--', label = 'Cue Start')
        plt.axvspan(0, cue_off_time - cue_on_time, alpha = 0.2, color = '#218BFF', label = 'Cue On')

        # Phase 3 specific - mark lever press time
        if 'phase 3' in arduino.stem:
            press_cue = filter_range(presses, [cue_on_time, data_end])
            if press_cue.shape[0] > 0:
                first_press = press_cue.index[0]
                last_press = press_cue.index[-1]
                plt.axvline(press_cue.index - cue_on_time, color = '#FF0000', linestyle = '--', label = 'Lever Press')
                plt.axvspan(first_press - cue_on_time, last_press - cue_on_time + 5, alpha = 0.2, color = '#4B0092', label = 'Lever Press Time')

        # Mark licks (if any)
        plt.scatter(licks_rewarded_trial.index - cue_on_time, np.ones(licks_rewarded_trial.shape[0]) * max_calcium + 0.5, marker = '|', color = '#DD7815', label = 'Rewarding Licks')
        plt.scatter(licks_not_rewarded_trial.index - cue_on_time, np.ones(licks_not_rewarded_trial.shape[0]) * max_calcium + 0.5, marker = '|', color = '#000000', label = 'Non-Rewarding Licks')

        # Adjust axis range and labels
        plt.xlabel('Time (s)')
        plt.ylabel(r"$\Delta F/F$")
        plt.xlim(axis_start, axis_end)
        plt.xticks(np.arange(tick_start, axis_end, 2))
        plt.ylim(top = max_calcium + 1)

        # Export plot
        plt.legend(loc = 'lower center', bbox_to_anchor = (0.5, 1.0), ncol = 3)
        plt.tight_layout()
        plt.savefig(output_dir / f'trial{trial + 1}.png', dpi = 600)
        plt.close()

# Compute average plot for rewarding/non-rewarding trials
def trial_average_plot(arduino_stats: Path, sheet: str, calcium: Path):
    # Import statistics and calcium data
    mouse_stats = pd.read_excel(arduino_stats, sheet_name = f'{sheet} Trial Stats')
    calcium_data = pd.read_excel(calcium, sheet_name = None, index_col = 'Time')

    # Get trial statistics for mouse ID and compute rewarding/non-rewarding trials
    mouse_stats = mouse_stats.set_index(mouse_stats.columns[0])
    if 'Trial 0' in mouse_stats.index:
        mouse_stats = mouse_stats.drop('Trial 0')
    mouse_stats = mouse_stats.drop('Trial 1')
    rewarding_trials = mouse_stats.dropna().index
    non_rewarding_trials = mouse_stats.index.difference(rewarding_trials)

    # Set up output directories
    dir_tree = '/'.join(arduino_stats.parts[1:-1])
    output_dir = Path(f'plots/{dir_tree}/{calcium.stem}')
    output_dir.mkdir(parents = True, exist_ok = True)
    
    # Plot rewarding and non-rewarding trials separately
    trial_split = [rewarding_trials, non_rewarding_trials]
    for index, split in enumerate(trial_split):
        if split.shape[0] == 0:
            continue

        # Get calcium data for selected trial
        calcium_trials = [calcium_data[x]['Values'].to_numpy() for x in split]

        # Truncate all trials to minimum length
        lengths = [x.shape[0] for x in calcium_trials]
        min_index = np.argmin(lengths)
        min_length = np.min(lengths)
        calcium_trials = [x[:min_length] for x in calcium_trials]

        # Compute mean and SEM
        calcium_mean = np.mean(calcium_trials, axis = 0)
        calcium_sem = stats.sem(calcium_trials, axis = 0)

        # Select time range
        time = calcium_data[split[min_index]].index
        time -= time[0]
        time /= 1000

        # Create plot
        figure_name = 'rewarding' if index == 0 else 'nonrewarding'
        plt.figure()
        plt.plot(time, calcium_mean, color = '#218BFF')
        plt.fill_between(time, calcium_mean - calcium_sem, calcium_mean + calcium_sem, color = '#218BFF', alpha = 0.2)
        plt.xlabel('Time (s)')
        plt.ylabel(r"$\Delta F/F$")
        plt.xticks(np.arange(0, time[-1], 2))
        plt.tight_layout()
        plt.savefig(output_dir / f'trials-average-{figure_name}.png', dpi = 600)
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
                trial_plot(arduino_file, sheet, calcium_file)
                trial_average_plot(arduino_stats_file, sheet, calcium_file)
            else:
                print(f"Calcium file not found for {sheet} in phase {phase}")
