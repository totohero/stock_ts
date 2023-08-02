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

# Remove rows where 'open' or 'close' is zero
df = df[(df['open'] != 0) & (df['close'] != 0)]

# Calculate the rolling 20 days max close price and max volume
df['max_close_20'] = df.groupby('ticker')['close'].rolling(window=50).max().reset_index(0, drop=True)
df['max_volume_20'] = df.groupby('ticker')['volume'].rolling(window=50).max().reset_index(0, drop=True)
# Calculate the 5 days and 20 days moving averages for the close prices
df['MA5'] = df.groupby('ticker')['close'].rolling(window=5).mean().reset_index(0, drop=True)
df['MA10'] = df.groupby('ticker')['close'].rolling(window=10).mean().reset_index(0, drop=True)
df['MA20'] = df.groupby('ticker')['close'].rolling(window=20).mean().reset_index(0, drop=True)

# Calculate the open to close change ratio
df['open_close_change_ratio'] = df['close'] / df['open']

# Calculate the next day change ratio from open to close
df['next_day_open_close_change_ratio'] = df.groupby('ticker')['close'].shift(-1) / df.groupby('ticker')['open'].shift(-1)
df = df.dropna(subset=['next_day_open_close_change_ratio'])

# Create a figure and a set of subplots
fig, axs = plt.subplots(1, 3, figsize=(18, 6))

#
# 전체 시가/종가 histogram
#
axs[0].hist(df['open_close_change_ratio'].dropna(), bins=60, color='g', alpha=0.5, edgecolor='black', range=(0.7, 1.3))
axs[0].set_title('Open to Close Change Ratio')
axs[0].set_xlabel('Change Ratio')
axs[0].set_ylabel('Frequency')

#
# 조건 만족하는 경우의 histogram
#
# Filter the rows where the conditions are met
df_filtered = df[(df['close'] == df['max_close_20']) & 
                (df['volume'] == df['max_volume_20']) & 
                (df['open_close_change_ratio'] > 1.1)]

# Create a histogram for the change ratio
axs[1].hist(df_filtered['next_day_open_close_change_ratio'].dropna(), bins=60, color='b', alpha=0.5, edgecolor='black', range=(0.7, 1.3))
axs[1].set_title('Next Day Open to Close Change Ratio')
axs[1].set_xlabel('Change Ratio')
axs[1].set_ylabel('Frequency')

#
# 조건 만족하는 경우의 histogram (including MA5 > MA10 > MA20)
#
# Filter the rows where the conditions are met
df_filtered2 = df[(df['close'] == df['max_close_20']) & 
                (df['volume'] == df['max_volume_20']) & 
                (df['open_close_change_ratio'] > 1.1) & 
                (df['MA5'] > df['MA10']) & 
                (df['MA10'] > df['MA20'])]

# Create a histogram for the change ratio
axs[2].hist(df_filtered2['next_day_open_close_change_ratio'].dropna(), bins=60, color='r', alpha=0.5, edgecolor='black', range=(0.7, 1.3))
axs[2].set_title('Next Day Open to Close Change Ratio\n(MA5 > MA10 > MA20)')
axs[2].set_xlabel('Change Ratio')
axs[2].set_ylabel('Frequency')

plt.tight_layout()
plt.show()