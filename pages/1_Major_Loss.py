import streamlit as st

from data.source import source, DataSchema
from src.components.bar_charts import plot_major_loss_trend
from src.components.filter_dataframe import draw_aggrid
from src.utils.utils import utils
import datetime


# NOTE: loading data ----
df = source.load_data(table="major_loss_articles")
df = df[df.Date >= datetime.date(year=2022, month=1, day=1)].reset_index(drop=True)

# Page Header ----
utils.page_title("Major Loss Tracking")

# sidebar controls ----
st.sidebar.subheader("Major loss search")
search = st.sidebar.text_input("Search articles", "Ian", key="search2")
st.sidebar.text("Search is case sensitive")

# Chart ----
st.text("")
chart_slot = st.empty()

# AgGrid ----
st.text("")
if len(search) > 0:
    df_search = df[
        (df[DataSchema.TITLE].str.contains(search))
        | (df[DataSchema.SUMMARY].str.contains(search))
    ]
else:
    df_search = df

grid_response = draw_aggrid(df_search)

# Attach updated chart ---
chart_slot.plotly_chart(
    plot_major_loss_trend(df, loss_search=search),
    use_container_width=True,
)
