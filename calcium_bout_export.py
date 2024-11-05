from pathlib import Path
import pandas as pd
from phase_utils import filter_range

# Export calcium data corresponding to individual bouts
def main(arduino_stats: Path, sheet: str, calcium: Path, output_file: Path):
    try:
        # Import bout statistics and calcium data
        try:
            mouse_stats = pd.read_excel(arduino_stats, sheet_name=f'{sheet} Bouts')
        except ValueError:
            print(f"Worksheet '{sheet} Bouts' not found in {arduino_stats}. Skipping this sheet.")
            return  # Skip to the next sheet

        try:
            calcium_data = pd.read_excel(calcium, sheet_name=None, index_col='Original_Time')
        except FileNotFoundError:
            print(f"Calcium data file '{calcium}' not found. Skipping this file.")
            return  # Skip to the next file

        # Set up the new output file writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # For each bout
            for index, bout in mouse_stats.iterrows():
                # Retrieve corresponding calcium data for trial
                trial_num = int(bout['Trial Number'])
                if trial_num > 0:
                    trial_calcium = calcium_data.get(f'Trial {trial_num}')
                else:
                    trial_calcium = calcium_data.get('Pre-Trial')

                # Check if trial_calcium exists before processing
                if trial_calcium is None:
                    print(f"Trial {trial_num} not found in calcium data for {sheet}. Skipping bout {index + 1}.")
                    continue

                # Use the original timestamps for filtering
                start_time = bout['Start']
                end_time = bout['End']

                # Get calcium data for specific bout (±0.5 seconds), ensuring timestamps are retained
                bout_calcium = filter_range(trial_calcium, [start_time - 0.5, end_time + 0.5])

                # Export each bout to a separate sheet in the new file
                bout_calcium.reset_index().to_excel(writer, sheet_name=f'Bout {index + 1}', index=False)

    except Exception as e:
        print(f"An error occurred while processing {sheet} in {arduino_stats}: {e}. Skipping this sheet.")

# Path to the directories containing the Arduino and calcium data
arduino = Path('parsed_data')
arduino_stats = Path('stats')
calcium = Path('parsed_data')

# Iterate through each phase folder in the Arduino data directory
for phase_folder in arduino.glob('phase *'):
    phase = phase_folder.name.split()[-1]

    # Iterate through each Arduino file in the phase folder
    for arduino_file in phase_folder.glob('phase*.xlsx'):
        # Load the Excel file to get the sheet names (mouse IDs)
        with pd.ExcelFile(arduino_file) as xls:
            sheets = xls.sheet_names

        # Iterate through each sheet name (mouse ID) in the Arduino file
        for sheet in sheets:
            # Construct the corresponding calcium file path
            calcium_file = calcium / f'phase {phase}' / f'{sheet}.xlsx'
            
            # Check if the calcium file exists before processing
            if calcium_file.exists():
                arduino_stats_file = arduino_stats / f'phase {phase}' / f'{arduino_file.stem}-reward.xlsx'
                output_file = arduino_stats / f'phase {phase}' / f'{sheet}_bouts.xlsx'
                
                print(f"Processing Arduino file: {arduino_stats_file}, Sheet: {sheet}, Calcium file: {calcium_file}")
                
                # Call main function with output file specified
                main(arduino_stats_file, sheet, calcium_file, output_file)
            else:
                print(f"Calcium file not found for {sheet} in phase {phase}. Skipping.")
