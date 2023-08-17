import plot_factor_vs_return
import talib

# Example Usage
def calculate_rsi(df):
    return talib.RSI(df['close'])

def plot_rsi_vs_5day_return(df):
    plot_factor_vs_return.plot_factor_vs_5day_return(df, 'RSI', calculate_rsi)