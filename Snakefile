import subprocess
import sys
import tempfile
from pathlib import Path
import scripts.preprocess, scripts.plot_scores
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

# snakemake has a problem with the dates in the config
del config["forecast_dates"]

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


rule all:
    input:
        config_copy,
        plot_data,
        plot_preds,
        plot_scores,


rule:
    input:
        config_path,
    output:
        config_copy,
    shell:
        "cp {input} {output}"


rule plot_scores:
    input:
        "scripts/plot_scores.py",
        scores,
        config_path,
    output:
        plot_scores,
    run:
        scripts.plot_scores.plot_scores(scores=scores, output=output)


rule plot_preds:
    input:
        "scripts/plot_preds.py",
        config_path,
        data,
        preds,
    output:
        plot_preds,
    shell:
        f"python scripts/plot_preds.py --config={config_path} --data={data} --preds={pred_dir} --output={plot_preds}"


rule plot_data:
    input:
        "scripts/plot_data.py",
        data,
        config_path,
    output:
        plot_data,
    shell:
        f"python scripts/plot_data.py --config={config_path} --data={data} --output={plot_data}"


rule scores:
    input:
        "scripts/eval.py",
        data,
        config_path,
        preds,
    output:
        scores,
    shell:
        f"python scripts/eval.py --config={config_path} --data={data} --output={scores}"


rule data:
    input:
        "scripts/preprocess.py",
        raw_data,
        config_path,
    output:
        data,
    run:
        scripts.preprocess.preprocess(
            config_path=config_path, data_path=raw_data, output=output
        )


rule clean:
    shell:
        f"rm -rf {output_dir}"


rule predict:
    input:
        "scripts/predict.py",
        fit=f"{output_dir}/fits/fit_{{date}}.pkl",
    output:
        f"{pred_dir}/forecast_date={{date}}/part-0.parquet",
    shell:
        f"python scripts/predict.py --fits={input.fit} --config={config_path} --output={output}"


rule fit:
    input:
        "scripts/fit.py",
        data,
        config_path,
    output:
        f"{output_dir}/fits/fit_{{date}}.pkl",
    shell:
        f"python scripts/fit.py --data={data} --config={config_path} --output={output} --forecast_date={{wildcards.date}}"
