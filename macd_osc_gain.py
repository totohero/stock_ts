import plot_factor_vs_return
import talib

def normalize_macd_oscillator(df):
    # MACD 오실레이터 계산
    macd_line, signal_line, macd_oscillator = talib.MACD(df['close'])

    # MACD 오실레이터의 최대 및 최소 값 찾기
    max_value = macd_oscillator.max()
    min_value = macd_oscillator.min()

    # MACD 오실레이터 정규화
    normalized_macd_oscillator = (macd_oscillator - min_value) / (max_value - min_value)

    return normalized_macd_oscillator

def plot_macd_oscillator_vs_5day_return(df):
    plot_factor_vs_return.plot_factor_vs_5day_return(df, 'MACD Oscillator', normalize_macd_oscillator)
