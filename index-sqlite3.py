import sqlite3

conn = sqlite3.connect('stock_prices.db')
c = conn.cursor()
c.execute('CREATE INDEX date_index ON prices(date)')
c.execute('CREATE INDEX ticker_index ON prices(ticker)')
conn.commit()