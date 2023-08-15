import sqlite3
import pandas as pd
import streamlit as st

db_paths = [ 'KOSPI_stock_prices.db', 'KOSDAQ_stock_prices.db']

@st.cache_data
def load_data():
    all_df = pd.DataFrame()
    for db_path in db_paths:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql('SELECT * FROM prices', conn)    
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        all_df = pd.concat([all_df, df])

    return all_df

if __name__ == '__main__':
    all_df = load_data()
    st.write(all_df.head(10))

