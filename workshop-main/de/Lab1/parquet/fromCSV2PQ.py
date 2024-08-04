from pathlib import Path
import pandas as pd


bcsv = Path(__file__).with_name('bank.csv')
bpq = Path(__file__).with_name('bank.parquet')

df = pd.read_csv(bcsv)
df.to_parquet(bpq) #,compression="gzip"
