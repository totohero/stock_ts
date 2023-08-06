import sqlite3
import pandas as pd

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
df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
df_ticker = df.groupby('ticker')

import pandas as pd
import matplotlib.pyplot as plt

# 가정: df는 'open', 'high', 'low'와 'close' 컬럼을 가진 데이터프레임이며, 
# 각 행은 하루의 시가(open), 최고가(high), 최저가(low)와 종가(close)를 나타냅니다.

df['prev_close'] = df['close'].shift(1)  # 이전 행의 'close' 값을 가져옵니다.
df['open_change'] = (df['open'] - df['prev_close']) / df['prev_close']
df['high_change'] = 100*(df['high'] - df['open']) / df['open']
df['low_change'] = 100*(df['low'] - df['open']) / df['open']

# 전날 종가 대비 당일 시가가 3% 이상 하락한 날들을 선택합니다.
df_significant_drop = df[df['open_change'] <= -0.05]

# 당일 시가 대비 최고가와 최저가의 변화율의 히스토그램을 그립니다.
df_significant_drop['high_change'].hist(bins=100, alpha=0.3, label='High Change', edgecolor='black', range=(-30, 30))
df_significant_drop['low_change'].hist(bins=100, alpha=0.3, label='Low Change', edgecolor='black', range=(-30, 30))
plt.title('Distribution of High and Low Change on Days with >3% Open Drop')
plt.xlabel('Change')
plt.ylabel('Frequency')
plt.legend(loc='upper right')
plt.show()
