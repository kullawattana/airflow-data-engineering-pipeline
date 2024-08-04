#List of operators https://airflow.apache.org/docs/apache-airflow/1.10.3/_api/airflow/operators/index.html#

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

#Define default arguments
default_args = {
    'owner': 'your_name',
    'start_date': datetime (2024, 6, 24),
    'retries': 1,
}

# Instantiate your DAG
dag = DAG ('my_first_dag', 
           default_args=default_args, 
           schedule_interval="* * * * *") #https://crontab.guru/#*_19_*_*_*

# Define tasks
def task1():
    print ("Executing Task 1")

def task2():
    print ("Executing Task 2")

task_1 = PythonOperator(
    task_id='task_1',
    python_callable=task1,
    dag=dag,
)

task_2 = PythonOperator(
    task_id='task_2',
    python_callable=task2,
    dag=dag,
)

# Set task dependencies
task_1 >> task_2