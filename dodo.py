from pathlib import Path

import polars as pl
import yaml

CONFIG = "scripts/config_vignette.yaml"

with open(CONFIG) as f:
    config = yaml.safe_load(f)

run_id = config["run_id"]

RAW_DATA = "data/raw.parquet"
OUTPUT_DIR = Path("output") / run_id
CONFIG_COPY = OUTPUT_DIR / "config.yaml"
DATA = OUTPUT_DIR / "data.parquet"
PRED_DIR = OUTPUT_DIR / "pred"
SCORES = OUTPUT_DIR / "scores.parquet"

# each plotting script outputs multiple files; use a single output as a flag
PLOT_DATA = OUTPUT_DIR / "plots" / ".data.checkpoint"
PLOT_PREDS = OUTPUT_DIR / "plots" / ".preds.checkpoint"
PLOT_SCORES = OUTPUT_DIR / "plots" / ".scores.checkpoint"

# dynamically find forecast dates to use
forecast_dates = pl.date_range(
    config["forecast_dates"]["start"],
    config["forecast_dates"]["end"],
    config["forecast_dates"]["interval"],
    eager=True,
)

PREDS = [PRED_DIR / f"forecast_date={x}" / "part-0.parquet" for x in forecast_dates]
FITS = [OUTPUT_DIR / "fits" / f"fit_{x}.pkl" for x in forecast_dates]


# all: $(CONFIG_COPY) $(PLOT_DATA) $(PLOT_PREDS) $(PLOT_SCORES) $(FITS)


def task_all():
    return {"file_dep": CONFIG_COPY}


def task_config_copy():
    return {
        "actions": [f"mkdir -p {OUTPUT_DIR}", f"cp {CONFIG} {CONFIG_COPY}"],
        "targets": [CONFIG_COPY],
        "clean": True,
    }


# $(PLOT_SCORES): scripts/plot_scores.py $(SCORES) $(CONFIG)
# 	python $< --scores=$(SCORES) --config=$(CONFIG) --output=$@

# $(PLOT_PREDS): scripts/plot_preds.py $(CONFIG) $(DATA) $(PREDS)
# 	python $< --config=$(CONFIG) --data=$(DATA) --preds=$(PRED_DIR) --output=$@

# $(PLOT_DATA): scripts/plot_data.py $(DATA) $(CONFIG)
# 	python $< --config=$(CONFIG) --data=$(DATA) --output=$@

# $(SCORES): scripts/eval.py $(PREDS) $(DATA) $(CONFIG)
# 	python $< --preds=$(PRED_DIR) --data=$(DATA) --config=$(CONFIG) --output=$@

# # output/run_id/pred/forecast_date=2021-01-01/part-0.parquet <== output/fits/fit_2021-01-01.pkl
# $(PRED_DIR)/forecast_date$(EQ)%/part-0.parquet: scripts/predict.py $(OUTPUT_DIR)/fits/fit_%.pkl
# 	python $< --fits=$(OUTPUT_DIR)/fits/fit_$*.pkl --config=$(CONFIG) --output=$@

# $(OUTPUT_DIR)/fits/fit_%.pkl: scripts/fit.py $(DATA) $(CONFIG)
# 	python $< --data=$(DATA) --forecast_date=$* --config=$(CONFIG) --output=$@

# $(DATA): scripts/preprocess.py $(RAW_DATA) $(CONFIG)
# 	python $< --config=$(CONFIG) --input=$(RAW_DATA) --output=$@
