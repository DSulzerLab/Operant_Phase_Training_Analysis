from pathlib import Path
import numpy as np
import pandas as pd

from phase_utils import *

# Compute stats on mice operant training task for phase 1
def phase1(data: pd.DataFrame, mode: str):
    # Extract required columns
    licks = data['# of Licks'].dropna()
    trials = data['Trial Number'].dropna()

    # Split licks into rewarded and not rewarded and compute stats
    if mode == 'reward':
        rewards = data['Reward'].dropna()
        licks_rewarded, licks_not_rewarded = lick_reward_split(rewards, licks)
    elif mode == 'time':
        cues = data['Cue'].dropna()
        licks_rewarded, licks_not_rewarded, _ = cue_split(cues, licks)
    lick_stats = ratio_stats(licks_rewarded, licks_not_rewarded)
    assert(lick_stats[-1] == licks.sum())

    # Compute latency to first lick
    trials_start = trials.drop_duplicates()
    initial_lick_latency = latency_to_first_lick(licks_rewarded, time = trials_start.index[0])

    # Parse lick stats across all trials
    stat_names = ['Latency to First Lick (ms)', 
                    '# of Rewarded Licks', 
                    '# of Non-Rewarded Licks', 
                    'Total # of Licks']

    # Export aggregate stats to sheet
    aggregate_data = (initial_lick_latency,) + lick_stats
    aggregate_frame = pd.DataFrame(aggregate_data, index = stat_names)

    # Parse each trial
    trial_records = []
    for i in range(trials_start.shape[0]):
        start = trials_start.index[i]
        if i < trials_start.shape[0] - 1:
            end = trials_start.index[i + 1]
        else:
            end = None
        time_range = [start, end]

        # Compute stats
        trial_latency = latency_to_first_lick(licks_rewarded, trials = trials, time_range = time_range)
        trial_stats = ratio_stats(licks_rewarded, licks_not_rewarded, time_range = time_range)
        trial_records.append((trial_latency,) + trial_stats)
    
    # Create DataFrame
    indexes = [f'Trial {int(x)}' for x in trials_start]
    trial_frame = pd.DataFrame(trial_records, index = indexes, columns = stat_names)

    # Export bout information
    bout_frame = lick_bouts(licks, licks_rewarded, trials_start)

    return aggregate_frame, trial_frame, bout_frame

# Compute stats on mice operant training task for phase 2
def phase2(data: pd.DataFrame, mode: str):
    # Extract required columns
    licks = data['# of Licks'].dropna()
    trials = data['Trial Number'].dropna()
    presses = data['Lever Press'].dropna()

    # Create aggregate stats
    stat_names = ['# of Trials', 
                  'Latency to First Press (ms)', 
                  'Latency to First Lick (ms)', 
                  '# of Rewarded Licks', 
                  '# of Non-Rewarded Licks', 
                  'Total # of Licks']
    
    # Split licks into rewarded and not rewarded and compute stats
    if mode == 'reward':
        rewards = data['Reward'].dropna()
        licks_rewarded, licks_not_rewarded = lick_reward_split(rewards, licks)
    elif mode == 'time':
        cues = data['Cue'].dropna()
        licks_rewarded, licks_not_rewarded, _ = cue_split(cues, licks)
    lick_stats = ratio_stats(licks_rewarded, licks_not_rewarded)
    assert(lick_stats[-1] == licks.sum())

    # Number of lever presses (i.e. trials)
    num_lever_presses = presses.shape[0]

    # Latency to first press (i.e. trial) from test start
    start_time = data.index[0]
    first_press = presses.index[0]
    press_latency = first_press - start_time
    
    # Latency to first lick
    initial_lick_latency = latency_to_first_lick(licks_rewarded, time = data.index[0])

    # Export stats
    aggregate_data = (num_lever_presses, press_latency, initial_lick_latency) + lick_stats
    aggregate_frame = pd.DataFrame(aggregate_data, index = stat_names)

    # Parse each trial
    trial_records = []
    trials_start = trials.drop_duplicates()
    for i in range(trials_start.shape[0]):
        start = trials_start.index[i]
        if i < trials_start.shape[0] - 1:
            end = trials_start.index[i + 1]
        else:
            end = None
        time_range = [start, end]

        # Compute stats
        trial_lick_latency = latency_to_first_lick(licks_rewarded, trials = trials, time_range = time_range)
        trial_stats = ratio_stats(licks_rewarded, licks_not_rewarded, time_range = time_range)
        trial_records.append((trial_lick_latency,) + trial_stats)
    
    # Export trial data
    trial_indexes = [f'Trial {int(x)}' for x in trials_start]
    trial_frame = pd.DataFrame(trial_records, index = trial_indexes, columns = stat_names[2:])

    # Export bout information
    bout_frame = lick_bouts(licks, licks_rewarded, trials_start)

    return aggregate_frame, trial_frame, bout_frame

