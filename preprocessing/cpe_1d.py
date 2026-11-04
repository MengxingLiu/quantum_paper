import pandas as pd
import os

def generate_1d_files(df):
    """
    Generate 1D files for each subject and session.
    Each file has 5 rows (one per block), with CPE values.
    """
    # os.makedirs(output_dir, exist_ok=True)
    
    # Group by subject and session
    for (subid, session_id), group in df.groupby(['subid', 'ses']):
        # Collect CPE values for each block
        rows = []
        for block_id in sorted(group['block'].unique()):
            block_data = group[group['block'] == block_id]
            cpe_values = block_data['cpe1'].values
            # Convert to space-separated string
            row_str = ' '.join(map(str, cpe_values))
            rows.append(row_str)
        output_dir=f'/path/to/QUANTUM_4S/GLM_1Ds/sub-{subid}/ses-{session_id}/'
        # Write to 1D file
        filename = f"cpe.1D"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write('\n'.join(rows))
        
        print(f"Created: {filepath}")

df = pd.read_csv("/path/to/QUANTUM_4S/GLM_1Ds/df_beh.csv")
# Usage
generate_1d_files(df)
