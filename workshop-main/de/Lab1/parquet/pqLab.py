from pathlib import Path
import pandas as pd

bpq = Path(__file__).with_name('bank.parquet')
df = pd.read_parquet(bpq, engine='pyarrow')
print(df.head())