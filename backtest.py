import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def draw_graph(perf_df):
    # Create subplot figure
    fig = make_subplots(rows=3, cols=1)

    # Create series for profits and losses
    profits = perf_df['realized_pnl'].clip(lower=0)
    losses = perf_df['realized_pnl'].clip(upper=0)

    # Add traces
    fig.add_trace(go.Scatter(x=perf_df.index, y=perf_df['cumulative_return'], mode='lines', name='Cumulative Returns'), row=1, col=1)
    fig.add_trace(go.Bar(x=perf_df.index, y=profits, name='Profits', marker_color='green'), row=2, col=1)
    fig.add_trace(go.Bar(x=perf_df.index, y=losses, name='Losses', marker_color='red'), row=2, col=1)
    fig.add_trace(go.Scatter(x=perf_df.index, y=-perf_df['draw_down'], mode='lines', name='Drawdown'), row=3, col=1)

    # Update layout to autosize
    fig.update_layout(autosize=True, title_text="Subplots")

    # Update yaxis titles
    fig.update_yaxes(title_text="Cumulative Returns", row=1, col=1)
    fig.update_yaxes(title_text="PNL", row=2, col=1)
    fig.update_yaxes(title_text="DD", row=3, col=1)

    fig.show()

class Backtest:
    def __init__(self, db_path, preprocess, daily_sort, buy_strategy, sell_strategy, starting_cash, buy_ratio, hold_days=None, target_return=None, stop_loss=None, begin_date=None, end_date=None, transaction_cost=0.0):
        self.db_path = db_path
        self.preprocess = preprocess
        self.daily_sort = daily_sort
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
    def execute_buy(self, row, cash):
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

    def trade_a_day(self, date, df_to_buy_today, date_df, holdings, cash, total_value):
        tickers_to_add = {}
        tickers_to_remove = set()
        # Buying process
        num_buys = 0
        print(f'### {date} ### - {len(df_to_buy_today)} tickers to buy')
        for i, ticker_df in df_to_buy_today.iterrows():
            if ticker_df['ticker'] not in holdings:
                buy_signal, investment, shares = self.execute_buy(ticker_df, total_value)
                if buy_signal and investment > 0 and cash >= investment:
                    num_buys += 1
                    cash -= investment
                    tickers_to_add[ticker_df['ticker']] = {'entry_price': ticker_df['close'], 'shares': shares, 'investment': investment}
                    print(
                            f'Buying {ticker_df["ticker"]} at {ticker_df["close"]} for {shares} shares investing {investment}')

        # Selling process
        num_sells = 0
        realized_pnl = 0
        for ticker in list(holdings.keys()):
            ticker_df = date_df[date_df['ticker'] == ticker]
            entry_price = shares = holdings[ticker]['entry_price']
            shares = holdings[ticker]['shares']
            investment = holdings[ticker]['investment']
            for i, row in ticker_df.iterrows():
                sell_signal, exit_price, exit_return = self.execute_sell(ticker_df, row, entry_price, shares)
                if sell_signal:
                    num_sells += 1
                    realized_pnl += exit_return - investment
                    cash += exit_return
                    tickers_to_remove.add(ticker)
                    print(f'Selling {ticker} at {exit_price} for {shares} shares returning {exit_return} with pnl {exit_return - investment} (ratio: {exit_return / investment * 100 - 100:.2f}%)')

        holdings = {ticker: holdings[ticker] for ticker in holdings if ticker not in tickers_to_remove}
        holdings.update(tickers_to_add)

        return holdings, cash, realized_pnl, num_buys, num_sells

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

    def run(self, df, perf_df, cash):
        result_df = df.copy()
        result_df = self.buy_strategy(result_df)
        df_to_buy = result_df[result_df['buy_signal']]
        result_df = self.sell_strategy(result_df)

        holdings = {}
        total_value = max_total_value = cash
        max_draw_down = 0

        changes = {}
        for date in result_df.index.unique():
            df_to_buy_today = self.daily_sort(df_to_buy[df_to_buy.index == date])
            holdings, cash, realized_pnl, num_buys, num_sells = self.trade_a_day(date, df_to_buy_today, result_df.loc[date], holdings, cash, total_value)
            total_value, max_total_value, draw_down = self.update_total_value_and_drawdown(result_df.loc[date], holdings, cash, max_total_value)
            max_draw_down = max(max_draw_down, draw_down)

            # Update performance tracking DataFrame
            new_row = pd.DataFrame({'date': [date],
                        'num_holdings': [len(holdings)],
                        'num_buys': [num_buys],
                        'num_sells': [num_sells],
                        'realized_pnl': [realized_pnl],
                        'cumulative_return': [total_value / self.starting_cash - 1],
                        'draw_down': [draw_down]})
            perf_df = pd.concat([perf_df, new_row])

        for idx, column, value in changes:
            result_df.loc[idx, column] = value

        return result_df, perf_df, total_value, max_total_value, max_draw_down

    def start(self):
        df = self.load_data()
        # Initialize performance tracking DataFrame
        perf_df = pd.DataFrame(); # columns=['date', 'num_holdings', 'num_buys', 'num_sells', 'realized_pnl', 'cumulative_return', 'draw_down'])

        cash = self.starting_cash
        df, perf_df, total_value, max_total_value, max_draw_down = self.run(df, perf_df, cash)
        print(f'====================================')
        print(f'Final total return: {100*total_value/self.starting_cash - 100:.2f}%')
        print(f'Max total return: {100*max_total_value/self.starting_cash - 100:.2f}%')
        cagr = (total_value/self.starting_cash)**(252/len(df.index.unique())) - 1
        print(f'CAGR: {100*cagr:.2f}%')
        print(f'MDD: {100*max_draw_down:.2f}%')

        # Converting 'date' to datetime
        perf_df['date'] = pd.to_datetime(perf_df['date'])

        # Setting 'date' as the index
        perf_df.set_index('date', inplace=True)

        draw_graph(perf_df)

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
    
    def daily_sort(df):
        return df.sort_values(by=['ticker', 'date'], ascending=[True, False])

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

    bt = Backtest('stock_prices.db', preprocess, daily_sort, buy_strategy, sell_strategy,
                  starting_cash, buy_ratio, hold_days, target_return, stop_loss,
                  begin_date='2021-01-01', end_date='2023-08-14', transaction_cost=0.00015)
    
    if True:
        bt.start()
    else:
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