# Compute stats on mice operant training task for phase 3
def phase3(data: pd.DataFrame, mode: str):
    # Extract required columns
    licks = data['# of Licks'].dropna()
    trials = data['Trial Number'].dropna()
    cues = data['Cue'].dropna()
    presses = data['Lever Press'].dropna()

    # Create aggregate stats
    stat_names = ['Latency to First Press (ms)',
                    '# of Presses within Cue',
                    '# of Presses outside Cue',
                    'Total # of Presses', 
                    'Latency to First Lick (ms)', 
                    '# of Rewarded Licks', 
                    '# of Non-Rewarded Licks', 
                    'Total # of Licks']
    
    # Split presses into in/out of cue and compute stats
    press_in_cue, press_out_cue, cue_on = cue_split(cues, presses)
    press_stats = ratio_stats(press_in_cue, press_out_cue)
    assert(press_stats[-1] == presses.sum())

    # Split licks into rewarded and not rewarded and compute stats
    if mode == 'reward':
        rewards = data['Reward'].dropna()
        # Remove rewards that are printed with presses
        press_reward = [x for x in rewards.index if np.min(np.abs(presses.index - x)) < 5]
        rewards = rewards.loc[rewards.index.difference(press_reward)]
        licks_rewarded, licks_not_rewarded = lick_reward_split(rewards, licks)
    elif mode == 'time':
        licks_rewarded, licks_not_rewarded = lick_press_split(press_in_cue, licks)
    lick_stats = ratio_stats(licks_rewarded, licks_not_rewarded)
    assert(lick_stats[-1] == licks.sum())

    # Latency to first press from start of test
    trials_start = trials.drop_duplicates()
    initial_press_latency = latency_to_first_press(presses, time = trials_start.index[0])

    # Latency to first lick from start of test
    initial_lick_latency = latency_to_first_lick(licks_rewarded, time = trials_start.index[0])

    # Export stats to sheet
    aggregate_data = (initial_press_latency,) + press_stats + (initial_lick_latency,) + lick_stats
    aggregate_frame = pd.DataFrame(aggregate_data, index = stat_names)

    # Parse each trial
    trial_records = []
    for i in range(trials_start.shape[0]):
        # Get start/end times of trial
        start = trials_start.index[i]
        if i < trials_start.shape[0] - 1:
            end = trials_start.index[i + 1]
        else:
            end = None
        time_range = [start, end]

        # Compute press stats
        trial_press_latency = latency_to_first_press(press_in_cue, cues = cue_on, time_range = time_range)
        trial_press_stats = ratio_stats(press_in_cue, press_out_cue, time_range = time_range)

        # Compute lick stats
        trial_lick_latency = latency_to_first_lick(licks_rewarded, presses = press_in_cue, time_range = time_range)
        trial_lick_stats = ratio_stats(licks_rewarded, licks_not_rewarded, time_range = time_range)

        trial_records.append((trial_press_latency,) + trial_press_stats + (trial_lick_latency,) + trial_lick_stats)
    
    # Export trial data
    trial_indexes = [f'Trial {int(x)}' for x in trials_start]
    trial_frame = pd.DataFrame(trial_records, index = trial_indexes, columns = stat_names)

    # Export bout information
    bout_frame = lick_bouts(licks, licks_rewarded, trials_start)

    return aggregate_frame, trial_frame, bout_frame

