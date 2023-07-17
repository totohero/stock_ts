import mydb
import plotly.graph_objects as go
import pandas as pd

db, meta, date_collection, stock_ts = mydb.get_db()

symbol = "005930"
data = list(stock_ts.find({'symbol': symbol}))

# Assuming you have the OHLCV data in a variable called `df`
df = pd.DataFrame(data)
duplicates = df['dup'] = df.duplicated(subset='date')

if duplicates.any():
    print("Duplicate rows with the same date exist.")
    print(df[df['dup'] == True])
else:
    print("No duplicate rows with the same date.")

period=20
df_close = df['close']
df['SMA'] = df_close.rolling(window=period).mean()

# sort df rows by date
df = df.sort_values(by='date')

for index, row in df[0:30].iterrows():
    print(str(index) + " " + str(row))
    print("")

fig = go.Figure(data=[go.Candlestick(x=df['date'],
                                   open=df['open'],
                                   high=df['high'],
                                   low=df['low'],
                                   close=df['close']),
    go.Scatter(x=df['date'],
               y=df['SMA'],
               mode='lines',
               name='SMA')])

fig.show()
