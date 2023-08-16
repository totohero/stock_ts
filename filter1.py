import pandas as pd
import talib

def calculate_rsi(df, period=14):
    return talib.RSI(df['close'], timeperiod=period)

def calculate_macd_oscillator(df):
    _, _, macd_oscillator = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    return macd_oscillator


def rsi_and_macd_condition(df):
    rsi = calculate_rsi(df)
    macd_oscillator = calculate_macd_oscillator(df)
    return (rsi >= 70) & (macd_oscillator >= 0)

def filter_stocks(df):
    return df[rsi_and_macd_condition(df)]
