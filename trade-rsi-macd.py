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

# Calculate the rolling 20 days max close price and max volume
df['max_close_20'] = df_ticker['close'].rolling(window=50).max().reset_index(0, drop=True)
df['max_volume_20'] = df_ticker['volume'].rolling(window=50).max().reset_index(0, drop=True)
# Calculate the 5 days and 20 days moving averages for the close prices
df['MA5'] = df_ticker['close'].rolling(window=5).mean().reset_index(0, drop=True)
df['MA10'] = df_ticker['close'].rolling(window=10).mean().reset_index(0, drop=True)
df['MA20'] = df_ticker['close'].rolling(window=20).mean().reset_index(0, drop=True)

# Calculate the open to close change ratio
df['open_close_change_ratio'] = df['close'] / df['open']

# Calculate the next day change ratio from open to close
df['+1d_open_close_change_ratio'] = df_ticker['close'].shift(-1) / df_ticker['open'].shift(-1)
# df = df.dropna(subset=['+1d_open_close_change_ratio'])
df['+5d_open_close_change_ratio'] = df_ticker['close'].shift(-5) / df_ticker['open'].shift(-1)
# df = df.dropna(subset=['+5d_open_close_change_ratio'])


df = df[(df['MA5'] > df['MA10']) & (df['MA10'] > df['MA20'])]

# Group by date and calculate the 90th percentile for each date
turnover_threshold = df.groupby('date')['transaction_amount'].quantile(0.9)
df_top_10_percent_turnover = df[df.groupby('date')['transaction_amount'].transform(lambda x: x >= x.quantile(0.9))]

def plot_histogram(df, ax, filter_func, title):
    df_filtered = df[filter_func(df)]
    ax.hist(df_filtered['+5d_open_close_change_ratio'].dropna(), bins=60, color='r', alpha=0.5, edgecolor='black', range=(0.7, 1.3))
    ax.set_title(title)
    ax.set_xlabel('Change Ratio')
    ax.set_ylabel('Frequency')

    avg_change_ratio = df_filtered['+1d_open_close_change_ratio'].mean()
    print(f"Average Change Ratio for {title}: {avg_change_ratio:.4f}")

fig, axs = plt.subplots(1, 5, figsize=(18, 6))

filter_func = lambda df: df['open_close_change_ratio'].notna()
plot_histogram(df, axs[0], filter_func, 'Day0 Change Ratio')

filter_func = lambda df: (df['close'] == df['max_close_20']) & (df['volume'] == df['max_volume_20']) & (df['open_close_change_ratio'] > 1.1)
plot_histogram(df, axs[1], filter_func, 'Change Ratio\n(Close == Max Close Price)\n(Volume == Max Volume Price)\n(Open to Close Change Ratio > 1.1)')

filter_func = lambda df: df['close'] > 0
plot_histogram(df, axs[2], filter_func, 'Change Ratio\n(MA5 > MA10 > MA20)')

filter_func = lambda df: df['close'] > 0
plot_histogram(df_top_10_percent_turnover, axs[3], filter_func, 'Top 10 % turnover. Change Ratio\n(MA5 > MA10 > MA20)')

# Define the function to calculate RSI
def calculate_rsi(df, window):
    delta = df['close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    average_gain = up.rolling(window).mean()
    average_loss = abs(down.rolling(window).mean())
    rs = average_gain / average_loss
    df['RSI'] = 100 - (100 / (1 + rs))

# Define the function to calculate MACD
def calculate_macd(df, short_window, long_window):
    short_ema = df['close'].ewm(span=short_window, adjust=False).mean()
    long_ema = df['close'].ewm(span=long_window, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    df['MACD'] = macd_line - signal_line

# Calculate RSI and MACD
calculate_rsi(df, window=14)
calculate_macd(df, short_window=12, long_window=26)

filter_func = lambda df: (df['RSI'] > 70) & (df['MACD'] > 0)
plot_histogram(df, axs[4], filter_func, 'RSI > 70 and MACD > 0')

plt.tight_layout()
plt.show()
