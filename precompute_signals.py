import pandas as pd
from pathlib import Path
from TradingStrats import STRATEGY_REGISTRY, get_strategy, BuyAndHold, MovingAverageCrossover, RSIMeanReversion, TimeSeriesMomentum
from WrangleData import wrangle_data

DATA_DIR = Path("data")
OUTPUT_PARQUET = Path("precomputed_signals.parquet")

def precompute_signals():
    tickers = [f.stem for f in DATA_DIR.glob("*.csv")]
    df = wrangle_data(tickers)
    strategies = {
        "buy_and_hold": BuyAndHold(),
        "mavg_50_200": MovingAverageCrossover(short_win=50, long_win=200),
        "rsi_14_30_70": RSIMeanReversion(period=14, buy_level=30, sell_level=70),
        "momentum_126_0": TimeSeriesMomentum(lookback=126, threshold=0.0),
    }
    
    results_dfs = []
    
    for name, strat in strategies.items():
        strat_df = strat.run(df.copy())
        keep_cols = ['Date', 'Ticker', 'Close', 'signal', 'pos', 'strat_rtn', 'cumulative_rtn']
        strat_df = strat_df[keep_cols]
        strat_df = strat_df.rename(columns={
            'signal': f'signal_{name}',
            'pos': f'pos_{name}',
            'strat_rtn': f'strat_rtn_{name}',
            'cumulative_rtn': f'cumulative_rtn_{name}'
            # 'strat_cumulative_rtn': f'strat_cumulative_rtn_{name}'
        })
        results_dfs.append(strat_df)
        
        # Merge all strategies on data and ticker
        df_all = results_dfs[0]
        for other in results_dfs[1:]:
            df_all = df_all.merge(
                other.drop(columns=['Close']),
                on = ['Date', 'Ticker'],
                how = 'outer'
            )
    df_all = df_all.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    df_all.to_parquet(OUTPUT_PARQUET, index=False, compression='snappy')

if __name__ == "__main__":
    precompute_signals()