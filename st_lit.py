import streamlit as st
import pandas as pd
import numpy as np
from strat import wrangle_data, add_signals, find_returns

st.write("MAG 7 - strategy backtester")

all_stocks = ["TSLA"]
with st.container(border=True):
    stocks = st.multiselect("Stocks", all_stocks, default=all_stocks)
    rolling_average = st.toggle("Rolling average")

np.random.seed(42)
df = wrangle_data(pd.read_csv(f"data/{all_stocks[0]}.csv"))
df = add_signals(df)
df = find_returns(df)

if rolling_average:
    df = df['cumulative_rtn']

tab1, tab2 = st.tabs(["Chart", "Dataframe"])
tab1.line_chart(df['Close'], height=250)
tab2.dataframe(df, height=250, use_container_width=True)