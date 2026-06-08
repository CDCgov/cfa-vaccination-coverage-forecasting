import subprocess
import sys
import tempfile
from pathlib import Path

import polars as pl
import yaml

config_path = "scripts/config_vignette.yaml"

with open(config_path) as f:
    config = yaml.safe_load(f)

run_id = config["run_id"]

forecast_dates = pl.date_range(
    config["forecast_dates"]["start"],
    config["forecast_dates"]["end"],
    config["forecast_dates"]["interval"],
    eager=True,
)

output_dir = Path("output") / run_id
config_copy = output_dir / "config.yaml"
raw_data = Path("data") / "raw.parquet"
data = output_dir / "data.parquet"
pred_dir = output_dir / "pred"
scores = output_dir / "scores.parquet"
plot_dir = output_dir / "plots"
plot_data = plot_dir / ".data.checkpoint"
plot_preds = plot_dir / ".preds.checkpoint"
plot_scores = plot_dir / ".scores.checkpoint"
preds = [pred_dir / f"forecast_date={x}" / "part-0.parquet" for x in forecast_dates]
fits = [output_dir / "fits" / f"fit_{x}.pkl" for x in forecast_dates]

rules = (
    [
        {"output": "all", "input": config_copy},
        {
            "output": config_copy,
            "input": config_path,
            "action": f"cp {config_path} {config_copy}",
        },
        {
            "output": plot_scores,
            "input": ["scripts/plot_scores.py", scores, config_path],
            "action": f"python scripts/plot_scores.py --scores={scores} --config={config_path} --output={plot_scores}",
        },
        {
            "output": plot_preds,
            "input": ["scripts/plot_preds.py", config_path, data] + preds,
            "action": f"python scripts/plot_preds.py --config={config_path} --data={data} --preds={pred_dir} --output={plot_preds}",
        },
        {
            "output": plot_data,
            "input": ["scripts/plot_data.py", data, config_path],
            "action": f"python scripts/plot_data.py --config={config_path} --data={data} --output={plot_data}",
        },
        {
            "output": scores,
            "input": ["scripts/eval.py", data, config_path] + preds,
            "action": f"python scripts/eval.py --config={config_path} --data={data} --output={scores}",
        },
        {
            "output": data,
            "input": ["scripts/preprocess.py", raw_data, config_path],
            "action": f"python scripts/preprocess.py --config={config_path} --input={raw_data} output={data}",
        },
        {"output": "clean", "action": f"rm -rf {output_dir}"},
    ]
    + [
        {
            "output": pred,
            "input": ["scripts/predict.py", fit],
            "action": f"python scripts/predict.py --fits={fit} --config={config_path} --output={pred}",
        }
        for pred, fit in zip(preds, fits)
    ]
    + [
        {
            "output": fit,
            "input": ["scripts/fit.py", data, config_path],
            "action": f"python scripts/fit.py --data={data} --config={config_path} --output={fit} --forecast_date={date}",
        }
        for fit, date in zip(fits, forecast_dates)
    ]
)


def make(rules):
    lines = []
    for rule in rules:
        line = str(rule["output"]) + ":"
        if "input" in rule:
            if isinstance(rule["input"], (str, Path)):
                line += " " + str(rule["input"])
            elif isinstance(rule["input"], list):
                line += " " + " ".join([str(x) for x in rule["input"]])
        lines.append(line)
        if "action" in rule:
            lines.append("\t" + rule["action"])
        lines.append("")

    makefile = "\n".join(lines)

    print(makefile)

    with tempfile.NamedTemporaryFile("w+t") as f:
        f.write(makefile)
        f.flush()

        subprocess.run(["make", "--makefile", f.name] + sys.argv[1:])


if __name__ == "__main__":
    make(rules)
