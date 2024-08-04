import json
import pendulum
from airflow.decorators import dag, task
from airflow.operators.email_operator import EmailOperator

default_args = {
    "email": ["testkepttest@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": True,
}

@dag(schedule_interval=None, 
     start_date=pendulum.datetime(2021, 1, 1, tz="UTC"), 
     catchup=False,
    default_args=default_args)
def mixed_etl():

    @task(task_id='extract', retries=2)
    def extract_data():
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
        order_data_dict = json.loads(data_string)
        return order_data_dict


    @task(multiple_outputs=True)
    def transform(order_data_dict: dict):
        total_order_value = 0
        for value in order_data_dict.values():
            total_order_value += value

        return {"total_order_value": total_order_value}

    @task()
    def load(total_order_value: float):
        print(f"Total order value is: {total_order_value:.2f}")

    email_notification = EmailOperator(
        task_id='email_notification',
        to='pokekarat@gmail.com',
        subject='dag completed',
        html_content='the dag has finished'
    )

    load(transform(extract_data())["total_order_value"]) >> email_notification

mixed_etl = mixed_etl()