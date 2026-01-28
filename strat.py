import pandas as pd
import numpy as np


def wrangle_data(selected_stocks: list[str]) -> pd.DataFrame:
    """
    Load CSVs, normalize prices, keep Date as index, concat without resetting.
    Returns DataFrame with DatetimeIndex and 'Ticker' column.
    """
    all_data = []
    
    for stock in selected_stocks:
        # Load with Date as index if it's the first column
        df = pd.read_csv(
            f"data/{stock}.csv",
            index_col=0,                    # assume first column = Date
            parse_dates=True                # auto-convert to datetime
        )
        
        # Rename index to 'Date' if needed (some CSVs use 'date', 'timestamp', etc.)
        if not isinstance(df.index.name, str) or df.index.name.lower() not in ['date', 'datetime']:
            df.index.name = 'Date'
        
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        
        # Normalize Close (or Adj Close)
        price_col = 'Close'
        df[price_col] = pd.to_numeric(df[price_col], downcast='float')
        df[price_col] = df[price_col] / df[price_col].iloc[0]
        
        # Add Ticker as column
        df['Ticker'] = stock
        
        all_data.append(df)
    
    # Concat while preserving the Date index
    combined_df = pd.concat(all_data)  # ← no ignore_index=True !
    
    # Sort by date and ticker (optional but nice)
    combined_df = combined_df.sort_index().sort_values('Ticker')
    
    # Optional: add returns here so later steps are simpler
    combined_df['returns'] = combined_df.groupby('Ticker')[price_col].pct_change()
    
    return combined_df



def add_signals(df : pd.DataFrame, 
                short_win : int = 50, 
                long_win : int = 200,
                rsi_period : int = 14,
                rsi_buy : int = 30,
                rsi_sell : int = 70,
                strat : str = "mavg") -> pd.DataFrame :
    """
    Add trading signals to the DataFrame based on moving averages.

    Parameters:
    df (pd.DataFrame): Input DataFrame with stock prices.
    short_ma (int): size for short-term moving average.
    long_ma (int): size for long-term moving average.

    Returns:
    pd.DataFrame: DataFrame with added trading signals.
    """
    if strat == "buy and hold":
        df = df.copy()
        df['signal'] = 1
        df['pos'] = df['signal'].shift(1).fillna(0)
        return df

    if strat == "mavg":
        df = df.copy()
        df['short_ma'] = df['Close'].rolling(short_win).mean()
        df['long_ma'] = df['Close'].rolling(long_win).mean()
        df['signal'] = 0
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
        df['pos'] = df['signal'].shift(1).fillna(0)
        return df

    if strat == "rsi":
        df = df.copy()
        df['rsi'] = rsi_pandas_vect(df['Close'], period=rsi_period)
        df['signal'] = 0
        df.loc[df['rsi'] < rsi_buy, 'signal'] = 1
        df.loc[df['rsi'] > rsi_sell, 'signal'] = -1
        df['pos'] = df['signal'].shift(1).fillna(0)
        return df
    
    if strat == "momentum":
        df = momentum_signals(df)
        return df

def add_signals_per_stock(df: pd.DataFrame,
                          stock_list: list[str]) -> pd.DataFrame:
    for stock in stock_list:
        stock_df = df[df['Ticker'] == stock]
        stock_df = add_signals(stock_df)
        stock_df = find_returns(stock_df)
        df.update(stock_df)
    # Equal-weighted portfolio returns (daily)
    port_returns = (
        df.pivot(index='Date', columns='Ticker', values='strat_rtn')  
        .mean(axis=1)                                                # 1/n weighting
        .rename('portfolio_daily_ret')
    )
    # Cumulative
    port_cumulative = (1 + port_returns).cumprod().rename('port_cumulative_rtn')

    # merge cululative returns into df
    df = df.merge(
    port_cumulative.to_frame(),
    left_on='Date',
    right_index=True,
    how='left'
    )
    
    return df

def rsi_pandas_vect(close : pd.Series,
                    period : int = 14,
                    # fillna : bool = False,
                   ) -> pd.Series:
    """
    Vectorized RSI with Wilder's smoothing
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta< 0, 0.0)
    avg_gain = gain.rolling(window = period, min_periods = period).mean()
    avg_loss = loss.rolling(window = period, min_periods = period).mean()
    #EMA smoothing
    avg_gain = avg_gain.where(
        avg_gain.isna(),
        gain.ewm(com = period - 1, min_periods = period, adjust = False).mean()
    )
    avg_loss = avg_loss.where(
        avg_loss.isna(),
        loss.ewm(com = period - 1, min_periods = period, adjust = False).mean()
    )
    rs = avg_gain /avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def momentum_signals(
    df: pd.DataFrame,
    lookback: int = 126,
    threshold: float = 0.0,
    top_n: int = None,
    rebalance_freq: str = 'M' #monthly or quarterly
) -> pd.DataFrame:
    "Vectorized momentum : adds momentum (ROC)"
    df = df.copy()
    df['momentum'] = df['Close'] / df['Close'].shift(lookback) - 1
    if top_n is None:
        df['signal'] = np.where(df['momentum'] > threshold,1 ,0)
    else:
        df['period'] = df.index.get_level_values(0).to_period(rebalance_freq)
        df['rank'] = df.groupby('period')['momentum'].rank(ascending = False, pct = False)
        df['signal'] = np.where(df['rank'] <= top_n, 1, 0)

    df['pos'] = df['signal'].shift(1).fillna(0)
    return df

def find_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily returns and strategy returns.

    Parameters:
    df (pd.DataFrame): Input DataFrame with stock prices and signals.

    Returns:
    pd.DataFrame: DataFrame with added returns columns.
    """
    df = df.copy()
    df = df.dropna()
    df['strat_rtn'] = df['Close'].pct_change()
    df['cumulative_rtn'] = (1 + df['strat_rtn']).cumprod()
    
    return df