# Split licks into lick bouts based on simple threshold
def lick_bouts(licks: pd.Series, licks_rewarded: pd.Series, trials_start: pd.Series, threshold: float = 0.5):
    # For each trial
    bout_records = []
    for i in range(trials_start.shape[0]):        
        # Filter licks within trial
        start = trials_start.index[i]
        if i == trials_start.shape[0] - 1:
            end = None
        else:
            end = trials_start.index[i + 1]
        trial_licks = filter_range(licks, [start, end])

        # Compute difference between each lick time
        # Use threshold to split into lick bouts
        if trial_licks.shape[0] > 0:
            threshold_ms = threshold * 1000
            time_diff = np.diff(trial_licks.index)
            trial_lick_bouts = np.split(trial_licks.index, np.where(time_diff > threshold_ms)[0] + 1)
            
            # Add record for lick bouts
            for bout in trial_lick_bouts:
                # Determine number of licks in bout
                bout_licks = filter_range(licks, [bout[0], bout[-1]])
                bout_lick_total = bout_licks.sum()

                # Determine whether bout is rewarding
                bout_lick_times = bout_licks.index.to_series()
                bout_licks_reward = bout_lick_times.apply(lambda x: x in licks_rewarded.index)
                bout_rewarding = bout_licks_reward.any()

                # Determine whether bout is highly rewarding
                bout_highly_rewarding = bout_licks_reward.sum() > 5

                # Determine lick efficiency
                bout_duration = bout[-1] - bout[0]
                if bout_duration > 0:
                    bout_lick_times = bout_licks.index.to_series()
                    bout_time_diff = np.diff(bout_lick_times)
                    bout_lick_efficiency = (bout_time_diff <= 150).sum() / bout_time_diff.shape[0]
                else:
                    bout_lick_efficiency = 0

                bout_records.append((int(trials_start.values[i]), bout[0], bout[-1], bout_lick_total, bout_rewarding, bout_highly_rewarding, bout_lick_efficiency))
    
    # Create DataFrame from bout records
    bout_frame_columns = ['Trial Number', 'Start', 'End', '# of Licks', 'Rewarding', "Highly Rewarding", 'Lick Efficiency']
    bout_frame = pd.DataFrame.from_records(bout_records, columns = bout_frame_columns)

    # Print warning if there are only non-rewarding or only rewarding bouts
    if bout_frame['Rewarding'].sum() == 0:
        print('WARNING: all bouts were identified as NON-REWARDING. Please double-check the original Arduino log to make sure this is valid.')
    elif bout_frame['Rewarding'].sum() == bout_frame.shape[0]:
        print('WARNING: all bouts were identified as REWARDING. Please double-check the original Arduino log to make sure this is valid.')
    
    return bout_frame

# Export stats on mice operant training task
def phase_stats(path: Path, mode: str, func: callable):
    # Import parsed data
    data = pd.read_excel(path, sheet_name = None)

    # Create ExcelWriter for output file
    file_name = path.stem.split('-')[0]
    dir_tree = list(path.parts[:-1])
    dir_tree[0] = 'stats'
    output_folder = Path(*dir_tree)
    output_folder.mkdir(parents = True, exist_ok = True)
    writer = pd.ExcelWriter(output_folder / f'{file_name}-{mode}.xlsx', engine = 'xlsxwriter')

    # For each data frame
    for frame_name in data:
        # Skip first sheet with mouse ID
        if 'Cage ID' in data[frame_name].columns:
            continue
        else:
            print(f"Mouse ID: {frame_name}")
            raw_data = data[frame_name].set_index('Time')
            aggregate_frame, trial_frame, bout_frame = func(raw_data, mode)
            aggregate_frame.to_excel(writer, sheet_name = f'{frame_name} Test Stats', header = False)
            trial_frame.to_excel(writer, sheet_name = f'{frame_name} Trial Stats')
            bout_frame.to_excel(writer, sheet_name = f'{frame_name} Bouts', index = False)   
    # Close excel writer
    writer.close()

modes = ['reward', 'time']

# Run phase 1
data_folder = Path('parsed_data')
phase1_files = (data_folder / 'phase 1').glob('phase*.xlsx')
for file in phase1_files:
    for mode in modes:
        print(f"Processing Arduino file: {file}, Mode: {mode}")
        phase_stats(file, mode, phase1)

# Run phase 2
phase2_files = (data_folder / 'phase 2').glob('phase*.xlsx')
for file in phase2_files:
    for mode in modes:
        print(f"Processing Arduino file: {file}, Mode: {mode}")
        phase_stats(file, mode, phase2)

# Run phase 3
phase3_files = (data_folder / 'phase 3').glob('phase*.xlsx')
for file in phase3_files:
    for mode in modes:
        print(f"Processing Arduino file: {file}, Mode: {mode}")
        phase_stats(file, mode, phase3)
