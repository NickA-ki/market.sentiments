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
    st.session_state.count = 12


def increment_counter():
    st.session_state.count += 12


def decrement_counter():
    st.session_state.count -= 12


def reset_counter():
    st.session_state.count = 12


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
    with st.spinner("Loading feed..."):
        for article in range(st.session_state.count - 12, st.session_state.count):
            mui_card(
                title=df.loc[article][DataSchema.MAIN],
                content=df.loc[article][DataSchema.SUMMARY],
                date=df.loc[article][DataSchema.DATE],
                link=df.loc[article][DataSchema.LINK],
            )
        col1, col2, col3, col4, col5 = st.columns(
            [0.3, 0.1, 0.1, 0.1, 0.4], gap="small"
        )
        if st.session_state.count == 12:
            disable = True
        else:
            disable = False
        col2.button(
            "Latest", type="secondary", on_click=reset_counter, disabled=disable
        )
        col3.button(
            "Previous", type="primary", on_click=decrement_counter, disabled=disable
        )
        col4.button("Next", type="primary", on_click=increment_counter)
        # components.html(source_code, height=600)
        st.markdown(
            """
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8350475854193715"
                crossorigin="anonymous"></script>
            <!-- market_news -->
            <ins class="adsbygoogle"
                style="display:block"
                data-ad-client="ca-pub-8350475854193715"
                data-ad-slot="7942115995"
                data-ad-format="auto"
                data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
            """,
            unsafe_allow_html=True,
        )

    with st.sidebar:
        logout(authenticator)

elif authentication_status == False:
    st.error("Username/password is incorrect")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)

elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)
