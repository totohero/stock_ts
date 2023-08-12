import sqlite3
import pandas as pd

original_db_path = 'stock_prices.db'

def load_db():
    # Connect to the SQLite database
    return sqlite3.connect('stock_prices.db')

def load_df():
    conn = load_db()
    return pd.read_sql('SELECT * FROM prices', conn)
