import streamlit as st

from data.source import load_data
from src.components.bar_charts import plot_major_loss_trend
from src.components.filter_dataframe import draw_aggrid

# NOTE: loading data ----
df = load_data(table="major_loss_articles")

# Page Header ----
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 9], gap="small")
with col1:
    st.image(
        "assets/dr_nick.jpeg",
        width=100,
    )
with col2:
    st.title("Major Loss Tracking")

# sidebar controls ----
st.sidebar.subheader("Major loss search")
search = st.sidebar.text_input("Search articles", "Ian")
st.sidebar.text("Search is case sensitive")


# Chart ----
st.text("")
chart_slot = st.empty()


# AgGrid ----
st.text("")
if len(search) > 0:
    df_search = df[(df.Title.str.contains(search)) | (df.Summary.str.contains(search))]
else:
    df_search = df

grid_response = draw_aggrid(df_search)

# Attach updated chart ---
chart_slot.plotly_chart(
    plot_major_loss_trend(df, loss_search=search),
    use_container_width=True,
)
