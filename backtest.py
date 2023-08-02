import sqlite3
import pandas as pd
import numpy as np

class Backtest:
    def __init__(self, db_path, preprocess, buy_strategy, sell_strategy, hold_days=None, target_return=None, stop_loss=None):
        self.conn = sqlite3.connect(db_path)
        self.preprocess = preprocess
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.hold_days = hold_days
        self.target_return = target_return
        self.stop_loss = stop_loss

    def load_data(self):
        df = pd.read_sql('SELECT * FROM prices', self.conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = self.preprocess(df)
        return df

    def run(self, df):
        df['in_trade'] = False
        df['pnl'] = 0.0
        df = self.buy_strategy(df)
        df = self.sell_strategy(df)
        entry_price = 0.0
        for i in range(1, len(df)):
            if df['buy_signal'].iloc[i]:
                df['in_trade'].iloc[i] = True
                entry_price = df['close'].iloc[i]
            elif df['in_trade'].iloc[i-1]:
                if self.stop_loss is not None and df['low'].iloc[i] / entry_price - 1 <= self.stop_loss:
                    df['in_trade'].iloc[i] = False
                    df['pnl'].iloc[i] = self.stop_loss
                else:
                    if self.target_return is not None and df['high'].iloc[i] / entry_price - 1 >= self.target_return:
                        df['in_trade'].iloc[i] = False
                        df['pnl'].iloc[i] = self.target_return
                    elif self.hold_days is not None and df['in_trade'].shift(self.hold_days).iloc[i]:
                        df['in_trade'].iloc[i] = False
                        df['pnl'].iloc[i] = df['close'].iloc[i] / entry_price - 1
                    elif df['sell_signal'].iloc[i]:
                        df['in_trade'].iloc[i] = False
                        df['pnl'].iloc[i] = df['close'].iloc[i] / entry_price - 1

        trades = df['in_trade'].sum()
        print(f'Ticker: {df.name}, Accumulated profit or loss: {df["pnl"].sum() * 100:.2f}% over {trades} trades')
        return df

    def start(self):
        df = self.load_data()
        df = df.groupby('ticker').apply(self.run)
        total_pnl = df['pnl'].sum()
        print(f'Total profit or loss: {total_pnl * 100:.2f}%')
