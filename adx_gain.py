import pandas as pd
import numpy as np
import streamlit
import talib
import matplotlib.pyplot as plt

def plot_adx_vs_5day_return(df):
    # Calculate ADX
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'])

    df = df[df['close'] != 0]
    df.dropna(inplace=True)
    # Calculate the maximum close price over the next 5 days
    df['5_day_max_return'] = 100 * df['close'].shift(-1).rolling(window=5, min_periods=1).max() / df['close'] - 100
    
    # Calculate the minimum close price over the next 5 days
    df['5_day_min_return'] = 100 * df['close'].shift(-1).rolling(window=5, min_periods=1).min() / df['close'] - 100
    df = df[df['5_day_max_return'] > -50]
    df = df[df['5_day_max_return'] < 50]
    df = df[df['5_day_min_return'] > -50]
    df = df[df['5_day_min_return'] < 50]
    # Bin ADX values
    df['adx_bin'] = pd.cut(df['adx'], bins=20)

    # Calculate mean for max and min returns for each ADX bin
    adx_summary = df.groupby('adx_bin')[['5_day_max_return', '5_day_min_return']].agg(['mean', 'var'])

    # Plot the graph
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot max return
    ax.plot(adx_summary.index.astype(str), adx_summary['5_day_max_return']['mean'], marker='o', color='blue', label='Max 5-Day Return')
    ax.bar(adx_summary.index.astype(str), adx_summary['5_day_max_return']['var'], alpha=0.2, color='blue') # 분산 바 플롯
    
    # Plot min return
    ax.plot(adx_summary.index.astype(str), adx_summary['5_day_min_return']['mean'], marker='o', color='red', label='Min 5-Day Return')
    ax.bar(adx_summary.index.astype(str), adx_summary['5_day_min_return']['var'], alpha=0.2, color='red') # 분산 바 플롯

    ax.set_xlabel('ADX')
    ax.set_ylabel('5-Day Return (%)')
    ax.set_title('Max and Min 5-Day Return by ADX')
    plt.xticks(rotation=45)
    plt.legend()

    streamlit.pyplot(plt)
