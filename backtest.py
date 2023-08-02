import sqlite3
import pandas as pd
import numpy as np

class Backtest:
    def __init__(self, db_path, preprocess, buy_strategy, sell_strategy, starting_cash, buy_ratio, hold_days=None, target_return=None, stop_loss=None):
        self.conn = sqlite3.connect(db_path)
        self.preprocess = preprocess
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.starting_cash = starting_cash
        self.buy_ratio = buy_ratio
        self.hold_days = hold_days
        self.target_return = target_return
        self.stop_loss = stop_loss

    def load_data(self):
        df = pd.read_sql('SELECT * FROM prices', self.conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = self.preprocess(df)
        return df

    def calculate_investment(self, cash):
        return cash * self.buy_ratio

    def execute_buy(self, df, row, cash):
        investment = self.calculate_investment(cash)
        if row['buy_signal']:
            if investment > row['close']:
                return True, investment
            else:
                return True, 0
        else:
            return False, 0

    def execute_sell(self, df, row, entry_price):
        if row['in_trade']:
            if self.stop_loss is not None and row['low'] / entry_price - 1 <= self.stop_loss:
                return False, self.stop_loss
            elif self.target_return is not None and row['high'] / entry_price - 1 >= self.target_return:
                return False, self.target_return
            elif self.hold_days is not None and row['in_trade'].shift(self.hold_days):
                pnl = row['close'] / entry_price - 1
                return False, pnl
            elif row['sell_signal']:
                pnl = row['close'] / entry_price - 1
                return False, pnl
        return row['in_trade'], row['pnl']

    def run(self, df, cash):
        result_df = df.copy()
        result_df['in_trade'] = False
        result_df['pnl'] = 0.0
        result_df = self.buy_strategy(result_df)
        result_df = self.sell_strategy(result_df)

        for date in result_df.index.unique():
            date_df = result_df.loc[date]
            for ticker in date_df['ticker'].unique():
                ticker_df = date_df[date_df['ticker'] == ticker].copy()
                entry_price = 0.0
                investment = 0.0
                for i, row in ticker_df.iterrows():
                    in_trade, investment = self.execute_buy(ticker_df, row, cash)
                    if in_trade and investment > 0:
                        entry_price = row['close']
                        cash -= investment
                    in_trade, pnl = self.execute_sell(ticker_df, row, entry_price)
                    if not in_trade and investment > 0:
                        cash += investment
                        investment = 0
                    ticker_df.loc[i, 'in_trade'] = in_trade
                    ticker_df.loc[i, 'pnl'] = pnl * investment
                result_df.loc[(date_df['ticker'] == ticker).index] = ticker_df
            print(f'{date}: Remaining cash is {cash}')
        return result_df, cash

    def start(self):
        df = self.load_data()
        df = df.sort_values(['date', 'ticker'])
        cash = self.starting_cash
        df, cash = self.run(df, cash)
        total_pnl = df['pnl'].sum() / self.starting_cash
        print(f'Total profit or loss: {total_pnl * 100:.2f}%')

if __name__ == "__main__":
    # 직접 실행되는 경우에만 수행될 코드
    def preprocess(df):
        df = df[(df['open'] != 0) & (df['close'] != 0) & (df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
        df['MA5'] = df.groupby('ticker')['close'].rolling(window=5).mean().reset_index(0, drop=True)
        df['MA10'] = df.groupby('ticker')['close'].rolling(window=10).mean().reset_index(0, drop=True)
        return df

    def buy_strategy(df):
        df['buy_signal'] = (df['MA5'] > df['MA10']) & (df['MA5'].shift(1) < df['MA10'].shift(1))
        return df

    def sell_strategy(df):
        df['sell_signal'] = (df['MA5'] < df['MA10']) & (df['MA5'].shift(1) > df['MA10'].shift(1))
        return df

    starting_cash = 10000000  # 1000만원
    buy_ratio = 0.1  # 10%
    hold_days = 5
    target_return = 0.05  # 5%
    stop_loss = -0.15  # -15%

    bt = Backtest('stock_prices.db', preprocess, buy_strategy, sell_strategy, starting_cash, buy_ratio, hold_days, target_return, stop_loss)
    bt.start()
