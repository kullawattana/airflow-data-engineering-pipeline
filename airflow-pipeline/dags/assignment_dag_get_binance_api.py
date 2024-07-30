import json
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.mongo.hooks.mongo import MongoHook

def upload_to_mongo_db(ti, **context):
    try:
        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn() #get connection from mongoDB
        db = client.MyDB #Database name is "MyDB"
        print(f"Connected to MongoDB - {client.server_info()}")
        data = context["result"]
        db.get_binance_price_collection.insert_many(data)
    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")

default_args = {
    'owner': 'Suttipong',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 28),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'get_binance_price_every_15_minutes',
    default_args=default_args,
    description='Compute and store crypto average prices every 15 minutes from 6:00 AM',
    schedule_interval='*/15 6-23 * * *',
) as dag:

    t1 = SimpleHttpOperator(    
        task_id='get-currency-from-binance',
        method='GET',
        http_conn_id='binance_api',  # set up in Airflow UI => Admin => Connection
        endpoint='/api/v3/ticker?type=MINI&symbols=["BTCUSDT","BNBUSDT","ETHUSDT"]&windowSize=15m',
        headers={"Content-Type": "application/json"},
        response_check = lambda response : response.json() is not None,
        do_xcom_push=True,
        dag=dag
    )

    t2 = PythonOperator(
        task_id='upload-to-mongodb-db',
        python_callable=upload_to_mongo_db,
        op_kwargs={"result": t1.output},
        dag=dag
        )
    
    t1 >> t2