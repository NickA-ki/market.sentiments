import streamlit as st
import datetime

from data.source import load_data
from src.components.bar_charts import plot_article_sentiments
from src.components.filter_dataframe import draw_aggrid
from streamlit_extras import toggle_switch
from streamlit_card import card


df = load_data()
card_style = (
    {
        "card": {
            "height": "150px",
            "width": "150px",
            "border-radius": "40px",
            "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
            "background-color": "lightgrey",
        },
    },
)

# Page Header ----
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 9], gap="small")
with col1:
    st.image(
        "assets/dr_nick.jpeg",
        width=100,
    )
with col2:
    st.title("Market Tracking")

# sidebar controls ----
st.sidebar.subheader("Article Search")
search = st.sidebar.text_input("Search articles", "")
start_date = st.sidebar.date_input(
    "Start date", datetime.datetime.strptime("2020-01-01", "%Y-%M-%d")
)
end_date = st.sidebar.date_input("End date", datetime.date.today())

# Data filtering ----
df = df[
    (df.TextSearch.str.contains(search.lower()))
    & (df.Date >= start_date)
    & (df.Date <= end_date)
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
        styles=card_style[0],
        on_click=lambda: None,
    )
    card(
        text="Mkt Sentiment",
        title=f"{sentiment}",
        styles=card_style[0],
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
