from pathlib import Path
import pandas as pd

from phase_utils import filter_range

# Synchronize Arduino and calcium timelines
# and split calcium data by experiment trials
def main(arduino: Path, sheet: str, calcium: Path):
    # Import Arduino log and calcium trace data
    arduino_data = pd.read_excel(arduino, index_col = 'Time', sheet_name = sheet)
    calcium_data = pd.read_csv(calcium, index_col = 'Time')
    
    # NOTE: better approach is needed (i.e. synchronizing by CUE ON or REWARD)
    # Create Excel file for calcium data
    dir_tree = list(calcium.parts)
    dir_tree[0] = 'parsed_data'
    new_calcium = Path(*dir_tree).with_suffix('.xlsx')
    writer = pd.ExcelWriter(new_calcium)

    # Splt calcium data by trial based on cue time
    cues = arduino_data['Cue'].dropna()
    cue_on = cues[cues == 'On']
    for i in range(cue_on.shape[0]):
        # Save pre-trial calcium data in separate sheet
        if i == 0:
            data = filter_range(calcium_data, [None, cue_on.index[i]])
            data.reset_index().to_excel(writer, sheet_name = 'Pre-Trial', index = False)
        
        # Save data for each trial in sheet
        start = cue_on.index[i]
        if i == cue_on.shape[0] - 1:
            end = arduino_data.index[-1] # Truncate data to end of test 
        else:
            end = cue_on.index[i + 1]
        data = filter_range(calcium_data, [start, end])
        data.reset_index().to_excel(writer, sheet_name = f'Trial {i + 1}', index = False)
    
    writer.close()

# Path to the directories containing the Arduino and calcium data
arduino_dir = Path('parsed_data')
calcium_dir = Path('original_data')

# Iterate through each phase folder in the Arduino data directory
for phase_folder in arduino_dir.glob('phase *'):
    phase = phase_folder.name.split()[-1]

    # Iterate through each Arduino file in the phase folder
    for arduino_file in phase_folder.glob('*.xlsx'):
        # Load the Excel file to get the sheet names (mouse IDs)
        with pd.ExcelFile(arduino_file) as xls:
            sheets = xls.sheet_names

        # Iterate through each sheet name (mouse ID) in the Arduino file
        for sheet in sheets:
            # Construct the corresponding calcium file path
            calcium_file = calcium_dir / f'phase {phase}' / f'{sheet}.csv'
            
            # Check if the calcium file exists before processing
            if calcium_file.exists():
                print(f"Processing Arduino file: {arduino_file}, Sheet: {sheet}, Calcium file: {calcium_file}")
                main(arduino_file, sheet, calcium_file)
            else:
                print(f"Calcium file not found for {sheet} in phase {phase}")
