import pandas as pd
from pathlib import Path

# Define input and output paths. Adjust accordingly phase by phase
input_folder = Path('parsed_data/phase 1')
output_file = Path('parsed_data/all_trials_phase_1.xlsx')

# Get a list of all Excel files in the input folder
calcium_files = list(input_folder.glob('*.xlsx'))

# Loop through each calcium file in the folder
for calcium_file in calcium_files:
    calcium_path = calcium_file

    # Get the file name without the extension
    calcium_file_base = calcium_file.stem

    # Read the Excel file
    xls = pd.ExcelFile(calcium_path)

    # Read the existing output file if it exists, else create an empty DataFrame
    if output_file.exists():
        existing_data = pd.read_excel(output_file)
    else:
        existing_data = pd.DataFrame()

    # Create a list to store the data for each sheet
    all_data = []

    # Ignore the first sheet 'Pre-Trial'
    sheet_names = [sheet for sheet in xls.sheet_names if sheet != 'Pre-Trial']

    # Process each sheet
    for i, sheet_name in enumerate(sheet_names):
        current_sheet = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Check if previous sheet exists (not for 'Trial 1')
        if i == 0:
            # For the first sheet ('Trial 1'), leave the first 244 samples as blank
            previous_samples = pd.Series([pd.NA] * 244)
        else:
            # For subsequent sheets, take the last 244 samples from 'AIN01' of the previous sheet
            previous_sheet = pd.read_excel(xls, sheet_name=sheet_names[i-1])
            previous_samples = previous_sheet['AIN01'].iloc[-244:]
        
        # Get the first 976 samples from 'AIN01' of the current sheet
        current_samples = current_sheet['AIN01'].iloc[:976]
        
        # Concatenate the previous samples and current samples
        combined_samples = pd.concat([previous_samples, current_samples], ignore_index=True)
        
        # Add to the list as a DataFrame with a column name as specified
        all_data.append(pd.DataFrame({f'{calcium_file_base}_{sheet_name}': combined_samples}))

    # Combine all sheet data side by side
    new_data = pd.concat(all_data, axis=1)

    # Concatenate the new data next to any existing data
    if not existing_data.empty:
        output_df = pd.concat([existing_data, new_data], axis=1)
    else:
        output_df = new_data

    # Save the final DataFrame to the output Excel file
    output_df.to_excel(output_file, index=False)

print(f"Data successfully written to {output_file}")
