import sqlite3
import pandas as pd
import numpy as np


class Backtest:
    def __init__(self, db_path, preprocess, buy_strategy, sell_strategy, starting_cash, buy_ratio, hold_days=None, target_return=None, stop_loss=None, begin_date=None, end_date=None, transaction_cost=0.0):
        self.db_path = db_path
        self.preprocess = preprocess
        self.buy_strategy = buy_strategy
        self.sell_strategy = sell_strategy
        self.starting_cash = starting_cash
        self.buy_ratio = buy_ratio
        self.hold_days = hold_days
        self.target_return = target_return
        self.stop_loss = stop_loss
        self.begin_date = begin_date
        self.end_date = end_date
        self.transaction_cost = transaction_cost

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM prices", conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        if self.begin_date is not None and self.end_date is not None:
            mask = (df.index >= pd.to_datetime(self.begin_date)) & (
                df.index <= pd.to_datetime(self.end_date))
            df = df.loc[mask]
        df = self.preprocess(df)
        return df

    def calculate_investment(self, cash):
        return cash * self.buy_ratio

    # returns a tuple of (buy_signal, actual_investment, shares_to_buy)
    def execute_buy(self, df, row, cash):
        investment = self.calculate_investment(cash)
        if row['buy_signal']:
            shares_to_buy = np.floor(
                investment / (row['close'] * (1 + self.transaction_cost)))
            actual_investment = np.ceil(
                shares_to_buy * row['close'] * (1 + self.transaction_cost))
            if shares_to_buy > 0:
                return True, actual_investment, shares_to_buy
            else:
                return False, 0, 0
        else:
            return False, 0, 0

    # returns a tuple of (sell_signal, exit_price, exit_return)
    def execute_sell(self, df, row, entry_price, shares):
        sell_signal = False
        exit_price = 0.0
        exit_return = 0.0

        if self.stop_loss is not None and row['low'] / entry_price - 1 <= self.stop_loss:
            sell_signal = True
            exit_price = np.floor((1 + self.stop_loss) * entry_price)
        elif self.target_return is not None and row['high'] / entry_price - 1 >= self.target_return:
            sell_signal = True
            exit_price = np.floor((1 + self.target_return) * entry_price)
        elif row['sell_signal']:
            sell_signal = True
            exit_price = row['close']
        elif self.hold_days is not None and df.loc[df['ticker'] == row['ticker']].shape[0] >= self.hold_days:
            sell_signal = True
            exit_price = row['close']

        if sell_signal:
            exit_return = np.ceil(exit_price * shares *
                                  (1 - self.transaction_cost))

        return sell_signal, exit_price, exit_return

    def trade_a_day(self, date, tickers_to_buy_today, date_df, holdings, cash, total_value):
        tickers_to_add = {}
        tickers_to_remove = set()
        changes = []
        # Buying process
        print(f'### {date} ### - {len(tickers_to_buy_today)} tickers to buy')
        for ticker in tickers_to_buy_today:
            if ticker not in holdings:
                ticker_df = date_df[date_df['ticker'] == ticker]
                for i, row in ticker_df.iterrows():
                    buy_signal, investment, shares = self.execute_buy(ticker_df, row, total_value)
                    if buy_signal and investment > 0 and cash >= investment:
                        cash -= investment
                        tickers_to_add[ticker] = {'entry_price': row['close'], 'shares': shares, 'investment': investment}
                        print(
                                f'Buying {ticker} at {row["close"]} for {shares} shares investing {investment}')

        # Selling process
        for ticker in list(holdings.keys()):
            ticker_df = date_df[date_df['ticker'] == ticker]
            entry_price = shares = holdings[ticker]['entry_price']
            shares = holdings[ticker]['shares']
            investment = holdings[ticker]['investment']
            for i, row in ticker_df.iterrows():
                sell_signal, exit_price, exit_return = self.execute_sell(ticker_df, row, entry_price, shares)
                if sell_signal:
                    cash += exit_return
                    tickers_to_remove.add(ticker)
                    print(f'Selling {ticker} at {exit_price} for {shares} shares returning {exit_return} with pnl {exit_return - investment} (ratio: {exit_return / investment * 100 - 100:.2f}%)')


        holdings = {ticker: holdings[ticker] for ticker in holdings if ticker not in tickers_to_remove}
        holdings.update(tickers_to_add)

        return holdings, cash, changes

    def update_total_value_and_drawdown(self, date_df, holdings, cash, max_total_value):
        total_value = cash
        for ticker in holdings:
            entry_price = holdings[ticker]["entry_price"]
            current_price = date_df[date_df["ticker"] == ticker]["close"].iloc[0] if not date_df[date_df['ticker'] == ticker].empty else 0
            print(f'Holding {ticker} shares: {holdings[ticker]["shares"]}, entry_price: {entry_price}, current_price: {current_price}, rate: {100* current_price / entry_price - 100:.2f}%')
            total_value += current_price * holdings[ticker]['shares']
        print(f'Remaining cash is {cash}, Total portfolio value is {total_value}')
        max_total_value = max(max_total_value, total_value)
        draw_down = (max_total_value - total_value) / max_total_value if max_total_value != 0 else 0

        return total_value, max_total_value, draw_down

    def run(self, df, cash):
        result_df = df.copy()
        result_df = self.buy_strategy(result_df)
        tickers_to_buy = result_df[result_df['buy_signal']].groupby(result_df[result_df['buy_signal']].index)['ticker'].apply(list)
        result_df = self.sell_strategy(result_df)

        holdings = {}
        total_value = max_total_value = cash
        max_draw_down = 0

        changes = {}
        for date in result_df.index.unique():
            tickers_to_buy_today = sorted(tickers_to_buy.get(date, []))
            holdings, cash, changes = self.trade_a_day(date, tickers_to_buy_today, result_df.loc[date], holdings, cash, total_value)
            total_value, max_total_value, draw_down = self.update_total_value_and_drawdown(result_df.loc[date], holdings, cash, max_total_value)
            max_draw_down = max(max_draw_down, draw_down)

        for idx, column, value in changes:
            result_df.loc[idx, column] = value

        return result_df, total_value, max_total_value, max_draw_down

    def start(self):
        df = self.load_data()
        cash = self.starting_cash
        df, total_value, max_total_value, max_draw_down = self.run(df, cash)
        print(f'====================================')
        print(f'Final total return: {100*total_value/self.starting_cash - 100:.2f}%')
        print(f'Max total return: {100*max_total_value/self.starting_cash - 100:.2f}%')
        cagr = (total_value/self.starting_cash)**(252/len(df.index.unique())) - 1
        print(f'CAGR: {100*cagr:.2f}%')
        print(f'MDD: {100*max_draw_down:.2f}%')


