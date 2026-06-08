import dagster as dg

import scripts.preprocess

raw_data = "data/raw.parquet"
config_path = "scripts/config_vignette.yaml"
output = "output/vignette/data.parquet"


@dg.asset
def data():
    scripts.preprocess.preprocess(
        config_path=config_path, data_path=raw_data, output=output
    )
