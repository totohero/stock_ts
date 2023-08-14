import load_db
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st

# 종목별로 이후 5일간의 최고 수익률과 최저 수익률을 계산하는 함수
@st.cache_data
def calculate_return(df):
    # 이후 5일간의 수익률 계산
    next_5_days_returns = [100 * df['close'].pct_change(periods=i).shift(-i) for i in range(1, 6)]
    
    # 이후 5일간의 최고 수익률
    df['max_return_next_5_days'] = pd.concat(next_5_days_returns, axis=1).max(axis=1)
    
    # 이후 5일간의 최저 수익률
    df['min_return_next_5_days'] = pd.concat(next_5_days_returns, axis=1).min(axis=1)
    
    return df

@st.cache_data
def calculate_frequency(df):
    # 종목별로 위의 함수를 적용
    result_df = df.groupby('ticker').apply(calculate_return)

    # 필요한 컬럼만 선택
    result_df = result_df[['ticker', 'date', 'max_return_next_5_days', 'min_return_next_5_days']]

    # x, y 축 범위를 정의 (필요에 따라 조정)
    x_bins = np.linspace(-10, 10, 21) # 최고 수익률 범위
    y_bins = np.linspace(-10, 10, 21) # 최저 수익률 범위

    # 히트맵을 그릴 데이터 준비 (max_return_next_5_days, min_return_next_5_days)
    heatmap_data = result_df[['max_return_next_5_days', 'min_return_next_5_days']]

    # x, y 축을 빈으로 나눕니다.
    heatmap_data['x_bin'] = pd.cut(heatmap_data['max_return_next_5_days'], x_bins)
    heatmap_data['y_bin'] = pd.cut(heatmap_data['min_return_next_5_days'], y_bins)

    # 피벗 테이블을 사용하여 빈도를 계산합니다.
    frequency_table = pd.pivot_table(heatmap_data, index='y_bin', columns='x_bin', values='max_return_next_5_days', aggfunc='count', fill_value=0)
    return frequency_table

def doit():
    # Read the DataFrame from the SQLite database
    df = load_db.load_data()

    frequency_table = calculate_frequency(df)

    # 히트맵 그리기
    plt.figure(figsize=(10, 8))
    sns.heatmap(frequency_table, cmap='YlGnBu', annot=False, fmt='d')
    plt.title('Distribution of Max & Min Returns over the Next 5 Days')
    plt.xlabel('Max Return Next 5 Days')
    plt.ylabel('Min Return Next 5 Days')
    # plt.show()
    st.write(frequency_table)

    # Streamlit에 플롯 출력
    st.pyplot(plt)

if __name__ == "__main__":
    doit()