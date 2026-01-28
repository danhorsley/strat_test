import streamlit as st
import pandas as pd
import numpy as np
from strat import wrangle_data, add_signals_per_stock, find_returns

st.write("MAG 7 - strategy backtester")

all_stocks = ["TSLA","MSFT","AAPL","GOOG","AMZN","NVDA","META"]
with st.container(border=True):
    selected_stocks = st.multiselect("Stocks", all_stocks, default=all_stocks)
    portfolio_return = st.toggle("portfolio_return")
    
all_strats = ["Simple MA Crossover", "RSI Oversold/Overbought", "Buy & Hold (Benchmark)", "Momentum (ROC)"]
with st.container(border=True):
    strat = st.selectbox("Strategy", all_strats, index=0)
    if strat == "Simple MA Crossover":
        short_win = st.number_input("Short Window", min_value=1, max_value=100, value=20)
        long_win = st.number_input("Long Window", min_value=1, max_value=200, value=50)
    if strat == "RSI Oversold/Overbought":
        rsi_period = st.number_input("RSI Period", min_value=1, max_value=50, value=14)
        rsi_buy = st.number_input("RSI Buy Threshold", min_value=1, max_value=50, value=30)
        rsi_sell = st.number_input("RSI Sell Threshold", min_value=50, max_value=100, value=70)
    if strat == "Momentum (ROC)":
        lookback = st.number_input("ROC Period", min_value=1, max_value=252, value=126)
        threshold = st.number_input("ROC Threshold", min_value=-100.0, max_value=100.0, value=0.0)
        rebalance_freq = st.selectbox("Rebalance Frequency", options=['D','W','M','Q','A'], index=2)


    
df = wrangle_data(selected_stocks)
df = add_signals_per_stock(df, selected_stocks)




tab1, tab2 = st.tabs(["Chart", "Dataframe"])
if portfolio_return:
    tab1.line_chart(df['port_cumulative_rtn'], height=250)
else:
    tab1.line_chart(df['Close'], height=250)

tab2.dataframe(df, height=250, use_container_width=True)