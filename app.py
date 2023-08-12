import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

@st.cache_data
def load_data():
    conn = sqlite3.connect('stock_prices.db')
    df = pd.read_sql('SELECT * FROM prices', conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# Sidebar date selection
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date = st.sidebar.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date)

# Filter the DataFrame by the selected date range
df = df[(df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))]

# Remove rows where 'open' or 'close' is zero
df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
df_ticker = df.groupby('ticker')

df['prev_close'] = df['close'].shift(1)
df['prev_close-low'] = (df['low'] - df['prev_close']) / df['prev_close']
df['buy'] = df['prev_close'] * 0.9
df['close_change'] = 100 * (df['close'] - df['buy'] ) / df['buy']
df['low_change'] = 100 * (df['low'] - df['buy'] ) / df['buy']
df.dropna(inplace=True)

# 전날 종가 대비 10% 이상 하락한 날들을 선택합니다.
df_filtered = df[df['prev_close-low'] <= -0.1]

# close_change와 low_change를 빈으로 나눕니다.
df_filtered['close_change_bin'] = pd.cut(df_filtered['close_change'], np.linspace(-20, 20, 41))
df_filtered['low_change_bin'] = pd.cut(df_filtered['low_change'], np.linspace(-20, 0, 21))


# 위에 위치할 텍스트
st.header("Top Section")
st.write("This is the top section of the page.")

# Create a 2D histogram
plt.figure(figsize=(10, 4))
sns.histplot(data=df_filtered, x='close_change', y='low_change', bins=100, cmap="Blues")
plt.xlim(-20, 20)
plt.ylim(-20, 0)
plt.title('2D Histogram of Change Ratios')
plt.xlabel('Close Change Ratio (5% below previous close)')
plt.ylabel('Low Change Ratio (5% below previous close)')
st.pyplot(plt.gcf())

# 피벗 테이블을 사용하여 빈도를 계산합니다.
frequency_table = pd.pivot_table(df_filtered, index='low_change_bin', columns='close_change_bin', values='open', aggfunc='count', fill_value=0)

# 표를 출력합니다.
# st.table(frequency_table)
print(frequency_table)
