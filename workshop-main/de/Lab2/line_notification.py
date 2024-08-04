import requests
import json
from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import pendulum # use for time


def get_bitcoin_report_today():
    url = 'https://api.binance.com/api/v3/ticker?type=MINI&symbol=BTCUSDT&windowSize=1h'
    response = requests.get(url)
    data = response.json()

    # on docker
    # with open('/usr/local/airflow/tests/data.json', 'w') as f:
    #     json.dump(data, f)

    # on cloud
    with open('/usr/local/airflow/data.json', 'w') as f:
        json.dump(data, f)  

    return data

def send_line_notify():
    url = 'https://notify-api.line.me/api/notify'
    #token = 'your_token'
    headers = {
        'content-type':
        'application/x-www-form-urlencoded',
        'Authorization': 'Bearer '+ 'vjTvwXaj4cLkzMP4AUMRKI0C1MAI35Sqq8j1EV59aG3'
    }

    # on docker
    # with open('/usr/local/airflow/tests/data.json') as f:
    #     data = json.load(f)

    # on cloud
    with open('/usr/local/airflow/data.json') as f:
        data = json.load(f)    

    msg = "BTC report today \n"
    for (k,v) in data.items():
        msg += str(k) + ":" + str(v) + "\n"

    r = requests.post(url, headers=headers, data={'message': msg})
    print(r.text)    

local_tz = pendulum.timezone("Asia/Bangkok") #Correct timezone

default_args = {
    'owner': 'Suttipong',
    'start_date': datetime(2021, 2, 28, 0, 0, 0, tzinfo=local_tz)
}
with DAG('line-notify',
         schedule_interval='0 6 * * *',  #run every at 6.00 AM.
         default_args=default_args,
         description='A simple data pipeline for line-notify',
         catchup=False) as dag:

    t1 = PythonOperator(
        task_id='get_bitcoin_report_today',
        python_callable=get_bitcoin_report_today
    )

    t2 = PythonOperator(
        task_id='send_line_notify',
        python_callable=send_line_notify
    )

    t1 >> t2

#Setup line notify
'''
1. Add "Line Notify" as a friend
2. Goto "https://notify-bot.line.me/th/" and login with line user password
3. Goto my account (Top) > My page (หน้าของฉัน) > click ออก access Token 
> "Create a token name (BTC notification)" > Select chat target

'''