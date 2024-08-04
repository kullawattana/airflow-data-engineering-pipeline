import json
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pymongo
from airflow.providers.mongo.hooks.mongo import MongoHook

def compute_and_store_avg_prices():
    try:
        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.BIDB #Database name is "BIDB"

        # ดึงข้อมูลทั้งหมดใน collection
        cursor = db.get_binance.find()
        data_list = list(cursor)
        
        # คำนวณค่าเฉลี่ย
        avg_prices = {}
        for record in data_list:
            if 'data' in record:
                _data = json.loads(record['data'])
                for item in _data:
                    symbol = item['symbol']
                    price = float(str(item['lastPrice']))
                    if symbol in avg_prices:
                        avg_prices[symbol].append(price)
                    else:
                        avg_prices[symbol] = [price]

        avg_prices = {symbol: sum(prices)/len(prices) for symbol, prices in avg_prices.items()}
        print("Average Prices:", avg_prices)

        # รับค่าเวลาปัจจุบันในรูปแบบ ISO
        current_time = datetime.utcnow().isoformat()
        dt = datetime.fromisoformat(current_time)

        # แปลง datetime object เป็น string ในรูปแบบ prices_YYYY_MM_DD_HH_MM
        formatted_time = dt.strftime('prices_%Y_%m_%d_%H_%M')

        # คำนวณค่าเฉลี่ย
        result_dict = {"timestamp": current_time, "avg_price": avg_prices}

        # เก็บค่าเฉลี่ยในแต่ละช่วงเวลา
        db.average_prices.insert_one(result_dict)
        db[formatted_time].insert_one(result_dict)

        # เก็บข้อมูลเพื่อใช้ในการค้นหาตามเวลา
        time_doc = {"formatted_time": formatted_time}
        db.collections_prices_date_times.insert_one(time_doc)

        print("Average prices saved with timestamp.")

    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")

default_args = {
    'owner': 'Suttipong',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 4),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes = 5),
}

with DAG(
    'get_binance_price_every_3_hours_for_visualization',
    default_args=default_args,
    description='Fetch data from MongoDB every 3 hours starting from 9:05 AM',
    schedule_interval='5 */3 * * *',
) as dag:
    t1 = PythonOperator(
        task_id='compute_average_prices_of_binance',
        python_callable=compute_and_store_avg_prices,
        dag=dag
        )
