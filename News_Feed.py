import streamlit as st
import datetime

from src.utils.utils import utils
from src.components.card import mui_card
from data.source import source, DataSchema
from src.components.auth import authenticate, logout
import streamlit.components.v1 as components

df = source.load_data()
HtmlFile = open("./data/ads.html", "r", encoding="utf-8")
source_code = HtmlFile.read()

# Page Header ----
utils.page_title("Insurance News Feed ")

authenticator, authentication_status = authenticate()

if "count" not in st.session_state:
    st.session_state.count = 5


def increment_counter():
    st.session_state.count += 5


search = st.sidebar.text_input("Search articles", "")
start_date = st.sidebar.date_input(
    "Start date", datetime.datetime.strptime("2020-01-01", "%Y-%M-%d")
)
end_date = st.sidebar.date_input("End date", datetime.date.today())

df = df[
    (df[DataSchema.SEARCH].str.contains(search.lower()))
    & (df[DataSchema.DATE] >= start_date)
    & (df[DataSchema.DATE] <= end_date)
].reset_index(drop=True)

if authentication_status:
    st.divider()
    with st.spinner("Loading feed..."):
        for article in range(len(df.head(st.session_state.count))):
            mui_card(
                title=df.loc[article][DataSchema.MAIN],
                content=df.loc[article][DataSchema.SUMMARY],
                date=df.loc[article][DataSchema.DATE],
                link=df.loc[article][DataSchema.LINK],
            )
        col1, col2, col3 = st.columns([0.45, 0.3, 0.25])
        col2.button("Load More...", type="primary", on_click=increment_counter)
        components.html(source_code, height=600)

    with st.sidebar:
        logout(authenticator)

elif authentication_status == False:
    st.error("Username/password is incorrect")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)

elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)
