import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data(ttl=None)
def load_precomputed():
    return pd.read_parquet("precomputed_signals.parquet")

df_pre = load_precomputed()


# ── UI: title ───────────────────────────────────────────────────
st.write("MAG 7 - strategy backtester")

# ── UI: strategy selection ────────────────────────────────────────────────
strat_display = st.selectbox(
    "Strategy",
    options=[
        "Buy & Hold",
        "MA Crossover (50/200)",
        "RSI (14, 30/70)",
        "Momentum (126 days)"
    ]
)

# Map legible name → column suffix
strat_suffix_map = {
    "Buy & Hold": "buy_and_hold",
    "MA Crossover (50/200)": "mavg_50_200",
    "RSI (14, 30/70)": "rsi_14_30_70",
    "Momentum (126 days)": "momentum_126_0"
}
suffix = strat_suffix_map[strat_display]

# ── UI: stock selection ──────────────────────────────────────────────

all_stocks = ["TSLA","MSFT","AAPL","GOOG","AMZN","NVDA","META"]
with st.container(border=True):
    selected_stocks = st.multiselect("Stocks", all_stocks, default=all_stocks)
    portfolio_return = st.toggle("portfolio_return", value=True)

# ── UI: date selection ──────────────────────────────────────────────
min_date = df_pre['Date'].min().date()
max_date = df_pre['Date'].max().date()

# Default: full range
default_start = min_date
default_end   = max_date

# The widget
date_range = st.date_input(
    "Select date range",
    value=(default_start, default_end),
    min_value=min_date,
    max_value=max_date,
    format="YYYY-MM-DD"  # optional, looks clean
)



# Handle the output
if len(date_range) == 2:
    start_date, end_date = date_range
    st.write(f"Selected: {start_date} → {end_date}")
    # Convert to pd.Timestamp for filtering (pandas likes Timestamp better than date)
    start_ts = pd.Timestamp(start_date)
    end_ts   = pd.Timestamp(end_date)
else:
    st.info("Select both start and end dates")


df_filt = df_pre[
    (df_pre['Date'] >= start_ts) &
    (df_pre['Date'] <= end_ts)
].copy()

df_filt['strat_rtn'] = df_filt[f'strat_rtn_{suffix}']

port_daily = (
    df_filt.pivot_table(
        index='Date',
        columns='Ticker',
        values='strat_rtn',
        aggfunc='mean'          # equal weight = average across stocks
    )
    .mean(axis=1)               # final portfolio daily return
    .rename('portfolio_daily_ret')
)

port_cum = (1 + port_daily).cumprod().rename('port_cumulative_rtn')

df_plot = df_filt.merge(
    port_cum.to_frame(),
    left_on='Date',
    right_index=True,
    how='left'
)

tab1, tab2 = st.tabs(["Chart", "Dataframe"])
if portfolio_return:
    tab1.line_chart(df_plot.drop_duplicates(subset='Date').set_index('Date')['port_cumulative_rtn'], height=250)
else:
    df_filt['pct_change_close'] = df_filt.groupby('Ticker')['Close'].pct_change()
    df_filt['avg_pct_change'] = df_filt.groupby('Date')['pct_change_close'].transform('mean')
    df_filt['base_cum_rtn'] = (1 + df_filt['avg_pct_change']).cumprod()
    tab1.line_chart(df_filt.drop_duplicates(subset='Date').set_index('Date')['base_cum_rtn'], height=250)

tab2.dataframe(df_filt, height=250, use_container_width=True)

# Now use df_plot or port_cum for charts, metrics, etc.
# st.line_chart(port_cum)