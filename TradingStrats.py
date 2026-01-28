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
        df['signal'] = 0
        df['pos'] = 0
        return df

    def compute_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes per-stock returns + strategy returns, then adds equal-weighted portfolio cumulative.
        Assumes df has 'Close', 'pos' (from signals), and 'Ticker' column.
        """
        df = df.copy()
    
        df['returns'] = df.groupby('Ticker')['Close'].pct_change()
        df['strat_rtn'] = df['pos'] * df['returns']
    
        # 3. Per-stock cumulative strategy return (optional, but useful for comparison)
        df['cumulative_rtn'] = (
            (1 + df['strat_rtn'])
            .groupby(df['Ticker'])
            .cumprod()
            .fillna(1)
            )
        
        # 4. Portfolio-level: equal-weighted average daily strat return per date
        #    (this is the key step for combined portfolio)
        port_daily_ret = (
            df.pivot_table(
                index='Date',
                columns='Ticker',
                values='strat_rtn',
                aggfunc='mean'          # equal weight = average across stocks
            )
            .mean(axis=1)               # final portfolio daily return
            .rename('portfolio_daily_ret')
        )
    
        # 5. Portfolio cumulative return (starts at 1)
        port_cum = (1 + port_daily_ret).cumprod().rename('port_cumulative_rtn')
    
        # 6. Merge portfolio cumulative back into the long df (broadcast per date)
        df = df.merge(
            port_cum.to_frame(),
            left_on='Date',
            right_index=True,
            how='left'
        )
    
        return df

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Combines signals and returns in chain.
        """
        df = self.compute_signals(df)
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
        df['signal'] = np.where(df['momentum'] > self.threshold, 1, 0)
        df['pos'] = df.groupby('Ticker')['signal'].shift(1).fillna(0)
        return df
    
STRATEGY_REGISTRY = {
    "buy_and_hold": BuyAndHold,
    "mavg": MovingAverageCrossover,
    "rsi": RSIMeanReversion,
    "momentum": TimeSeriesMomentum,
    # add more here later
}

def get_strategy(name: str, **params) -> TradingStrategy:
    "Factory function for clean entry point from Streamlit"
    strategy_class = STRATEGY_REGISTRY.get(name)
    if not strategy_class:
        raise ValueError("Unknown straategy: {name}")
    return strategy_class(**params)
