import pandas as pd

def wrangle_data(selected_stocks: list[str]) -> pd.DataFrame:
    all_data = []
    
    for stock in selected_stocks:
        df = pd.read_csv(f"data/{stock}.csv")
        
        # Sort just in case
        df = df.sort_values('Date')
        
        # Normalize
        price_col = 'Close'
        df[price_col] = pd.to_numeric(df[price_col], downcast='float')
        df[price_col] = df[price_col] / df[price_col].iloc[0]
        
        df['Ticker'] = stock
        all_data.append(df)
    
    combined = pd.concat(all_data, ignore_index=True)
    
    # tidy index and confirm sort
    combined = combined.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    
    return combined