import requests
import pandas as pd
import yaml
import time
from typing import List

def extract(countries: List[str], days: int) -> pd.DataFrame:
    """
    Fetch COVID-19 historical data for each country over `days`.
    Returns a long-form DataFrame with columns [date, country, metric, count].
    """
    with open('config/config.yaml') as f:
        cfg = yaml.safe_load(f)['covid_api']
    base = cfg['base_url']
    template = cfg['historical_country']

    frames = []
    for country in countries:
        url = f"{base}{template.format(country=country, days=days)}"
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json().get('timeline', {})
                break
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        df = pd.DataFrame(data).reset_index().rename(columns={'index': 'date'})
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y')
        df['country'] = country
        long = df.melt(
            id_vars=['date', 'country'],
            value_vars=['cases', 'deaths', 'recovered'],
            var_name='metric',
            value_name='count'
        )
        frames.append(long)

    return pd.concat(frames, ignore_index=True)
