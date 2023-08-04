
from backtest import Backtest

def preprocess(df):
        df = df[(df['open'] != 0) & (df['close'] != 0) & (
            df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
        df['MA5'] = df.groupby('ticker')['close'].rolling(
            window=5).mean().reset_index(0, drop=True)
        df['MA10'] = df.groupby('ticker')['close'].rolling(
            window=10).mean().reset_index(0, drop=True)
        return df

def buy_strategy(df):
    df['buy_signal'] = (df['MA5'] > 1.03*df['MA10']
                        ) & (df['MA5'].shift(1) < 1.03*df['MA10'].shift(1))
    return df

def sell_strategy(df):
    df['sell_signal'] = (df['MA5'] < 0.97*df['MA10']
                            ) & (df['MA5'].shift(1) > 0.97*df['MA10'].shift(1))
    return df

starting_cash = 10000000  # 1000만원
buy_ratio = 0.1  # 10%
hold_days = 5
target_return = 0.3  # 30%
stop_loss = -0.1  # -10%

bt = Backtest('stock_prices.db', preprocess, buy_strategy, sell_strategy,
                starting_cash, buy_ratio, hold_days, target_return, stop_loss,
                begin_date='2023-01-01', end_date='2023-07-26', transaction_cost=0.00015)
bt.start()
