import streamlit as st
import analysis_1day
import analysis_5day
import traceback

st.sidebar.title("Choose action:")
b2 = st.sidebar.button("1 Day Analysis")
b3 = st.sidebar.button("5 Day Analysis")

try:    
    if b2:
        analysis_1day.doit()
    if b3:
        analysis_5day.doit()
except Exception as e:
    st.error(traceback.format_exc())
