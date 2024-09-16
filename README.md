# Operant Phase Training Analysis
The following scripts are for analyzing Arduino and calcium fiber photometry data from operant training experiments with mice. They have been listed in the order in which they need to be run.

## Arduino Data Analysis
### `arduino_log_parse.py`
Parses Arduino logs into a human-readable format.
- Input: an Excel file containing multiple sheets. Each sheet should be marked by a specific mouse ID and test number and contain a single column of information with the Arduino log.
- Output: a new Excel file exported to a `parsed_data/` folder with the parsed log sorted by the sheet name. The columns in the parsed log will vary depending on the specific phase of the experiment (e.g. phase 1, phase 2, phase 3).

### `phase_stats.py`
Compute basic statistics about the operant tasks.
- Input: a parsed Arduino log file outputted from `arduino_log_parse.py` in the `parsed_data/` folder
- Output: a new Excel file exported to a `stats/` folder. For each mouse test, the file contains three corresponding sheets named `${mouse_id} Test Stats`, `${mouse_id} Trial Stats`, and `${mouse_id} Bouts` containing statistics about the latency to first lick, number of lever presses, number of licks (grouped by rewarding and non-rewarding), and bout start/end times.

### `compare_modes.py` (Optional)
Compare the difference in statistics between using "reward" mode (i.e. using the REWARD column to sort rewarding/non-rewarding licks) and "time" mode (i.e. using the experiment cue duration to sort rewarding/non-rewarding licks).
- Input: two Excel stat files generated from `phase_stats.py` in the `stats/` folder, one in "reward" mode and one in "time" mode
- Output: a new Excel file exported  to the `stats/` folder containing the difference between the two files. All sheet names are retained. 

## Calcium Data Analysis
### `calcium_data_synchronize.py`
Synchronize the time scale of the calcium data with the corresponding Arduino log.
- Input: a parsed Arduino log file (outputted from `arduino_log_parse.py`) in the `parsed_data/` folder and a raw calcium data CSV file. The calcium file should have two columns named "Time" and "Values"
- Output: a new Excel file exported to the `parsed_data/` folder, with the calcium data split into individual trials and stored on separate sheets as `Trial {trial_num}`

### `calcium_bout_export.py`
Export the calcium data for lick bouts identified in each test.
- Input: an Arduino stats file in the `stats/` folder and a parsed calcium file in the `parsed_data/` folder.
- Output: an **updated** calcium data Excel file exported to the same input path in the `parsed_data/` folder, with bouts stored on additional sheets as `Bout {bout_num}`.

### `calcium_bout_analysis.py`
Analyze the calcium data for each lick bout, using customized metrics such as the AUC, pre-bout calcium slope, pre-bout calcium "exponential rate", and the max observed calcium.
- Input: an Arduino stats file in the `stats/` folder and a parsed calcium file in the `parsed_data/` folder.
- Output: an **updated** Arduino stats Excel file exported to the same input path in the `stats/` folder, with new columns ("AUC Metric", "Pre-Bout Calcium Slope", "Pre-Bout Calcium ExpRate", and "Max Calcium") for each analyzed metric.

### `calcium_bout_plots.py`
Create a variety of line and scatter plots based on the calcium data for each bout and the analyzed metrics.
- Input: a parsed Arduino file in the `parsed_data/` folder, an Arduino stats file in the `stats/` folder, and a parsed calcium file in the `parsed_data/` folder.
- Output: PNG files exported in the `plots/` folder. 

### `calcium_trial_plots.py`
Create a variety of line plots based on the original calcium data for each trial.
- Input: a parsed Arduino file in the `parsed_data/` and a parsed calcium file in the `parsed_data/` folder.
- Output: PNG files exported in the `plots/` folder. 

## Helper Files
### `phase_utils.py`
Contains various helper functions used in several scripts, such as filtering data based on time ranges and splitting licks into rewarding/non-rewarding categories.

