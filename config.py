# project paths, change base/code to your own directories

import getpass
import platform
from pathlib import Path


def get_paths() -> dict:
    # get project paths based on current environment
    user = getpass.getuser()
    system = platform.system()
    
    # environment-specific base paths
    if user == "user_a" and system == "Linux":
        base = "/path/to/QUANTUM_4S"
        code = "/path/to/code"
    elif user == "user_b":
        base = "/path/to/QUANTUM_4S"
        code = "/path/to/code"
    elif user == "user_c":
        base = "/path/to/code"
        code = base
    elif user == "user_a" and system == "Darwin":
        base = "/path/to/code"
        code = base
    else:
        raise ValueError(f"Unknown environment: user={user}, system={system}")
    
    paths = {
        "base_dir": Path(base),
        "code_dir": Path(code),
        "model_file_dir": Path(base) / "GLM_1Ds",
        "csv_dir": Path(base) / "CSVs",
        "fig_dir": Path(code) / "figures",
    }
    
    # make output directories
    paths["fig_dir"].mkdir(parents=True, exist_ok=True)
    
    return paths