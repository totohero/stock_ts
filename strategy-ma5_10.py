
from backtest import Backtest

def preprocess(df):
    df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
    df['MA5'] = df.groupby('ticker')['close'].rolling(window=5).mean().reset_index(0, drop=True)
    df['MA10'] = df.groupby('ticker')['close'].rolling(window=10).mean().reset_index(0, drop=True)
    return df

def buy_strategy(df):
    df['buy_signal'] = (df['MA5'] > df['MA10']) & (df['MA5'].shift(1) < df['MA10'].shift(1))
    return df

def sell_strategy(df):
    df['sell_signal'] = (df['MA5'] < df['MA10']) & (df['MA5'].shift(1) > df['MA10'].shift(1))
    return df

hold_days = 5
target_return = 0.05  # 5%
stop_loss = -0.15  # -15%

bt = Backtest('stock_prices.db', preprocess, buy_strategy, sell_strategy, hold_days, target_return, stop_loss)
bt.start()
