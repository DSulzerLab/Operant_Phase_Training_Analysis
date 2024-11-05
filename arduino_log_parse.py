from pathlib import Path
import pandas as pd
import numpy as np

# these are the items listed in the output of the Arduino code. If you make changes to the Arduino code, adjust this accordingly.
key_list = ['Time', 'Force', '# of Licks', 'Trial Number', 'Port', 'Cue', 'Lever Press', 'Syncs', 'Servos', 'Reward']

# Parse log information from Arduino into multiple columns
def parse_data(path: Path):
    # Import data
    data = pd.read_excel(path, sheet_name = None)

    # Create ExcelWriter for output file
    dir_tree = list(path.parts[:-1])
    dir_tree[0] = 'parsed_data'
    output_dir = Path(*dir_tree)
    output_dir.mkdir(parents = True, exist_ok = True)
    file_name = output_dir / f'{path.stem}.xlsx'
    writer = pd.ExcelWriter(file_name, engine = 'xlsxwriter')
    
    # This is based on the way we organized the data. For each output file we have one file per animal (with animal ID on first sheet) and one sheet per test/day
    for frame_name in data:
        # Skip first sheet with mouse ID
        if 'Animal ID' in data[frame_name].columns:
            data[frame_name].to_excel(writer, sheet_name = frame_name, index = False)
        else:
            # Create formatted frame for dictionary
            keys = key_list.copy()
            parsed_data = {}
            for key in keys:
                parsed_data.setdefault(key, [])
            
            # Parse each row of raw data
            if not data[frame_name].empty:
                raw_data = data[frame_name].iloc[:, 0].to_list()
                latest_trial_num = 0
                for row in raw_data:
                    # Split string into individual components
                    row_parts = row.split(',')
                    
                    # Extract time (in ms) if exists
                    if 'ms' in row_parts[-1]:
                        data_time = int(row_parts[-1].split('=')[-1].rstrip())
                        
                        # Check if new row needs to be added for time
                        if len(parsed_data['Time']) > 0:
                            if parsed_data['Time'][-1] != data_time:
                                # If more rows exist, fill in blank strings for unfilled columns
                                for key in keys:
                                    parsed_data[key].append('')
                                keys = key_list.copy()
                                parsed_data['Time'].append(data_time)
                                keys.remove('Time')
                        else:
                            parsed_data['Time'].append(data_time)
                            keys.remove('Time')
                        row_parts.pop(-1)
                    else:
                        if 'bout' not in row:
                            continue
                    
                    # Parse other parts of row
                    for part in row_parts:
                        if part == 'syncOut': # Sync notifications
                            if 'Syncs' in keys:
                                parsed_data['Syncs'].append('TRUE')
                                keys.remove('Syncs')
                        elif 'g' in part:
                            force = np.round(float(part.split('=')[-1].rstrip()), 2)
                            parsed_data['Force'].append(force)
                            keys.remove('Force')
                        elif 'trialNum' in part: # Trial number
                            latest_trial_num = int(part.split('=')[-1].rstrip())
                            if 'Trial Number' in keys:
                                parsed_data['Trial Number'].append(latest_trial_num)
                                keys.remove('Trial Number')
                        elif 'port' in part: # Port number
                            port = int(part.split('=')[-1].rstrip())
                            if 'Port' in keys:
                                parsed_data['Port'].append(port)
                                keys.remove('Port')
                        elif 'cue' in part: # Cue triggers
                            cue_status = part[3:]
                            if 'Cue' in keys:
                                parsed_data['Cue'].append(cue_status)
                                keys.remove('Cue')
                            if 'Trial Number' in keys:
                                parsed_data['Trial Number'].append(latest_trial_num)
                                keys.remove('Trial Number')
                        elif part == 'levPress': # Lever Press
                            if 'Lever Press' in keys:
                                parsed_data['Lever Press'].append(1)
                                keys.remove('Lever Press')
                        elif part == 'moveServo': # Servo motion
                            if 'Servos' in keys:
                                parsed_data['Servos'].append('TRUE')
                                keys.remove('Servos')
                        elif 'lick' in part: # Spout licks
                            if 'bout' in part:
                                num_licks = int(part.split(' ')[0])
                                parsed_data['# of Licks'][-1] = num_licks
                            else:
                                parsed_data['# of Licks'].append(1)
                                keys.remove('# of Licks')
                        elif part == 'REWARD': # Reward notification
                            parsed_data['Reward'].append('TRUE')
                            keys.remove('Reward')
            
            # Add blank values for pending keys (if any)
            for key in keys:
                parsed_data[key].append('')

            # Create parsed DataFrame
            parsed_frame = pd.DataFrame(parsed_data)
            if 'phase 1' in file_name.parts:
                parsed_frame.drop(columns = ['Force', 'Lever Press'], inplace = True)

            # Convert time scale from milliseconds to seconds and offset start to 0
            parsed_frame['Time'] /= 1000
            parsed_frame['Time'] -= parsed_frame['Time'][0]
            
            # Export parsed DataFrame
            parsed_frame.to_excel(writer, sheet_name = frame_name, index = False)
    
    # Close excel writer
    writer.close()

# Parse multiple files at once
def main(folder: Path):
    # Get list of files
    files = folder.glob('*.xlsx')

    # For each file
    for file in files:
        # Parse data
        parse_data(file)
        print(f"Completed parsing for {file.stem}")

folders = [x for x in Path('original_data').iterdir() if x.is_dir()]
for folder in folders:
    main(folder)