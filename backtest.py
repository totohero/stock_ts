import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

# Connect to the SQLite database
conn = sqlite3.connect('stock_prices.db')

# Read the DataFrame from the SQLite database
df = pd.read_sql('SELECT * FROM prices', conn)

# Convert date to datetime and set it as index
df['date'] = pd.to_datetime(df['date'])
# 2022년 이후로만 필터링 (처리 속도)
# df = df[df['date'] > '2023-01-01']

df.set_index('date', inplace=True)

# Remove rows where 'open' or 'close' or 'high' or 'low' or 'volume' is zero
df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
df_ticker = df.groupby('ticker')

# Calculate the 5 days and 20 days moving averages for the close prices
df['MA5'] = df_ticker['close'].rolling(window=5).mean().reset_index(0, drop=True)
df['MA10'] = df_ticker['close'].rolling(window=10).mean().reset_index(0, drop=True)
df['MA20'] = df_ticker['close'].rolling(window=20).mean().reset_index(0, drop=True)

def backtest(df):
    # Define the number of days to hold the stock
    hold_days = 5

    # Create a column to hold the holding period for each stock
    df['holding_period'] = 0

    # Create a column to hold the profit or loss for each trade
    df['pnl'] = 0.0

    # Create a column to hold the status of the trade (whether the stock is currently being held or not)
    df['in_trade'] = False

    # Iterate over the rows of the DataFrame
    for i in range(1, len(df)):
        # If the 5-day moving average crosses above the 10-day moving average, enter a trade
        if df['MA5'].iloc[i] > df['MA10'].iloc[i] and df['MA5'].iloc[i - 1] < df['MA10'].iloc[i - 1]:
            df['in_trade'].iloc[i] = True
            df['holding_period'].iloc[i] = 1
        # If a trade is ongoing, increment the holding period
        elif df['in_trade'].iloc[i - 1] and df['holding_period'].iloc[i - 1] < hold_days:
            df['in_trade'].iloc[i] = True
            df['holding_period'].iloc[i] = df['holding_period'].iloc[i - 1] + 1
            # If the holding period is reached, exit the trade and calculate the profit or loss
            if df['holding_period'].iloc[i] == hold_days:
                df['pnl'].iloc[i] = df['close'].iloc[i] / df['close'].iloc[i - hold_days + 1] - 1
                # print(f'Ticker: {df.name}, Buy on {df.index[i - hold_days + 1]} and sell on {df.index[i]}, Profit or loss: {df["pnl"].iloc[i] * 100:.2f}%')
    trades = df['in_trade'].sum()
    print(f'Ticker: {df.name}, Backtesting completed. Accumulated profit or loss: {df["pnl"].sum() * 100:.2f}% over {trades} trades')
    return df

# Group by ticker and apply the backtest function
df = df_ticker.apply(backtest)

# Calculate the total profit or loss
total_pnl = df['pnl'].sum()
print(f'Total profit or loss: {total_pnl * 100:.2f}%')