if __name__ == "__main__":
    # 직접 실행되는 경우에만 수행될 코드
    def preprocess(df):
        df = df[(df['open'] != 0) & (df['close'] != 0) & (
            df['high'] != 0) & (df['low'] != 0) & (df['volume'] != 0)]
        df['MA5'] = df.groupby('ticker')['close'].rolling(
            window=5).mean().reset_index(0, drop=True)
        df['MA10'] = df.groupby('ticker')['close'].rolling(
            window=10).mean().reset_index(0, drop=True)
        return df

    def buy_strategy(df):
        df['buy_signal'] = (df['MA5'] > 1.03*df['MA10']
                            ) & (df['MA5'].shift(1) < 1.03*df['MA10'].shift(1))
        return df

    def sell_strategy(df):
        df['sell_signal'] = (df['MA5'] < 0.97*df['MA10']
                             ) & (df['MA5'].shift(1) > 0.97*df['MA10'].shift(1))
        return df

    starting_cash = 10000000  # 1000만원
    buy_ratio = 0.1  # 10%
    hold_days = 5
    target_return = 0.3  # 30%
    stop_loss = -0.1  # -10%

    bt = Backtest('stock_prices.db', preprocess, buy_strategy, sell_strategy,
                  starting_cash, buy_ratio, hold_days, target_return, stop_loss,
                  begin_date='2023-06-01', end_date='2023-07-01', transaction_cost=0.00015)
    
    import cProfile

    # Create a Profile object
    pr = cProfile.Profile()

    # Begin profiling
    pr.enable()
    
    bt.start()

    # End profiling
    pr.disable()

    # Print the profiling stats
    pr.print_stats(sort='time')
    pr.dump_stats("my_profile.prof")

    import os
    os.system("snakeviz my_profile.prof")