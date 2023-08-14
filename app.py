import streamlit as st
import crawl_sqlite3
import analysis_1day
import analysis_5day

st.sidebar.title("Choose action:")
b1 = st.sidebar.button("Crawl data (could be very slow)"):
b2 = st.sidebar.button("1 Day Analysis"):
b3 = st.sidebar.button("5 Day Analysis"):

try:
    st.sidebar.title("Choose action:")
    if b1:
        crawl_sqlite3.crawl()
    if b2:
        analysis_1day.doit()
    if b3:
        analysis_5day.doit()
except Exception as e:
    st.error(e)
