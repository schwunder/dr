import yaml
import subprocess

with open("configs.yaml") as f:
    cfgs = yaml.safe_load(f)

for method in ["spacemap", "trimap", "phate"]:
    for c in cfgs[method]:
        print(f"Running {method}:{c['name']}")
        subprocess.run(["python", "run.py", "--method", method, "--config", c["name"]]) 