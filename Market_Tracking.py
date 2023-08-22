import streamlit as st
import datetime

from data.source import source, DataSchema
from src.components.bar_charts import plot_article_sentiments
from src.components.filter_dataframe import draw_aggrid
from src.components.auth import authenticate, logout
from llm.trainer import LLMIns
from src.utils.utils import utils
from streamlit_extras import toggle_switch
from streamlit_card import card

# Page Header ----
utils.page_title("Market Tracking ")

authenticator, authentication_status = authenticate()

if authentication_status:
    df = source.load_data()
    if "chat_model" not in st.session_state:
        st.session_state["chat_model"]: LLMIns = LLMIns()  ## Intialisation

    # sidebar controls ----
    st.sidebar.subheader("Article Search")
    search = st.sidebar.text_input("Search articles", "")
    start_date = st.sidebar.date_input(
        "Start date", datetime.datetime.strptime("2020-01-01", "%Y-%M-%d")
    )
    end_date = st.sidebar.date_input("End date", datetime.date.today())
    with st.sidebar:
        logout(authenticator)

    # Data filtering ----
    df = df[
        (df[DataSchema.SEARCH].str.contains(search.lower()))
        & (df[DataSchema.DATE] >= start_date)
        & (df[DataSchema.DATE] <= end_date)
    ].reset_index(drop=True)
    articles = df.shape[0]
    sentiment = "Positive" if df.compound.sum() >= 0 else "Negative"
    search_text = search if search != "" else "All"

    # AI Assitant ---
    # Get user input
    question = st.text_input("🤖 Ask me your insurance question")

    # Generate the response
    if st.button("Get Answer"):
        with st.spinner("Generating Answer..."):
            try:
                response = st.session_state["chat_model"].falcon_generate(question)
                st.success(response)
            except Exception as e:
                st.error(f"Error answering the question: {str(e)}")

    # Chart and KPI Cards ----
    tog = toggle_switch.st_toggle_switch(
        label="Show as % of Articles:", default_value=True
    )
    with st.spinner("Fetching Articles..."):
        card1, card2 = st.columns([0.75, 0.25])
        with card1:
            chart_slot = st.empty()
        with card2:
            card(
                text="Articles",
                title=f"{articles:,}",
                styles=utils.card_style[0],
                on_click=lambda: None,
            )
            card(
                text="Mkt Sentiment",
                title=f"{sentiment}",
                styles=utils.card_style[0],
                on_click=lambda: None,
            )
            card(
                text="Articles",
                title=f"{search_text}",
                styles=utils.card_style[0],
                on_click=lambda: None,
            )

    # Table ----
    st.subheader("Articles:")
    grid_response = draw_aggrid(df)
    df = grid_response["data"]

    # Append chart data ----
    # displays the chart
    if tog:
        chart_slot.plotly_chart(
            plot_article_sentiments(df, True),
            use_container_width=True,
        )
    else:
        chart_slot.plotly_chart(
            plot_article_sentiments(df, False),
            use_container_width=True,
        )

elif authentication_status == False:
    st.error("Username/password is incorrect")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)

elif authentication_status == None:
    st.warning("Please enter your username and password")
    st.markdown(utils.hide_bar, unsafe_allow_html=True)
