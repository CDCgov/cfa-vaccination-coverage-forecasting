import argparse
import calendar
import datetime as dt
from pathlib import Path

import polars as pl
import yaml

import vcf

# these values should be irrelevant
FORECAST_DATE = dt.date(2020, 1, 1)
ALPHA = 0.05
QUANTILES = [0.5, ALPHA / 2, 1.0 - ALPHA / 2]


def count_missing(data: pl.DataFrame, config: dict) -> str:
    """Count missing values in the data.

    Args:
        data: Input data to count missing values on.
        config: Configuration dictionary.

    Returns:
        String report of missing values.
    """

    model_params = next(x["params"] for x in config["models"] if x["name"] == "RFModel")
    assert "n_estimators" in model_params

    model = vcf.RFModel(
        data=data,
        forecast_date=FORECAST_DATE,
        params=model_params,
        season=config["season"],
        quantiles=QUANTILES,
    )
    model_data_long = model.data_no_impute.unpivot(
        index=["season", "geography"], variable_name="t", value_name="estimate"
    )

    missing_by_column = {
        k: v.item()
        for k, v in model.data_no_impute.select(pl.all().is_null())
        .sum()
        .to_dict()
        .items()
    }
    month0 = calendar.month_name[config["season"]["start_month"]]

    report = "\n".join(
        [
            "Total rows: " + str(model_data_long.shape[0]),
            "Total missing values: "
            + str(model_data_long.select(pl.col("estimate").is_null()).sum().item()),
            f"Missing values by column: (`0` is {month0})",
            str(missing_by_column),
        ]
    )

    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", help="config file", required=True)
    p.add_argument("--data", help="input data", required=True)
    p.add_argument("--output", help="output report path", required=True)
    args = p.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    data = pl.read_parquet(args.data)

    report = count_missing(data=data, config=config)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)
