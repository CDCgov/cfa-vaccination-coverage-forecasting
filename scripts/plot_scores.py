import argparse
from pathlib import Path

import altair as alt
import polars as pl
import yaml
from plot_preds import MODEL_COLOR_SCALE

LINE_OPACITY = 0.4

# scores across seasons & states

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--scores", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)

    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    scores = pl.read_parquet(args.scores)

    out_flag = Path(args.output)
    out_dir = out_flag.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    ## boxplot of scores across states by forecast date ##
    alt.Chart(scores).mark_boxplot(ticks=True).encode(
        alt.X(
            "model",
            title=None,
            axis=alt.Axis(labels=False, ticks=False),
            scale=alt.Scale(padding=1),
        ),
        alt.Y("score_value", title="End-of-season abs. diff. (p.p.)"),
        alt.Color("model", scale=MODEL_COLOR_SCALE),
        alt.Column(
            "forecast_date",
            title="",
            header=alt.Header(orient="bottom", labelFontSize=20, format="%b"),
        ),
    ).properties(width=80, height=400).configure_facet(spacing=0).configure_view(
        stroke=None
    ).configure_axis(labelFontSize=20, titleFontSize=24).configure_legend(
        labelFontSize=20, title=None
    ).save(out_dir / "scores.svg")

    out_flag.touch()
