import streamlit as st
import analysis_1day
import analysis_5day
import traceback

st.sidebar.title("Choose action:")
b2 = st.sidebar.button("1 Day Analysis")
b3 = st.sidebar.button("5 Day Analysis")
remote = st.sidebar.checkbox('Load db from remote')

try:    
    if b2:
        analysis_1day.doit(remote)
    if b3:
        analysis_5day.doit(remote)
except Exception as e:
    st.error(traceback.format_exc())
