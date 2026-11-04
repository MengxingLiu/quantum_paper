import argparse
import os
import shutil
import subprocess as sp
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

#### CLI ####
parser = argparse.ArgumentParser(description='Submit jobs to slurm, SGE, or run locally.')
parser.add_argument('configFile', type=str, help='path to the config file')
parser.add_argument('--dry-run', action='store_true',
                    help="Print commands without submitting/running")
args = parser.parse_args()

print('config file:', args.configFile)
with open(args.configFile, 'r') as v:
    cfg = json.load(v)

#### pick cluster profile from active_cluster ####
cluster_name = cfg.get("active_cluster")
if not cluster_name:
    raise ValueError("'active_cluster' must be set in the config file.")
if cluster_name not in cfg["clusters"]:
    raise ValueError(f"active_cluster '{cluster_name}' not in config. "
                     f"Available: {list(cfg['clusters'])}")

cc       = cfg["clusters"][cluster_name]
project  = cfg["project_config"]
defaults = cfg.get("defaults", {})

# merge defaults with cluster overrides (cluster wins)
resolved = {**defaults, **cc}

tool     = project["tool"]
nordic   = project["nordic"]

base_dir     = resolved["base_dir"]
code_dir     = resolved["code_dir"]
tool_dir     = resolved["tool_dir"]
root_dir     = resolved["root_dir"]
queue        = resolved.get("queue")
mem          = resolved["mem_free"]
core         = resolved["core"]
node         = resolved["node"]
time_        = resolved["time"]
account      = resolved.get("account")
exclude      = resolved.get("exclude")
pe_name      = resolved.get("pe_name", "smp")
max_parallel = int(resolved.get("max_parallel", 1))
host         = resolved["scheduler"]

print(f"cluster: {cluster_name}, scheduler: {host}")

# make log/history dirs
os.makedirs(f"{code_dir}/logs", exist_ok=True)
os.makedirs(f"{code_dir}/qsub_history", exist_ok=True)

subseslist = os.path.join(code_dir, "subSesList.txt")
os.chdir(code_dir)
dt = pd.read_csv(subseslist, sep=",", header=0)


#### helpers to build the submit/run command ####
def _env_vars(sub, ses):
    return (f"sub_id={sub},ses_id={ses},code_dir={code_dir},"
            f"base_dir={base_dir},tool_dir={tool_dir},"
            f"root_dir={root_dir},nordic={nordic}")


def build_sge_cmd(sub, ses):
    # SGE: -v KEY=VAL pairs, -l h_rt for walltime
    parts = [
        "qsub",
        f"-q {queue}",
        f"-pe {pe_name} {core}",
        f"-N n-{sub}-{ses}-{tool}",
        f"-l mem_free={mem}",
        f"-l h_rt={time_}",
        f"-o {code_dir}/logs/n-{sub}_{ses}_{tool}_{now}.o",
        f"-e {code_dir}/logs/n-{sub}_{ses}_{tool}_{now}.e",
        f"-v {_env_vars(sub, ses)}",
    ]
    if account:
        parts.append(f"-A {account}")
    parts.append(f"{code_dir}/qsub_base/{tool}_base.sh")
    return " ".join(parts)


def build_slurm_cmd(sub, ses):
    parts = [
        "sbatch",
        f"-p {queue}",
        f"-c {core}",
        f"-N {node}",
        f"-J n-{sub}-{ses}-{tool}",
        f"--mem={mem}",
        f"-t {time_}",
        f"-o {code_dir}/logs/n-{sub}_{ses}_{tool}.o",
        f"-e {code_dir}/logs/n-{sub}_{ses}_{tool}.e",
        f"--export={_env_vars(sub, ses)}",
    ]
    if account:
        parts.append(f"--account={account}")
    if exclude:
        parts.append(f"--exclude={exclude}")
    parts.append(f"{code_dir}/qsub_base/{tool}_base.sh")
    return " ".join(parts)


def build_local_cmd(sub, ses):
    # run base.sh locally with the same env variables as on the cluster
    env_inline = (f"sub_id={sub} ses_id={ses} code_dir={code_dir} "
                  f"base_dir={base_dir} tool_dir={tool_dir} "
                  f"root_dir={root_dir} nordic={nordic}")
    log_o = f"{code_dir}/logs/n-{sub}_{ses}_{tool}_{now}.o"
    log_e = f"{code_dir}/logs/n-{sub}_{ses}_{tool}_{now}.e"
    return (f"{env_inline} bash {code_dir}/qsub_base/{tool}_base.sh "
            f"> {log_o} 2> {log_e}")


builders = {
    "SGE":   build_sge_cmd,
    "slurm": build_slurm_cmd,
    "local": build_local_cmd,
}
if host not in builders:
    raise ValueError(f"Unknown scheduler '{host}'. "
                     f"Expected one of {list(builders)}")


#### run a single job (used by both submit and local paths) ####
def run_job(cmdstr, label):
    print(f"[{label}] {cmdstr}")
    if args.dry_run:
        return 0
    return sp.call(cmdstr, shell=True)


#### execute ####
jobs = [(row.sub, str(row.ses)) for row in dt.itertuples(index=False) if row.RUN]

if host == "local":
    print(f"running {len(jobs)} jobs locally, max_parallel {max_parallel}")
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {
            pool.submit(run_job, builders[host](sub, ses), f"{sub}/{ses}"): (sub, ses)
            for sub, ses in jobs
        }
        for fut in as_completed(futures):
            sub, ses = futures[fut]
            rc = fut.result()
            status = "OK" if rc == 0 else f"FAILED (rc={rc})"
            print(f"[{sub}/{ses}] {status}")
else:
    # SGE/slurm: submission is near-instant, no need for parallelism
    for sub, ses in jobs:
        run_job(builders[host](sub, ses), f"{sub}/{ses}")

#### archive submission template + resolved config ####
shutil.copy(f"{code_dir}/qsub_base/{tool}_base.sh",
            f"{code_dir}/qsub_history/{tool}_base_{now}.sh")
shutil.copy(args.configFile,
            f"{code_dir}/qsub_history/config_qsub_{tool}_{cluster_name}_{now}.json")