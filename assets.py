from pathlib import Path
from typing import Any

import dagster as dg
import polars as pl
import yaml

import scripts.preprocess

repo_dir = Path(__file__).parent
raw_data_path = repo_dir / "data" / "raw.parquet"
config_path = repo_dir / "scripts" / "config_vignette.yaml"
output = "output/vignette/data.parquet"

print(raw_data_path)


@dg.asset
def config_() -> dict[str, Any]:
    with open(config_path) as f:
        x = yaml.safe_load(f)

    return x


@dg.asset
def raw_data() -> pl.DataFrame:
    return pl.read_parquet(raw_data_path)


@dg.asset
def data(config_: dict[str, Any], raw_data: pl.DataFrame):
    geographies = config_.get("geographies", None)

    data = scripts.preprocess.clean_data(
        raw_data,
        start_year=config_["season"]["start_year"],
        end_year=config_["season"]["end_year"],
        season_start_month=config_["season"]["start_month"],
        season_start_day=config_["season"]["start_day"],
        season_end_month=config_["season"]["end_month"],
        season_end_day=config_["season"]["end_day"],
        geographies=geographies,
    )

    if data.height == 0:
        raise RuntimeError("No data after preprocessing")

    return data
