import talib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit

def plot_adx_vs_max_5day_return(df):
    # Calculate ADX
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'])

    # Calculate the maximum close price over the next 5 days
    df['5_day_max_return'] = df['close'].shift(-1).rolling(window=5, min_periods=1).max()

    # Bin ADX values
    df['adx_bin'] = pd.cut(df['adx'], bins=20)

    # Calculate mean, variance, and count for each ADX bin
    adx_summary = df.groupby('adx_bin')['5_day_max_return'].agg(mean='mean', var='var', count='count')  # Corrected line

    # Plot the graph
    plt.figure(figsize=(10, 6))
    error_bars = plt.errorbar(x=adx_summary.index.astype(str), y=adx_summary['mean'], yerr=np.sqrt(adx_summary['var']), fmt='o')
    plt.xlabel('ADX')
    plt.ylabel('Max 5-Day Return')
    plt.title('Max 5-Day Return by ADX')
    plt.xticks(rotation=45)

    # Annotate with sample size
    for i, count in enumerate(adx_summary['count']):  # Corrected line
        x = error_bars.lines[0].get_xdata()[i]
        y = error_bars.lines[0].get_ydata()[i]
        plt.annotate(f'n={count}', (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9, color='blue')

    # plt.show()
    streamlit.pyplot(plt)
