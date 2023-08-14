import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import load_db

def doit():
    # Read the DataFrame from the SQLite database
    df = load_db.load_data()

    # Convert date to datetime and set it as index
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

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
    filtered_df = df[df['prev_close-low'] <= -0.1]

    # close_change와 low_change를 빈으로 나눕니다.
    filtered_df['close_change_bin'] = pd.cut(filtered_df['close_change'], np.linspace(0, 20, 21))
    filtered_df['low_change_bin'] = pd.cut(filtered_df['low_change'], np.linspace(-20, 0, 21))

    # 피벗 테이블을 사용하여 빈도를 계산합니다.
    frequency_table = pd.pivot_table(filtered_df, index='low_change_bin', columns='close_change_bin', values='open', aggfunc='count', fill_value=0)

    # 표를 출력합니다.
    print(frequency_table)

    import seaborn as sns

    # 히트맵을 그립니다.
    plt.figure(figsize=(10, 8))
    sns.heatmap(frequency_table, cmap="YlGnBu", annot=True)
    plt.title('Close Change vs Low Change Frequency')
    plt.xlabel('Close Change')
    plt.ylabel('Low Change')
    plt.show()

    # print table of distribution of High and Low Change on Days with >3% Open Drop with binning applied
    import numpy as np

    # -2에서 2 사이의 high_change와 low_change를 제외합니다.
    filtered_df = df_significant_drop

    # 빈의 경계를 정의합니다. 여기서는 예를 들어 -30에서 30 사이에 100개의 빈을 사용합니다.
    bins = np.linspace(-30, 30, 101)

    # high_change와 low_change를 빈으로 나눕니다.
    filtered_df['high_change_bin'] = pd.cut(filtered_df['high_change'], bins)
    filtered_df['low_change_bin'] = pd.cut(filtered_df['low_change'], bins)

    # 피벗 테이블을 사용하여 빈도를 계산합니다.
    frequency_table = pd.pivot_table(filtered_df, index='low_change_bin', columns='high_change_bin', values='open', aggfunc='count', fill_value=0)

    # 표를 출력합니다.
    print(frequency_table)