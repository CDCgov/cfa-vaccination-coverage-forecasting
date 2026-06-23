import argparse
from datetime import date

import polars as pl
import yaml

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    forecast_dates = pl.date_range(
        config["forecast_dates"]["start"],
        config["forecast_dates"]["end"],
        config["forecast_dates"]["interval"],
        eager=True,
    )

    if forecast_dates[0] < date(
        config["season"]["start_year"],
        config["season"]["start_month"],
        config["season"]["start_day"],
    ):
        print("forecast date out of data range. ")
    elif forecast_dates[-1] > date(
        config["season"]["end_year"],
        config["season"]["end_month"],
        config["season"]["end_day"],
    ):
        print("forecast date out of data range. ")
    else:
        print(*forecast_dates, sep=" ")
