import argparse
from pathlib import Path

import altair as alt
import polars as pl
import yaml
from plot_data import AXIS_PERCENT

import vcf

LINE_OPACITY = 0.4


def plot_data_cone(
    chart_data: pl.DataFrame,
    facet_kwargs: dict,
    out_dir: str,
    filename: str,
    properties_kwargs: dict | None = None,
    config_legend_kwargs: dict | None = None,
    config_axis_kwargs: dict | None = None,
):
    base = alt.Chart(chart_data).encode(
        alt.X("time_end", title=None, axis=alt.Axis(format="%b"))
    )
    fc_cone = base.mark_area(opacity=0.25).encode(
        alt.Y("pred_lci", title="", axis=AXIS_PERCENT),
        alt.Y2("pred_uci"),
        alt.Color("model"),
    )
    fc_points = base.mark_line(opacity=0.75).encode(
        alt.Y("pred_estimate"), alt.Color("model")
    )
    data_points = base.mark_point(color="black").encode(alt.Y("obs_estimate"))
    data_error = base.mark_rule(color="black").encode(
        alt.X2("time_end"), alt.Y("obs_lci"), alt.Y2("obs_uci")
    )

    out_path = Path(out_dir) / filename
    chart = fc_cone + fc_points + data_points + data_error

    if properties_kwargs:
        chart = chart.properties(**properties_kwargs)

    chart = chart.facet(**facet_kwargs)

    if config_axis_kwargs:
        chart = chart.configure_axis(**config_axis_kwargs)

    if config_legend_kwargs:
        chart = chart.configure_legend(**config_legend_kwargs)

    chart.save(out_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--preds", required=True)
    p.add_argument("--output", required=True, help="output flag file")
    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    season = config["season"]

    out_flag = Path(args.output)
    out_dir = out_flag.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    preds_raw = pl.read_parquet(args.preds)

    # get the prediction cones
    half_alpha = config["alpha"] / 2
    quantiles = {half_alpha, 0.5, 1.0 - half_alpha}

    # check that quantiles are present in the data
    all_quantiles = preds_raw.select(pl.col("quantile").unique()).to_series()
    assert quantiles.issubset(all_quantiles)

    forecast_season = preds_raw.select(
        vcf.to_season(
            pl.col("forecast_date"),
            season_start_month=season["start_month"],
            season_end_month=season["end_month"],
        ).unique()
    ).to_series()
    assert len(forecast_season) == 1, "Can only plot forecasts from one season"
    forecast_season = forecast_season[0]

    preds = (
        preds_raw.filter(
            pl.col("time_end") > pl.col("forecast_date"),
            pl.col("season") == pl.lit(forecast_season),
            pl.col("quantile").is_in(quantiles),
        )
        .drop("season")
        .with_columns(
            pl.col("quantile").replace_strict(
                {
                    half_alpha: "pred_lci",
                    0.5: "pred_estimate",
                    1.0 - half_alpha: "pred_uci",
                }
            )
        )
        .pivot(on="quantile", values="estimate")
    )

    obs = (
        pl.read_parquet(args.data)
        .filter(pl.col("season") == pl.lit(forecast_season))
        .select(["geography", "time_end", "estimate", "lci", "uci"])
        .rename({"estimate": "obs_estimate", "lci": "obs_lci", "uci": "obs_uci"})
    )

    # hack: at the last forecast date, we make a forecast for only one date, but we
    # can't show this with .mark_line(), and so it ends up blank. So remove those
    # dates
    good_fcs = (
        preds.filter(pl.col("pred_estimate").is_not_null())
        .group_by("model", "forecast_date")
        .agg(n=pl.col("time_end").unique().len())
        .filter(pl.col("n") >= 2)
        .select("model", "forecast_date")
    )

    chart_data = obs.join(good_fcs, how="cross").join(
        preds, on=["model", "geography", "forecast_date", "time_end"], how="left"
    )

    ## forecast all ##
    plot_data_cone(
        chart_data=chart_data,
        facet_kwargs={
            "column": "forecast_date",
            "row": "geography",
        },
        out_dir=out_dir,
        filename="forecast.svg",
    )

    ## forecast the entire season at the beginning of the season ##
    plot_data_cone(
        chart_data=chart_data.filter(
            pl.col("forecast_date") == pl.col("forecast_date").min()
        ),
        facet_kwargs={
            "facet": alt.Facet(
                "geography", title="", header=alt.Header(labelFontSize=20)
            ),
            "columns": 6,
        },
        properties_kwargs={"width": 300, "height": 200},
        config_axis_kwargs={"labelFontSize": 20, "titleFontSize": 24},
        config_legend_kwargs={"labelFontSize": 20, "title": None},
        out_dir=out_dir,
        filename="forecast_entire_season.svg",
    )

    ## forecast the good state and bad state in LPLModel ##
    plot_data_cone(
        chart_data=chart_data.filter(
            pl.col("geography").is_in(["South Dakota", "North Dakota"]),
            pl.col("model") == pl.lit("LPLModel"),
        ),
        facet_kwargs={
            "row": alt.Row(
                "geography",
                header=alt.Header(labelFontSize=20),
                title="",
                sort=["South Dakota", "North Dakota"],
            ),
            "column": alt.Column(
                "forecast_date", header=alt.Header(labelFontSize=20), title=""
            ),
        },
        config_axis_kwargs={"labelFontSize": 20, "titleFontSize": 24},
        out_dir=out_dir,
        filename="examples_LPL.svg",
    )

    ## forecast the good state and bad state in RFModel ##
    plot_data_cone(
        chart_data=chart_data.filter(
            pl.col("geography").is_in(["Wyoming", "Vermont"]),
            pl.col("model") == pl.lit("RFModel"),
        ),
        facet_kwargs={
            "row": alt.Row(
                "geography",
                header=alt.Header(labelFontSize=20),
                title="",
                sort=["Wyoming", "Vermont"],
            ),
            "column": alt.Column(
                "forecast_date", header=alt.Header(labelFontSize=20), title=""
            ),
        },
        config_axis_kwargs={"labelFontSize": 20, "titleFontSize": 24},
        out_dir=out_dir,
        filename="examples_RF.svg",
    )

    out_flag.touch()
