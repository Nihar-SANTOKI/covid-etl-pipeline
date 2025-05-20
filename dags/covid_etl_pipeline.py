from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow import DAG
from datetime import datetime, timedelta
import yaml
from etl.extract import extract
from etl.transform import transform
from etl.load import load

@dag(
    dag_id="covid_etl_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2024,1,1),
    catchup=False,
    doc_md="""
#### COVID-19 ETL Pipeline
1. **Extract** historical data per configured countries/days  
2. **Transform** into wide format, compute new cases/deaths/recovered + 7-day rolling avg  
3. **Load** into `covid_history` table on Postgres  
*Includes basic data validation and retry logic.*
"""
)
def covid_etl_pipeline():

    @task(retries=2, retry_delay=timedelta(minutes=5))
    def extract_task():
        cfg = yaml.safe_load(open('config/config.yaml'))['pipeline']
        df = extract(cfg['countries'], cfg['days'])
        if df.empty:
            raise AirflowFailException("No data extracted")
        return df

    @task()
    def transform_task(df):
        df_clean = transform(df)
        if df_clean.empty:
            raise AirflowFailException("Transformation resulted in empty DataFrame")
        return df_clean

    @task()
    def load_task(df):
        load(df)

    raw = extract_task()
    cleaned = transform_task(raw)
    load_task(cleaned)

covid_etl = covid_etl_pipeline()
