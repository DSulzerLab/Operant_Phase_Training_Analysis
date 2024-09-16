import numpy as np
import pandas as pd

# Filter data in given range
def filter_range(data: pd.Series | pd.DataFrame, time_range: list[float | int] | None):
    if time_range == None: # No changes if range not specified
        return data
    
    # Return data within range
    if time_range[1] == None:
        return data[data.index >= time_range[0]]
    elif time_range[0] == None:
        return data[data.index <= time_range[1]]
    else:
        return data[(data.index >= time_range[0]) & (data.index <= time_range[1])]

# Find index of values in A closest to values in B
# Used in functions for finding reward closest to licks, etc.
def find_closest(a: pd.Index, b: pd.Index):
    data_index = []
    for x in b:
        diff = x - a
        pos_diff = diff[diff >= 0]
        if pos_diff.shape[0] == 0:
            diff = np.abs(diff)
            data_index.append(np.argmin(diff))
        else:
            data_index.append(np.where(diff == np.min(pos_diff))[0][0])
    
    return data_index

# Given list of data and cues
# Compute # of data points within and outside cue trigger
def cue_split(cues: pd.Series, data: pd.Series):
    # Split cues by On and Off
    cue_on = cues[cues == 'On']
    cue_off = cues[cues == 'Off']

    # Get time indices
    cue_on_times = cue_on.index
    cue_off_times = cue_off.index
    data_times = data.index

    # Find closest cue to each data point
    data_cue_index = find_closest(cue_on_times, data_times)

    # Find difference between data time and cue on/off time
    data_on_diff = data_times - cue_on_times[data_cue_index]
    data_off_diff = data_times - cue_off_times[data_cue_index]
    
    # Split data into in/out of cue
    data_mask = (data_on_diff >= 0) & (data_off_diff <= 0)
    data_in_cue = data.loc[data_mask]
    data_out_cue = data.loc[~data_mask]
    
    return data_in_cue, data_out_cue, cue_on

# Given rewarded/not rewarded licks or presses
# Compute general stats
def ratio_stats(
    pos_data: pd.Series, 
    neg_data: pd.Series, 
    time_range: list[float] | None = None
):
    # Filter data
    pos_data = filter_range(pos_data, time_range)
    neg_data = filter_range(neg_data, time_range)

    # Compute stats
    num_pos = pos_data.sum()
    num_neg = neg_data.sum()
    total = num_pos + num_neg

    return num_pos, num_neg, total

# Given rewarded licks, trials, and presses (optional)
# Compute latency to first lick
def latency_to_first_lick(
    licks_rewarded: pd.Series,
    time: int | None = None,
    trials: pd.Series | None = None, 
    presses: pd.Series | None = None,
    time_range: list[float] | None = None
):
    # Filter by time range
    licks_rewarded = filter_range(licks_rewarded, time_range)

    # If no rewarded licks
    if licks_rewarded.shape[0] == 0:
        latency = 'N/A'
    else:
        # Get time of first lick
        first_lick = licks_rewarded.index[0]

        # If time is given, compute latency with respect to start of test
        if time is not None:
            latency = first_lick - time

        # If trials are given, compute latency with respect to start of trial
        elif trials is not None:
            # Get trial number of first lick
            trial_num = trials.loc[first_lick]

            # Get start time of corresponding trial
            trials_start = trials.drop_duplicates()
            trial_num_start = trials_start[trials_start == trial_num]

            # Compute latency from trial start to first lick
            latency = first_lick - trial_num_start.index[0]
        
        # If presses are given, compute latency with respect to first press
        elif presses is not None:
            presses = filter_range(presses, time_range)
            if presses.shape[0] == 0:
                latency = 'N/A'
            else:
                start_press = presses.index[0]
                latency = first_lick - start_press
    
    return latency

# Given presses and cues
# Compute latency to first press
def latency_to_first_press(
    presses: pd.Series,
    time: int | None = None,
    cues: pd.Series | None = None,
    time_range: list[float] | None = None
):
    # Filter by time range
    presses = filter_range(presses, time_range)

    # If no presses
    if presses.shape[0] == 0:
        latency = 'N/A'
    else:
        # Get time of first press
        first_press = presses.index[0]

        # If time is given, compute latency with respect to start of test
        if time is not None:
            latency = first_press - time
        
        # If cues are given, compute latency with respect to start of cue
        if cues is not None:
            cues = filter_range(cues, time_range)
            start_time = cues.index[0]
            latency = first_press - start_time
    
    return latency

# Given list of licks and rewards
# Compute # of rewarded and non-rewarded licks
def lick_reward_split(rewards: pd.Series, licks: pd.Series):
    reward_times = rewards.index
    lick_times = licks.index

    # For each reward time, find the closest lick index
    # Extract the corresponding indices from the lick times
    lick_reward_index = find_closest(lick_times, reward_times)
    lick_reward_times = lick_times[lick_reward_index] 
    
    # Split licks into received reward vs not received reward
    licks_rewarded = licks.loc[lick_reward_times]
    licks_not_rewarded = licks.loc[lick_times.difference(lick_reward_times)]

    return licks_rewarded, licks_not_rewarded

# Given list of presses and licks
# compute licks that are within reward period (denoted by threshold)
def lick_press_split(presses: pd.Series, licks: pd.Series, threshold: int = 5000):
    # Get time indices
    press_times = presses.index
    lick_times = licks.index
    
    # Find closest press to each lick
    if presses.shape[0] > 0:
        lick_press_index = find_closest(press_times, lick_times)
        
        # Find difference between lick and press times
        lick_diff = lick_times - press_times[lick_press_index]

        # Split licks into rewarded/not rewarded
        lick_mask = (lick_diff >= 0) & (lick_diff <= threshold)
        licks_rewarded = licks[lick_mask]
        licks_not_rewarded = licks[~lick_mask]
    else:
        licks_rewarded = pd.Series()
        licks_not_rewarded = licks.copy()
    
    return licks_rewarded, licks_not_rewarded
