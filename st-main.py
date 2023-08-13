import streamlit as st
import 5일수익률분포
import 전날종가-시가-종가-상관관계

# 사이드바에 메뉴 버튼을 만듭니다.
st.sidebar.title("Choose a chart:")
if st.sidebar.button("Chart 1"):
    file1.plot_chart1()
if st.sidebar.button("Chart 2"):
    file2.plot_chart2()
