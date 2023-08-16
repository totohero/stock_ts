import streamlit as st
import analysis_1day
import analysis_5day
import traceback
import filter1
import rsi_gain
import adx_gain
import load_db

st.sidebar.title("Choose action:")

remote = st.sidebar.checkbox('Load db from remote')
df = load_db.load_data(remote)

use_filter1 = st.sidebar.checkbox('Filter 1 (rsi > 70 && macd osc > 0)')
if use_filter1:
    df = filter1.filter_stocks(df)

try:    
    if st.sidebar.button("1 Day Analysis"):
        analysis_1day.doit(df)
    if st.sidebar.button("5 Day Analysis"):
        analysis_5day.doit(df)
    if st.sidebar.button("RSI - 5 Day Return"):
        rsi_gain.plot_rsi_vs_5day_return(df)
    if st.sidebar.button("ADX - 5 Day Return"):
        adx_gain.plot_adx_vs_5day_return(df)

except Exception as e:
    st.error(traceback.format_exc())
