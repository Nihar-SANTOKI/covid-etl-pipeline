import os
import yaml
from sqlalchemy import create_engine
import pandas as pd

def load(df: pd.DataFrame):
    """
    Load the transformed DataFrame into Postgres table `covid_history`,
    reading credentials from env vars first, then falling back to config.
    """
    # 1) Load config
    cfg = yaml.safe_load(open('config/config.yaml'))['database']
    host = os.getenv('DB_HOST',    cfg.get('host'))
    port = os.getenv('DB_PORT',    cfg.get('port'))
    db   = os.getenv('DB_NAME',    cfg.get('database'))
    user = os.getenv('DB_USER',    cfg.get('user'))
    pwd  = os.getenv('DB_PASS',    cfg.get('password'))

    # 2) Build connection URL
    conn_str = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    engine   = create_engine(conn_str, pool_pre_ping=True)

    # 3) Write in batches for performance
    df.to_sql(
        'covid_history',
        engine,
        if_exists='replace',
        index=False,
        method='multi',
        chunksize=1000
    )
