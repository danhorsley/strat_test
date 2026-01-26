import streamlit as st
import pandas as pd
import numpy as np
from strat import wrangle_data, add_signals, find_returns

st.write("MAG 7 - strategy backtester")

all_stocks = ["TSLA"]
with st.container(border=True):
    stocks = st.multiselect("Stocks", all_stocks, default=all_stocks)
    portfolio_return = st.toggle("portfolio_return")

np.random.seed(42)
df = wrangle_data(pd.read_csv(f"data/{all_stocks[0]}.csv"))
df = add_signals(df)
df = find_returns(df)



tab1, tab2 = st.tabs(["Chart", "Dataframe"])
if portfolio_return:
    tab1.line_chart(df['cumulative_rtn'], height=250)
else:
    tab1.line_chart(df['Close'], height=250)

tab2.dataframe(df, height=250, use_container_width=True)