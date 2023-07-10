from zipline import run_algorithm
from zipline.api import order, symbol
from datetime import datetime
import pandas as pd

def initialize(context):
    # Define the stock to trade (e.g., AAPL)
    context.stock = symbol('AAPL')

def handle_data(context, data):
    # Place a simple market order for 1 share of the stock
    order(context.stock, 1)

# Define the backtest start and end dates
start_date = pd.Timestamp('2010-01-01', tz='utc')
end_date = pd.Timestamp('2020-12-31', tz='utc')

# Define the backtest capital
capital_base = 100000

# Run the backtest
results = run_algorithm(
    start=start_date,
    end=end_date,
    initialize=initialize,
    capital_base=capital_base,
    handle_data=handle_data
)

# Print the backtest results
print(results)
