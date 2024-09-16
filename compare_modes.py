from pathlib import Path
import pandas as pd

def main(folder: Path):
    files = folder.glob('*reward.xlsx')
    for file in files:
        name = file.stem.split('-')[0]
        writer = pd.ExcelWriter(folder / f'{name}-diff.xlsx', engine = 'xlsxwriter')
        sheets = pd.read_excel(folder / f'{name}-reward.xlsx', sheet_name = None).keys()
        sheets = [x for x in sheets if 'Bouts' not in x]
        for key in sheets:
            if 'Test' in key:
                header = None
                export = False
            else:
                header = 0
                export = True
            reward_frame = pd.read_excel(folder / f'{name}-reward.xlsx', sheet_name = key, index_col = 0, header = header)
            time_frame = pd.read_excel(folder / f'{name}-time.xlsx', sheet_name = key, index_col = 0, header = header)
            diff = reward_frame.fillna(0).subtract(time_frame, fill_value = 0)
            diff.to_excel(writer, sheet_name = key, header = export)
        writer.close()

for i in range(3):
    phase = Path(f'stats/phase {i + 1}')
    main(phase)
