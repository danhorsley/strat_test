import pandas as pd

# Load and view the first few rows
df = pd.read_parquet("precomputed_signals.parquet")
print(df.head(10))                  # first 10 rows
print(df.tail(5))                   # last few
print(df.info())                    # column types, memory, non-null counts
print(df.describe())                # summary stats
print(df['Date'].min(), df['Date'].max())  # date range

