import plot_factor_vs_return
import talib

# Example Usage
def calculate_adx(df):
    return talib.ADX(df['high'], df['low'], df['close'])

def plot_adx_vs_5day_return(df):
    plot_factor_vs_return.plot_factor_vs_5day_return(df, 'ADX', calculate_adx)