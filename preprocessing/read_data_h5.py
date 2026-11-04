#!/bin/python
import h5py
import numpy as np

base_dir="/path/to/QUANTUM_4S"
f = h5py.File(f"{base_dir}/data.h5","r")

# context prediction error from the model, averaged over posterior samples
cpe1 = np.mean(f["cpe"],axis=1)

idx = f["idx"][:]                    # (14, 20, 40)
idx_flat = idx.flatten()
cpe1 = cpe1.flatten()
order = np.argsort(idx_flat)

result = np.column_stack([idx_flat[order], cpe1[order]])
print(result.shape)

np.savetxt('cpe_data.csv', result, delimiter=',', header='idx,cpe1', comments='')
