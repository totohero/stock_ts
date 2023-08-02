import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Connect to the SQLite database
conn = sqlite3.connect('stock_prices.db')

# Read the DataFrame from the SQLite database
df = pd.read_sql('SELECT * FROM prices', conn)

# Convert date to datetime and set it as index
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Calculate the rolling 20 days max close price and max volume
df['rolling_max_close'] = df.groupby('ticker')['close'].rolling(window=50).max().reset_index(0, drop=True)
df['rolling_max_volume'] = df.groupby('ticker')['volume'].rolling(window=50).max().reset_index(0, drop=True)

# Calculate the open to close change ratio
df['open_close_change_ratio'] = df['close'] / df['open']

# Calculate the next day change ratio from open to close
df['next_day_open_close_change_ratio'] = df.groupby('ticker')['close'].shift(-1) / df.groupby('ticker')['open'].shift(-1)

# Create a figure and a set of subplots
fig, axs = plt.subplots(1, 2, figsize=(12, 6))

#
# 전체 시가/종가 scatter graph
#
axs[0].scatter(df.index, df['open_close_change_ratio'])
axs[0].set_ylim(0.7, 1.3)
axs[0].set_title('Open to close change ratio')

#
# 조건 만족하는 경우의 scatter graph
#
# Filter the rows where the conditions are met
df_filtered = df[(df['close'] == df['rolling_max_close']) & 
                 (df['volume'] == df['rolling_max_volume']) & 
                 (df['open_close_change_ratio'] > 1.1)]

# Create a scatter plot for the change ratio
axs[1].scatter(df_filtered.index, df_filtered['next_day_open_close_change_ratio'])
axs[1].set_ylim(0.7, 1.3)
axs[1].set_title('Next day open to close change ratio')
plt.show()
