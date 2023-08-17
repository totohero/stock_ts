import pandas as pd
import numpy as np
import streamlit
import talib
import matplotlib.pyplot as plt

def plot_factor_vs_5day_return(df, factor_name, factor_func, bins=20):
    # Calculate the specified factor (e.g., RSI, ADX)
    df[factor_name] = factor_func(df)

    # Drop rows with NaN or 0 close price
    df = df[df['close'] != 0]
    df.dropna(inplace=True)
    
    # Calculate the maximum and minimum close price over the next 5 days
    df['5_day_max_return'] = 100 * df['close'].shift(-1).rolling(window=5, min_periods=1).max() / df['close'] - 100
    df['5_day_min_return'] = 100 * df['close'].shift(-1).rolling(window=5, min_periods=1).min() / df['close'] - 100
    
    # Filter extreme returns
    df = df[(df['5_day_max_return'] > -50) & (df['5_day_max_return'] < 50)]
    df = df[(df['5_day_min_return'] > -50) & (df['5_day_min_return'] < 50)]

    # Bin the factor values
    df[f'{factor_name}_bin'] = pd.cut(df[factor_name], bins=bins)

    # Calculate mean and variance for max and min returns for each factor bin
    summary = df.groupby(f'{factor_name}_bin')[['5_day_max_return', '5_day_min_return']].agg(['mean', 'var'])

    # Plot the graph
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot mean (max and min return) on the primary y-axis
    ax1.plot(summary.index.astype(str), summary['5_day_max_return']['mean'], marker='o', color='blue', label='Mean Max 5-Day Return')
    ax1.plot(summary.index.astype(str), summary['5_day_min_return']['mean'], marker='o', color='red', label='Mean Min 5-Day Return')
    ax1.set_xlabel(factor_name)
    ax1.set_ylabel('Mean 5-Day Return (%)')
    ax1.legend(loc='upper left')
    ax1.set_title(f'Max and Min 5-Day Return by {factor_name}')
    plt.xticks(rotation=45)

    # Create a secondary y-axis to plot variance
    ax2 = ax1.twinx()
    ax2.bar(summary.index.astype(str), summary['5_day_max_return']['var'], alpha=0.2, color='blue') # 분산 바 플롯 (Max Return)
    ax2.bar(summary.index.astype(str), summary['5_day_min_return']['var'], alpha=0.2, color='red') # 분산 바 플롯 (Min Return)
    ax2.set_ylabel('Variance of 5-Day Return')

    streamlit.pyplot(plt)

