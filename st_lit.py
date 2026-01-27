import streamlit as st
import pandas as pd
import numpy as np
from strat import wrangle_data, add_signals, find_returns

st.write("MAG 7 - strategy backtester")

all_stocks = ["TSLA","MSFT","AAPL","GOOG","AMZN","NVDA","META"]
with st.container(border=True):
    stocks = st.multiselect("Stocks", all_stocks, default=all_stocks)
    portfolio_return = st.toggle("portfolio_return")
    
all_strats = ["mavg", "rsi"]
with st.container(border=True):
    strat = st.selectbox("Strategy", all_strats, index=0)
    if strat == "mavg":
        short_win = st.number_input("Short Window", min_value=1, max_value=100, value=20)
        long_win = st.number_input("Long Window", min_value=1, max_value=200, value=50)
    if strat == "rsi":
        rsi_period = st.number_input("RSI Period", min_value=1, max_value=50, value=14)
        rsi_buy = st.number_input("RSI Buy Threshold", min_value=1, max_value=50, value=30)
        rsi_sell = st.number_input("RSI Sell Threshold", min_value=50, max_value=100, value=70)

df = wrangle_data(pd.read_csv(f"data/{all_stocks[0]}.csv"))
df = add_signals(df)
df = find_returns(df)



tab1, tab2 = st.tabs(["Chart", "Dataframe"])
if portfolio_return:
    tab1.line_chart(df['cumulative_rtn'], height=250)
else:
    tab1.line_chart(df['Close'], height=250)

tab2.dataframe(df, height=250, use_container_width=True)