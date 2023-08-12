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

# Calculate the previous close price
df['prev_close'] = df.groupby('ticker')['close'].shift(1)

# Apply the condition
df_filtered = df[df['open'] <= df['prev_close'] * 0.95]

# Calculate the change ratios
df_filtered['close_change_ratio'] = 100 * df_filtered['close'] / (df_filtered['prev_close'] * 0.95) - 100
df_filtered['low_change_ratio'] = 100 * df_filtered['low'] / (df_filtered['prev_close'] * 0.95) - 100
df_filtered.dropna(inplace=True)

# 위에 위치할 텍스트
st.header("Top Section")
st.write("This is the top section of the page.")

# Create a 2D histogram
plt.figure(figsize=(10, 4))
sns.histplot(data=df_filtered, x='close_change_ratio', y='low_change_ratio', bins=10, cmap="Blues")
plt.xlim(-10, 10)
plt.ylim(-10, 0)
plt.title('2D Histogram of Change Ratios')
plt.xlabel('Close Change Ratio (5% below previous close)')
plt.ylabel('Low Change Ratio (5% below previous close)')

st.pyplot(plt.gcf())

# Binning을 적용하여 2D 히스토그램을 계산합니다.
# close_change와 low_change를 빈으로 나눕니다.
df_filtered['close_change_bin'] = pd.cut(df_filtered['close_change_ratio'], np.linspace(-10, 10, 11))
df_filtered['low_change_bin'] = pd.cut(df_filtered['low_change_ratio'], np.linspace(-10, 0, 11))

# 피벗 테이블을 사용하여 빈도를 계산합니다.
frequency_table = pd.pivot_table(df_filtered, index='low_change_bin', columns='close_change_bin', values='open', aggfunc='count', fill_value=0)

# 표를 출력합니다.
print(frequency_table)

# Display the plot in Streamlit
st.table(frequency_table)
