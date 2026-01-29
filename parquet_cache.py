import streamlit as st
import pandas as pd

@st.cache_data(ttl=None)
def load_precomputed():
    return pd.read_parquet("precomputed_signals.parquet")

df_pre = load_precomputed()

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

#date filtering

df_filt = df_pre[
    (df_pre['Date'] >= st.date_input("Start date")) &
    (df_pre['Date'] <= st.date_input("End date"))
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

# Now use df_plot or port_cum for charts, metrics, etc.
st.line_chart(port_cum)