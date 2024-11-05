# Operant Training Analysis
The following scripts are for analyzing Arduino and calcium fiber photometry data from operant training experiments with mice. They have been listed in the order in which they need to be run.

## Arduino Code
### `gustometer_prime_water.ino`
This code primes the spout to deliver sucrose and empties the tubing after the experiments to prevent sucrose buildup.

### `phase1.ino`
This code plays a tone for 5 seconds every 20 seconds. If the mouse licks the spout during this time, a defined amount of solution is released. The data is synchronized with the photometry system, which is also activated by the start input. The code provides information on cue ON and OFF times, trial numbers, records each lick, and indicates whether a reward was given during the lick.

### `phase2.ino`
This code records the force applied to the lever and sets a threshold to release the spout. If the mouse licks the spout during this time, a defined amount of solution is dispensed. The data is synchronized with the photometry system, which is also activated by the start input. The code provides information on ON and OFF times after each lever press, trial numbers (press numbers), records each lick, and indicates whether a reward was given during the lick.

### `phase3.ino`
This code plays a tone for 5 seconds every 10 seconds and records the force applied to the lever and sets a threshold to release the spout. If the mouse licks the spout during this time, a defined amount of solution is released. The data is synchronized with the photometry system, which is also activated by the start input. The code provides information on cue ON and OFF times, trial numbers, records each lick, and indicates whether a reward was given during the lick.

## Arduino Data Analysis
### `arduino_log_parse.py`
Parses Arduino logs into a human-readable format.
- Input: an Excel file containing multiple sheets. Each sheet should be marked by a specific mouse ID and test number and contain a single column of information with the Arduino log.
- Output: a new Excel file exported to a `parsed_data/` folder with the parsed log sorted by the sheet name. The columns in the parsed log will vary depending on the specific phase of the experiment (e.g. phase 1, phase 2, phase 3).

### `phase_stats.py`
Compute basic statistics about the operant tasks.
- Input: a parsed Arduino log file outputted from `arduino_log_parse.py` in the `parsed_data/` folder
- Output: a new Excel file exported to a `stats/` folder. For each mouse test, the file contains three corresponding sheets named `${mouse_id} Test Stats`, `${mouse_id} Trial Stats`, and `${mouse_id} Bouts` containing statistics about the latency to first lick, number of lever presses, number of licks (grouped by rewarding and non-rewarding), and bout start/end times.
- it gives two options of outputs, one based on Time (splititng by time) and one based on confirmation of receiving of the reward. The latter is recommended but they are mostly interchangeable. 

### `compare_modes.py` (Optional)
Compare the difference in statistics between using "reward" mode (i.e. using the REWARD column to sort rewarding/non-rewarding licks) and "time" mode (i.e. using the experiment cue duration to sort rewarding/non-rewarding licks).
- Input: two Excel stat files generated from `phase_stats.py` in the `stats/` folder, one in "reward" mode and one in "time" mode
- Output: a new Excel file exported  to the `stats/` folder containing the difference between the two files. All sheet names are retained. 

## Calcium Data Analysis
### `calcium_data_synchronize.py`
Synchronize the time scale of the calcium data with the corresponding Arduino log.
- Input: a parsed Arduino log file (outputted from `arduino_log_parse.py`) in the `parsed_data/` folder and a raw calcium data CSV file. The calcium file should have two columns named "Time" and "AIN01" (sometims "Values" -- Old Doric system)
- Output: a new Excel file exported to the `parsed_data/` folder, with the calcium data split into individual trials and stored on separate sheets as `Trial {trial_num}`
- it also downsamples and adds the Calcium trace to the arduino file (so it is easier to correlate with force for phase 2 and phase 3)

### `calcium_trial_export.py`
For each trial in calcium data, combines the last 2 seconds of the previous trial and the first 8 seconds of the current trial. Saves all trials into one file
- Input: the Excel file exported to the `parsed_data/` folder, with the calcium data split into individual trials and stored on separate sheets as `{File name} Trial {trial_num}`
- Output: a new Excel file with all the trials from all calcium files

### `calcium_trial_plots.py`
For each trial in calcium data generates a line plot that indicates start of trial (tone or lever press) with rewarded and non-rewarded licks and appropriate shading for reward availability
- Input: a parsed Arduino file in the `parsed_data/` and a parsed calcium file in the `parsed_data/` folder.`
- Output: PNG files exported in the `plots/` folder. 
- 
### `calcium_bout_export.py`
Export the calcium data for lick bouts identified in each test.
- Input: an Arduino stats file in the `stats/` folder and a parsed calcium file in the `parsed_data/` folder.
- Output: a calcium data Excel file exported to the `stats/` folder, with bouts stored on additional sheets as `Bout {bout_num}`.

### `calcium_bout_analysis.py`
Analyze the calcium data for each lick bout, using customized metrics such as the AUC, pre-bout calcium slope, pre-bout calcium "exponential rate", and the max observed calcium.
- Input: an Arduino stats file in the `stats/` folder and a parsed calcium file in the `parsed_data/` folder.
- Output: an **updated** Arduino stats Excel file exported to the same input path in the `stats/` folder, with new columns ("AUC Metric", "Pre-Bout Calcium Slope", "Pre-Bout Calcium ExpRate", and "Max Calcium") for each analyzed metric.

### `calcium_bout_plots.py`
Create a variety of line and scatter plots based on the calcium data for each bout and the analyzed metrics.
- Input: a parsed Arduino file in the `parsed_data/` folder, an Arduino stats file in the `stats/` folder, and a parsed calcium file in the `parsed_data/` folder.
- Output: PNG files exported in the `plots/` folder. 

## Helper Files
### `phase_utils.py`
Contains various helper functions used in several scripts, such as filtering data based on time ranges and splitting licks into rewarding/non-rewarding categories.
