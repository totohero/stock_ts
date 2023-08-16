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
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot mean (max and min return) on the primary y-axis
    ax1.plot(adx_summary.index.astype(str), adx_summary['5_day_max_return']['mean'], marker='o', color='blue', label='Mean Max 5-Day Return')
    ax1.plot(adx_summary.index.astype(str), adx_summary['5_day_min_return']['mean'], marker='o', color='red', label='Mean Min 5-Day Return')
    ax1.set_xlabel('ADX')
    ax1.set_ylabel('Mean 5-Day Return (%)')
    ax1.legend(loc='upper left')
    ax1.set_title('Max and Min 5-Day Return by ADX')
    plt.xticks(rotation=45)

    # Create a secondary y-axis to plot variance
    ax2 = ax1.twinx()
    ax2.bar(adx_summary.index.astype(str), adx_summary['5_day_max_return']['var'], alpha=0.2, color='blue') # 분산 바 플롯 (Max Return)
    ax2.bar(adx_summary.index.astype(str), adx_summary['5_day_min_return']['var'], alpha=0.2, color='red') # 분산 바 플롯 (Min Return)
    ax2.set_ylabel('Variance of 5-Day Return')

    streamlit.pyplot(plt)
