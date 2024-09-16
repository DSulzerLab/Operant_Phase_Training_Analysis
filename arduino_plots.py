from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Create plots for parsed data
def plots(path: Path):
    # Import parsed data
    file_name = path.with_name(f'{path.stem}-parsed{path.suffix}')
    data = pd.read_excel(file_name, sheet_name = None)

    # Make images directory
    images_dir = Path('images/')
    images_dir.mkdir(parents = True, exist_ok = True)

    # For each data frame
    for frame_name in data:
        # Skip first sheet with mouse ID
        if 'Cage ID' in data[frame_name].columns:
            continue
        else:
            # Retrieve time, force, and lever press data
            raw_data = data[frame_name]
            time = raw_data['Time']
            force = raw_data['Force'].clip(lower = 0.0) # Clipping negative values to 0
            presses = raw_data['Lever Press']
            
            # Get non-null lever press times
            press_times = presses[presses.notna()].index.to_numpy()
            press_times[force[press_times].isna()] -= 1 # Moving index one position before if force reading is NaN

            # Create plot
            plt.figure()
            plt.plot(time, force, color = '#218BFF')
            plt.scatter(time[press_times], force[press_times], marker = 'x', color = '#DD7815', label = 'Lever Press')
            plt.xlabel('Time (ms)')
            plt.ylabel('Force (g)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(images_dir / f'{path.stem}-{frame_name}.png', dpi = 600)
            plt.close()
