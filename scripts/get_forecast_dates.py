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

    # start and end dates of all included data
    data_start = date(
        config["season"]["start_year"],
        config["season"]["start_month"],
        config["season"]["start_day"],
    )

    data_end = date(
        config["season"]["end_year"],
        config["season"]["end_month"],
        config["season"]["end_day"],
    )

    # first and last forecast dates
    forecast_start = config["forecast_dates"]["start"]
    forecast_end = config["forecast_dates"]["end"]

    assert data_start <= forecast_start <= forecast_end <= data_end

    forecast_dates = pl.date_range(
        forecast_start,
        forecast_end,
        config["forecast_dates"]["interval"],
        eager=True,
    )

    first_season_date = date(
        config["season"]["start_year"],
        config["season"]["start_month"],
        config["season"]["start_day"],
    )
    last_season_date = date(
        config["season"]["end_year"],
        config["season"]["end_month"],
        config["season"]["end_day"],
    )
    if (forecast_dates[0] < first_season_date) or (
        forecast_dates[-1] > last_season_date
    ):
        print("forecast date out of data range.")
    else:
        print(*forecast_dates, sep=" ")
