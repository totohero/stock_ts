import sqlite3
import pandas as pd
import streamlit as st

original_db_path = 'stock_prices.db'

@st.cache_data
def load_data():
    conn = sqlite3.connect(original_db_path)
    df = pd.read_sql('SELECT * FROM prices', conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

