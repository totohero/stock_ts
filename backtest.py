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
            shares_to_buy = np.floor(investment / row['close'])
            actual_investment = shares_to_buy * row['close']
            if shares_to_buy > 0:
                return True, actual_investment, shares_to_buy
            else:
                return False, 0, 0
        else:
            return False, 0, 0

    def execute_sell(self, df, row, entry_price, shares):
        if self.stop_loss is not None and row['low'] / entry_price - 1 <= self.stop_loss:
            return True, self.stop_loss * shares * entry_price
        elif self.target_return is not None and row['high'] / entry_price - 1 >= self.target_return:
            return True, self.target_return * shares * entry_price
        elif row['sell_signal']:
            pnl = row['close'] / entry_price - 1
            return True, pnl * shares * entry_price
        if self.hold_days is not None and df.loc[df['ticker'] == row['ticker']].shape[0] >= self.hold_days:
            pnl = row['close'] / entry_price - 1
            return True, pnl * shares * entry_price
        return False, row['pnl']


    def run(self, df, cash):
        result_df = df.copy()
        result_df['pnl'] = 0.0
        result_df = self.buy_strategy(result_df)
        buy_signals = result_df[result_df['buy_signal']].groupby(result_df[result_df['buy_signal']].index)['ticker'].apply(set)
        result_df = self.sell_strategy(result_df)

        holdings = {}
        changes = []

        total_value = cash
        for date in result_df.index.unique():
            date_df = result_df.loc[date]
            tickers_to_buy = buy_signals.get(date, set())
            
            tickers_to_add = {}
            # Buying process
            for ticker in tickers_to_buy:
                if ticker not in holdings:
                    ticker_df = date_df[date_df['ticker'] == ticker]

                    for i, row in ticker_df.iterrows():
                        buy_signal, investment, shares = self.execute_buy(ticker_df, row, total_value)
                        if buy_signal and investment > 0 and cash >= investment:
                            cash -= investment
                            tickers_to_add[ticker] = {'entry_price': row['close'], 'shares': shares}  # Save entry price and shares
                            changes.append((i, 'pnl', 0))  # No profit/loss at the moment of buying

            # Selling process
            tickers_to_remove = set()
            for ticker in list(holdings.keys()):
                ticker_df = date_df[date_df['ticker'] == ticker]
                entry_price = shares = holdings[ticker]['entry_price']
                shares = holdings[ticker]['shares']

                for i, row in ticker_df.iterrows():
                    sell_signal, pnl = self.execute_sell(ticker_df, row, entry_price, shares)
                    if sell_signal:
                        cash += row['close'] * shares
                        tickers_to_remove.add(ticker)  # Save ticker to remove from holdings
                        changes.append((i, 'pnl', pnl))                    
            
            holdings = {ticker: holdings[ticker] for ticker in holdings if ticker not in tickers_to_remove}  # Remove from holdings using set comprehension
            holdings.update(tickers_to_add)  # Add to holdings using update

            if len(holdings) > 0 or len(tickers_to_add) > 0:                
                # 계산된 현금과 보유 종목의 현재 가치를 합산하여 총자산 계산
                holdings_value = sum(holdings[ticker]['shares'] * (date_df[date_df['ticker'] == ticker]['close'].iloc[0] 
                      if not date_df[date_df['ticker'] == ticker].empty else 0) for ticker in holdings)

                total_value = cash + holdings_value
                print(f'{date}: Remaining cash is {cash}, Total portfolio value is {total_value}')

        for idx, column, value in changes:
            result_df.loc[idx, column] = value

        return result_df, cash

    def start(self):
        df = self.load_data()
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
