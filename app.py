import streamlit as st
import crawl_sqlite3
import analysis_1day
import analysis_5day

# 사이드바에 메뉴 버튼을 만듭니다.
st.sidebar.title("Choose action:")
if st.sidebar.button("Crawl data (could be very slow)"):
    crawl_sqlite3.crawl()
if st.sidebar.button("1 Day Analysis"):
    analysis_1day.doit()
if st.sidebar.button("5 Day Analysis"):
    analysis_5day.doit()
