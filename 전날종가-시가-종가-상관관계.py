import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Connect to the SQLite database
conn = sqlite3.connect('stock_prices.db')

# Read the DataFrame from the SQLite database
df = pd.read_sql('SELECT * FROM prices', conn)

# Convert date to datetime and set it as index
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Remove rows where 'open' or 'close' is zero
df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
df_ticker = df.groupby('ticker')

df['prev_close'] = df['close'].shift(1)
df['open_change'] = (df['open'] - df['prev_close']) / df['prev_close']
df['buy'] = df['prev_close'] * 0.95
df['high_change'] = 100 * (df['high'] - df['buy'] ) / df['buy']
df['low_change'] = 100 * (df['low'] - df['buy'] ) / df['buy']
df.dropna(inplace=True)

# 전날 종가 대비 당일 시가가 5% 이상 하락한 날들을 선택합니다.
filtered_df = df[df['open_change'] <= -0.05]

# high_change와 low_change를 빈으로 나눕니다.
filtered_df['high_change_bin'] = pd.cut(filtered_df['high_change'], np.linspace(0, 20, 21))
filtered_df['low_change_bin'] = pd.cut(filtered_df['low_change'], np.linspace(-20, 0, 21))

# 피벗 테이블을 사용하여 빈도를 계산합니다.
frequency_table = pd.pivot_table(filtered_df, index='low_change_bin', columns='high_change_bin', values='open', aggfunc='count', fill_value=0)

# 표를 출력합니다.
print(frequency_table)

import seaborn as sns

# 히트맵을 그립니다.
plt.figure(figsize=(10, 8))
sns.heatmap(frequency_table, cmap="YlGnBu", annot=True)
plt.title('High Change vs Low Change Frequency')
plt.xlabel('High Change')
plt.ylabel('Low Change')
plt.show()
