from pathlib import Path
import pandas as pd
import numpy as np

# Helper function to find the closest index
def find_closest_index(data, target):
    closest_index = data.index.get_indexer([target], method='nearest')[0]
    return data.index[closest_index]

# Synchronize Arduino and calcium timelines and split calcium data by experiment trials
def main(arduino: Path, sheet: str, calcium: Path):
    try:
        # Import Arduino log and calcium trace data
        arduino_data = pd.read_excel(arduino, index_col='Time', sheet_name=sheet)
        calcium_data = pd.read_csv(calcium, index_col='Time')

        # Downsample calcium data using interpolation to match the length of Arduino data
        arduino_indices = arduino_data.index.values
        calcium_indices = calcium_data.index.values
        downsampled_calcium = np.interp(arduino_indices, calcium_indices, calcium_data['AIN01'])

        # Append the downsampled calcium data as a new column in Arduino data
        arduino_data['Calcium'] = downsampled_calcium

        # Save the updated Arduino data with downsampled calcium
        with pd.ExcelWriter(arduino, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            arduino_data.to_excel(writer, sheet_name=sheet)

        # Create Excel file for calcium data
        dir_tree = list(calcium.parts)
        dir_tree[0] = 'parsed_data'
        new_calcium = Path(*dir_tree).with_suffix('.xlsx')
        writer = pd.ExcelWriter(new_calcium)

        # Split calcium data by trial based on cue time
        cues = arduino_data['Cue'].dropna()
        cue_on = cues[cues == 'On']
        for i in range(cue_on.shape[0]):
            # Find the closest index for each cue
            start = find_closest_index(calcium_data, cue_on.index[i])
            end = find_closest_index(calcium_data, arduino_data.index[-1]) if i == cue_on.shape[0] - 1 else find_closest_index(calcium_data, cue_on.index[i + 1])

            # Save pre-trial calcium data with both 'Time' and 'Original_Time' columns
            if i == 0:
                pre_trial_data = calcium_data.loc[:start].copy()
                pre_trial_data['Original_Time'] = pre_trial_data.index  # Keep the original time
                pre_trial_data.index = pre_trial_data.index - pre_trial_data.index[0]  # Reset time to start at 0
                pre_trial_data.reset_index(inplace=True)
                pre_trial_data.rename(columns={'Time': 'Time'}, inplace=True)
                pre_trial_data.to_excel(writer, sheet_name='Pre-Trial', index=False)

            # Save data for each trial with both 'Time' and 'Original_Time' columns
            trial_data = calcium_data.loc[start:end].copy()
            trial_data['Original_Time'] = trial_data.index  # Keep the original time
            trial_data.index = trial_data.index - trial_data.index[0]  # Reset time to start at 0
            trial_data.reset_index(inplace=True)
            trial_data.rename(columns={'Time': 'Time'}, inplace=True)
            trial_data.to_excel(writer, sheet_name=f'Trial {i + 1}', index=False)

        writer.close()

    except Exception as e:
        print(f"Error processing sheet '{sheet}' in file '{arduino}': {e}")

# Main function to process Arduino files
def process_all():
    arduino_dir = Path('parsed_data')
    calcium_dir = Path('original_calcium_data')

    # Iterate through each phase folder in the Arduino data directory
    for phase_folder in arduino_dir.glob('phase *'):
        phase = phase_folder.name.split()[-1]

        # Iterate through each Arduino file in the phase folder
        for arduino_file in phase_folder.glob('*.xlsx'):
            try:
                # Extract the day from the Arduino filename
                day = arduino_file.stem.split()[-1]

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

            except Exception as e:
                print(f"Error processing Arduino file '{arduino_file}': {e}")
                continue  # Safely move to the next file if an error occurs

if __name__ == "__main__":
    process_all()
