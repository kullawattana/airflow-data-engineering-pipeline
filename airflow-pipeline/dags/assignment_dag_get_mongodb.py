import requests
import json
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
from airflow.providers.mongo.hooks.mongo import MongoHook

def compute_and_store_avg_prices():
    client = MongoClient('mongodb+srv://admin1234:hhIv2MsSLh70nPFL@cluster0.yuisrie.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['MyDB'] #Database Name
    collection = db['get_binance_price_collection'] #Collection Name
    result = collection.find() #Retrive Data
    for record in result:
        print("Fetched data from MongoDB:", record)
        prices = [(item['symbol'], float(item['lastPrice'])) for item in record]

        #process collection data
        avg_prices = {}
        for symbol, price in prices:
            if symbol in avg_prices:
                avg_prices[symbol].append(price)
            else:
                avg_prices[symbol] = [price]

        #average last price        
        avg_prices = {symbol: sum(prices)/len(prices) for symbol, prices in avg_prices.items()}
    
        try:
            hook = MongoHook(mongo_conn_id='mongo_default')
            client = hook.get_conn()
            #Database Name is "MyDB"
            db = client.MyDB
            # Collection name "get_average_binance_price_collection" to insert data for visualization
            average_price_collection = db.get_average_binance_price_collection
            print(f"Connected to MongoDB - {client.server_info()}")
            average_price_collection.insert_one(avg_prices)
        except Exception as e:
            print(f"Error connecting to MongoDB -- {e}")

default_args = {
    'owner': 'Suttipong',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 28),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes = 5),
}

with DAG(
    'get_binance_price_every_3_hours',
    default_args=default_args,
    description='Fetch data from MongoDB every 3 hours starting from 9:05 AM',
    schedule_interval='5 */3 * * *',
) as dag:
    t1 = PythonOperator(
        task_id='compute_average_prices_of_binance',
        python_callable=compute_and_store_avg_prices,
        dag=dag
        )
