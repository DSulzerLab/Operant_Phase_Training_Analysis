from pathlib import Path
import pandas as pd

from phase_utils import filter_range

# Export calcium data corresponding to individual bouts 
def main(arduino_stats: Path, sheet: str, calcium: Path):
    # Import bout statistics and calcium data
    mouse_stats = pd.read_excel(arduino_stats, sheet_name = f'{sheet} Bouts')
    calcium_data = pd.read_excel(calcium, sheet_name = None, index_col = 'Time')

    # Set up output directories and file
    writer = pd.ExcelWriter(calcium, engine = 'openpyxl', mode = 'a')

    # For each bout
    for index, bout in mouse_stats.iterrows():
        # Retrieve corresponding calcium data for trial
        trial_num = int(bout['Trial Number'])
        if trial_num > 0:
            trial_calcium = calcium_data[f'Trial {trial_num}']
        else:
            trial_calcium = calcium_data[f'Pre-Trial']

        # Get calcium data for specific bout 
        # Include 0.5s before and 0.5s after
        bout_calcium = filter_range(trial_calcium, [bout['Start'] - 0.5, bout['End'] + 0.5])

        # Export to separate Excel sheet
        bout_calcium.reset_index().to_excel(writer, sheet_name = f'Bout {index + 1}', index = False)
    
    writer.close()

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
