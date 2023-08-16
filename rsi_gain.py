import pandas as pd
import numpy as np
import streamlit
import talib
import matplotlib.pyplot as plt

def plot_rsi_vs_max_5day_return(df):
    # Calculate RSI
    df['rsi'] = talib.RSI(df['close'])

    # Calculate the maximum close price over the next 5 days
    df['5_day_max_return'] = df['close'].shift(-1).rolling(window=5, min_periods=1).max()

    # Bin RSI values
    df['rsi_bin'] = pd.cut(df['rsi'], bins=100)

    # Calculate mean and variance for each RSI bin
    rsi_summary = df.groupby('rsi_bin')['5_day_max_return'].agg(['mean', 'var'])

    # Plot the graph
    plt.figure(figsize=(10, 6))
    plt.errorbar(x=rsi_summary.index.astype(str), y=rsi_summary['mean'], yerr=np.sqrt(rsi_summary['var']), fmt='o')
    plt.xlabel('RSI')
    plt.ylabel('Max 5-Day Return')
    plt.title('Max 5-Day Return by RSI')
    plt.xticks(rotation=45)
    # plt.show()
    streamlit.pyplot(plt)

