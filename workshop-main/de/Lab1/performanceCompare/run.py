#Download data from https://drive.google.com/drive/folders/10Vz7Dg15Yl7apMe85Ry8e5iO7-XblZ-Q?usp=sharing

from pathlib import Path
import pandas as pd
import time

csvFile = Path(__file__).with_name('train_credit_bureau_a_2_5.csv')
print(csvFile)
pqFile = Path(__file__).with_name('train_credit_bureau_a_2_5.parquet')
pqGzipFile = Path(__file__).with_name('train_credit_bureau_a_2_5.parquet.gzip')

#1. CSV
start = time.time()
df = pd.read_csv(csvFile)
print(df.head())
end = time.time()
print("load csv file = ",end - start," seconds")

#2. Parquet
start = time.time()
df = pd.read_parquet(pqFile)
print(df.head())
end = time.time()
print("load parquet file = ",end - start," seconds")

#3. Parquet.gzip
start = time.time()
df = pd.read_parquet(pqGzipFile)
print(df.head())
end = time.time()
print("load parquet.gzip file = ",end - start," seconds")
