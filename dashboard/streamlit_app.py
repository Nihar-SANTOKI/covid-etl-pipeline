import os
import streamlit as st
import pandas as pd
import yaml
from sqlalchemy import create_engine

st.set_page_config(page_title="COVID-19 Dashboard", layout="wide")

# 1) Load DB config (env vars override config file)
cfg = yaml.safe_load(open('config/config.yaml'))['database']
HOST = os.getenv('DB_HOST',    cfg.get('host'))
PORT = os.getenv('DB_PORT',    cfg.get('port'))
DB   = os.getenv('DB_NAME',    cfg.get('database'))
USER = os.getenv('DB_USER',    cfg.get('user'))
PASS = os.getenv('DB_PASS',    cfg.get('password'))

conn_url = f"postgresql+psycopg2://{USER}:{PASS}@{HOST}:{PORT}/{DB}"
ENGINE   = create_engine(conn_url, connect_args={"connect_timeout":10}, pool_pre_ping=True)

TEST = os.getenv("TEST_MODE", "false").lower() == "true"
if TEST:
    @st.cache_data
    def load_data():
        return pd.read_csv("sample_data.csv", parse_dates=['date'])
else:
    # Real mode: load DB config & query
    cfg = yaml.safe_load(open('config/config.yaml'))['database']
    HOST = os.getenv('DB_HOST', cfg['host'])
    PORT = os.getenv('DB_PORT', cfg['port'])
    DB   = os.getenv('DB_NAME', cfg['database'])
    USER = os.getenv('DB_USER', cfg['user'])
    PASS = os.getenv('DB_PASS', cfg['password'])

    ENGINE = create_engine(
        f"postgresql+psycopg2://{USER}:{PASS}@{HOST}:{PORT}/{DB}",
        connect_args={"connect_timeout": 10},
        pool_pre_ping=True
    )

    @st.cache_data
    def load_data():
        count = pd.read_sql("SELECT COUNT(*) AS cnt FROM covid_history;", ENGINE)
        st.write("🔢 covid_history row count:", int(count['cnt'][0]))
        return pd.read_sql(
            "SELECT * FROM covid_history ORDER BY country, date;",
            ENGINE,
            parse_dates=['date']
        )

st.title("🌏 COVID-19 Dashboard")

df = load_data()
if df.empty:
    st.error("No data in `covid_history`. Please run the ETL.")
    st.stop()

st.success("✅ Loaded data successfully!")

# — the rest of your UI —
countries    = df['country'].unique().tolist()
sel_countries = st.sidebar.multiselect("Countries", countries, default=countries)

min_date, max_date = df['date'].min(), df['date'].max()
start, end = st.sidebar.date_input(
    "Date range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

metrics     = [c for c in df.columns if c not in ('date','country')]
sel_metrics = st.sidebar.multiselect("Metrics", metrics, default=['new_cases'])

mask = (
    df['country'].isin(sel_countries) &
    (df['date'] >= pd.to_datetime(start)) &
    (df['date'] <= pd.to_datetime(end))
)
df_f = df.loc[mask]

# KPI cards
cols   = st.columns(3)
latest = df_f.groupby('country').tail(1)
cols[0].metric("Latest New Cases",   int(latest['new_cases'].sum()))
cols[1].metric("7-day Avg New Cases", round(latest['avg7_new_cases'].mean(),1))
cols[2].metric("Total Recovered",     int(latest['recovered'].sum()))

# Time series charts
for m in sel_metrics:
    st.subheader(m.replace('_',' ').title())
    pivot = df_f.pivot(index='date', columns='country', values=m)
    st.line_chart(pivot, use_container_width=True)
