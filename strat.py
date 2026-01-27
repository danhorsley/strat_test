import pandas as pd

def wrangle_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform data wrangling on the input DataFrame.

    Parameters:
    df (pd.DataFrame): Input DataFrame to be wrangled.

    Returns:
    pd.DataFrame: Wrangled DataFrame.
    """
    # Example wrangling steps
    # df = df.drop(["Ticker","Date"]) # change format of yfinance download 
    df['Close'] = pd.to_numeric(df['Close'],downcast='float')

    return df

def add_signals(df : pd.DataFrame, 
                short_win : int = 50, 
                long_win : int = 200,
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
        df['rsi'] = rsi_pandas_vect(df['Close'])
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1
        df.loc[df['rsi'] > 70, 'signal'] = -1
        df['pos'] = df['signal'].shift(1).fillna(0)
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

