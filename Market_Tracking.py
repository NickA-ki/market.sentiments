import streamlit as st
import datetime

from data.source import source, DataSchema
from src.components.bar_charts import plot_article_sentiments
from src.components.filter_dataframe import draw_aggrid
from src.utils.utils import utils
from streamlit_extras import toggle_switch
from streamlit_card import card


df = source.load_data()

# Page Header ----
utils.page_title("Market Tracking")

# sidebar controls ----
st.sidebar.subheader("Article Search")
search = st.sidebar.text_input("Search articles", "")
start_date = st.sidebar.date_input(
    "Start date", datetime.datetime.strptime("2020-01-01", "%Y-%M-%d")
)
end_date = st.sidebar.date_input("End date", datetime.date.today())
# with st.sidebar:
#     logout()

# Data filtering ----
df = df[
    (df[DataSchema.SEARCH].str.contains(search.lower()))
    & (df[DataSchema.DATE] >= start_date)
    & (df[DataSchema.DATE] <= end_date)
].reset_index(drop=True)
articles = df.shape[0]
sentiment = "Positive" if df.compound.sum() >= 0 else "Negative"

# Chart and KPI Cards ----
tog = toggle_switch.st_toggle_switch(label="Show as % of Articles:", default_value=True)
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

# Table ----
st.subheader("Articles:")
grid_response = draw_aggrid(df)
df = grid_response["data"]

# Append chart data ----
with st.spinner("Displaying results..."):
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
