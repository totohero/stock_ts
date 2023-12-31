import streamlit as st

import load_db
import analysis_1day
import analysis_5day
import traceback
import rsi_gain
import adx_gain
import macd_osc_gain

st.sidebar.title("Choose action:")

remote = st.sidebar.checkbox('Load db from remote')
df = load_db.load_data(remote)

try:
    if st.sidebar.button("1 Day Analysis"):
        analysis_1day.doit(df)
    if st.sidebar.button("5 Day Analysis"):
        analysis_5day.doit(df)
    if st.sidebar.button("RSI - 5 Day Return"):
        rsi_gain.plot_rsi_vs_5day_return(df)
    if st.sidebar.button("ADX - 5 Day Return"):
        adx_gain.plot_adx_vs_5day_return(df)
    if st.sidebar.button("MACD OSC - 5 Day Return"):
        macd_osc_gain.plot_macd_oscillator_vs_5day_return(df)

except Exception as e:
    st.error(traceback.format_exc())
