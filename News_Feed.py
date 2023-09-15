import streamlit as st
from src.utils.utils import utils
from src.components.card import mui_card
from data.source import source, DataSchema
from src.components.auth import authenticate, logout

df = source.load_data()

# Page Header ----
utils.page_title("Insurance News Feed ")

authenticator, authentication_status = authenticate()

if "count" not in st.session_state:
    st.session_state.count = 5


def increment_counter():
    st.session_state.count += 5


if authentication_status:
    st.divider()
    for article in range(len(df.head(st.session_state.count))):
        mui_card(
            title=df.loc[article][DataSchema.MAIN],
            content=df.loc[article][DataSchema.SUMMARY],
            date=df.loc[article][DataSchema.DATE],
            link=df.loc[article][DataSchema.LINK],
        )
    col1, col2, col3 = st.columns([0.45, 0.3, 0.25])
    col2.button("Load More...", type="primary", on_click=increment_counter)

    with st.sidebar:
        logout(authenticator)

elif authentication_status == False:
    st.error("Username/password is incorrect")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)

elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)
