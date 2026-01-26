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

def add_signals(df : pd.DataFrame, short_win : int = 50, long_win : int = 200) -> pd.DataFrame :
    """
    Add trading signals to the DataFrame based on moving averages.

    Parameters:
    df (pd.DataFrame): Input DataFrame with stock prices.
    short_ma (int): size for short-term moving average.
    long_ma (int): size for long-term moving average.

    Returns:
    pd.DataFrame: DataFrame with added trading signals.
    """
    df = df.copy()
    df['short_ma'] = df['Close'].rolling(short_win).mean()
    df['long_ma'] = df['Close'].rolling(long_win).mean()
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
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

