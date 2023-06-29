import streamlit as st
import pandas as pd
import numpy as np

from data.source import load_data
from src.components.bar_chart import plot_article_sentiments
from src.components.filter_dataframe import filter_dataframe
from streamlit_pagination import pagination_component

st.set_page_config(
    layout="wide",
)

st.markdown(
    "<style>" + open("./assets/style.css").read() + "</style>", unsafe_allow_html=True
)


def data_chunk_choice():
    if "foo" not in st.session_state:
        return 0
    if not st.session_state["foo"]:
        return 0
    return st.session_state["foo"]


st.title("Market Tracking")

data_load_state = st.text("Loading data...")
data = load_data()
data_load_state.text("Loading data...complete!")

data_filtered = filter_dataframe(data)

st.subheader("Article sentiments by month:")

st.plotly_chart(plot_article_sentiments(data_filtered, True), use_container_width=True)

st.subheader("Articles:")

n = 10
list_df = [data_filtered[i : i + n] for i in range(0, data_filtered.shape[0], n)]

data_l = list_df[data_chunk_choice()]

st.dataframe(data_l)

layout = {"color": "primary", "style": {"margin-top": "10px"}}

pagination_component(len(list_df), layout=layout, key="foo")
