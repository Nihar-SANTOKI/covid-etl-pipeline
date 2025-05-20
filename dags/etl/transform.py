import pandas as pd
import yaml

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot metrics into wide form, calculate daily deltas and rolling averages.
    """
    with open('config/config.yaml') as f:
        cfg = yaml.safe_load(f)['pipeline']
    window = cfg['rolling_window']

    # Basic validation
    expected = {'date','country','metric','count'}
    if not expected.issubset(df.columns):
        missing = expected - set(df.columns)
        raise KeyError(f"Missing columns: {missing}")

    df = df.dropna(subset=['count'])
    pivot = (
        df
        .pivot_table(index=['date','country'], columns='metric', values='count')
        .reset_index()
    )

    # Compute daily new and rolling averages
    pivot = pivot.sort_values(['country','date'])
    for m in ['cases','deaths','recovered']:
        pivot[f"new_{m}"]     = pivot.groupby('country')[m].diff()
        pivot[f"avg7_new_{m}"] = pivot.groupby('country')[f"new_{m}"]\
                                        .transform(lambda s: s.rolling(window, min_periods=1).mean())

    return pivot
