import streamlit as st
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Connect to the SQLite database
conn = sqlite3.connect('stock_prices.db')

# Read the DataFrame from the SQLite database
df = pd.read_sql('SELECT * FROM prices', conn)
df['date'] = pd.to_datetime(df['date'])

# Sidebar date selection
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date = st.sidebar.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date)

# Filter the DataFrame by the selected date range
df = df[(df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))]

# Apply additional conditions
# Calculate the rolling 20 days max close price and max volume
window = 20
df['rolling_max_close'] = df.groupby('ticker')['close'].rolling(window=window).max().reset_index(0, drop=True)
df['rolling_max_volume'] = df.groupby('ticker')['volume'].rolling(window=window).max().reset_index(0, drop=True)

# Filter based on conditions
df_filtered = df[
    (df['close'] == df['rolling_max_close']) &
    (df['volume'] == df['rolling_max_volume']) &
    ((df['close'] / df['open']) >= 1.07)
]

# Calculate the next day open to close change ratio
df_filtered['next_day_open_close_change_ratio'] = df_filtered.groupby('ticker')['close'].shift(-1) / df_filtered.groupby('ticker')['open'].shift(-1)
df_filtered['open_close_change_ratio'] = df_filtered['close'] / df_filtered['open']
df_filtered = df_filtered.dropna(subset=['next_day_open_close_change_ratio', 'open_close_change_ratio'])

# Create a 2D heatmap
plt.figure(figsize=(10, 4))
sns.kdeplot(data=df_filtered, x='next_day_open_close_change_ratio', y='open_close_change_ratio', cmap="Blues", fill=True)
plt.xlim(0.9, 1.1)
plt.ylim(1, 1.2)
plt.title('2D Heatmap of Change Ratios')
plt.xlabel('Next Day Open to Close Change Ratio')
plt.ylabel('Open to Close Change Ratio')

# Display the plot in Streamlit
st.pyplot(plt.gcf())
