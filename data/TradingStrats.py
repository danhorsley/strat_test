import pandas as pd
import numpy as np

class TradingStrategy():
    """Base class for all strategies"""
    name: str = "Unspecified strategy"
    description: str = ""

    def __init__(self,**kwargs):
        self.params = kwargs

    #abstract method
    def compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main method: takes long-format df and returns df with at least 'signal' 
        and 'pos' columns added.
        """
        pass

    def compute_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes return - same for all strategies.
        """
        df = df.copy()
        df['strat_rtn'] = df['pos'] * df['returns']
        df['cumulative_rtn'] = (1+ df['strat_rtn']).cumprod()
        return df

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Combines signals and returns in chain.
        """
        df = df.self.compute_signals(df)
        return self.compute_returns(df)
    
class BuyAndHold(TradingStrategy):
    name = "Buy & Hold"
    description = "Passive benchmark - always long"

    def compute_signals(self, df:pd.DataFrame) -> pd.DataFrame:
        df['signal'] = 1
        df['pos'] = 1
        return df
    
class MovingAverageCrossover(TradingStrategy):
    name = "MA Crossover"
    description = "Classic trend-following : Long when shorter MA is above longer MA and vice-versa."

    def __init__(self, short_win: int=50, long_win: int = 200, **kwargs):
        super().__init__(**kwargs)
        self.short_win = short_win
        self.long_win = long_win

    def compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # vectorized
        df['short_ma'] = (
            df.groupby('Ticker')['Close']
              .rolling(self.short_win, min_periods=self.short_win)
              .mean()
              .reset_index(level=0, drop=True)  # drop Ticker level from index
        )
        
        df['long_ma'] = (
            df.groupby('Ticker')['Close']
              .rolling(self.long_win, min_periods=self.long_win)
              .mean()
              .reset_index(level=0, drop=True)
        )
        
        df['signal'] = 0
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
        
        # Position still needs groupby shift (this one is unavoidable and fast)
        df['pos'] = df.groupby('Ticker')['signal'].shift(1).fillna(0)
        
        return df

class RSIMeanReversion(TradingStrategy):
    name = "RSI Oversold/Overbought"
    description = "Classic mean-reversion"

    def __init__(self, period: int = 14, buy_level: int = 30, sell_level: int=70, **kwargs):
        super().__init__(**kwargs)
        self.period = period
        self.buy_level = buy_level
        self.sell_level = sell_level

    def compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df.groupby('Ticker')['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta< 0, 0.0)
        avg_gain = gain.rolling(window = self.period, min_periods = self.period).mean()
        avg_loss = loss.rolling(window = self.period, min_periods = self.period).mean()
        #EMA smoothing
        avg_gain = avg_gain.where(
            avg_gain.isna(),
            gain.ewm(com = self.period - 1, min_periods = self.period, adjust = False).mean()
        )
        avg_loss = avg_loss.where(
            avg_loss.isna(),
            loss.ewm(com = self.period - 1, min_periods = self.period, adjust = False).mean()
        )
        rs = avg_gain /avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        df['rsi'] = rsi
        df['signal'] = 0
        df.loc[df['rsi'] < self.buy_level, 'signal'] = 1
        df.loc[df['rsi'] > self.sell_level, 'signal'] = -1
        df['pos'] = df.groupby('Ticker')['signal'].shift(1).fillna(0)
        return df

class TimeSeriesMomentum(TradingStrategy):
    name = "Momentum (ROC)"
    description = "Time-series momentum"

    def __init__(self, lookback: int = 126, threshold: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.lookback = lookback
        self.threshold = threshold

    def compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df['momentum'] = df.groupby('Ticker')['Close'].pct_change(periods = self.lookback)
        df['signal'] = np.where(['momentum'] > self.threshold, 1, 0)
        df['pos'] = df.groupby('Ticker')['signal'].shift(1).fillna(0)
        return df
