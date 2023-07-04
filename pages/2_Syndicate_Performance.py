import streamlit as st
import pandas as pd

from src.components._lloyds import plot_syndicate_quadrant

# NOTE: loading data ----
lloyds = pd.read_csv("./data/lloyds.csv")
lloyds = lloyds[(lloyds.ActiveSyndicateFlag == "Active")].reset_index(drop=True)

# Page Header ----
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 9], gap="small")
with col1:
    st.image(
        "assets/dr_nick.jpeg",
        width=100,
    )
with col2:
    st.title("Syndicate Performance")

# sidebar controls ----
st.sidebar.subheader("Lloyd's Filters")
cob = st.sidebar.selectbox(
    "Select Lloyd's COB:",
    sorted(
        ["Aviation", "Property", "Casualty", "Marine", "Energy", "Motor", "Reinsurance"]
    ),
)

syndicates = st.sidebar.multiselect(
    "Select Syndcates", options=lloyds.SyndicateCode.unique()
)


# Chart ----
st.text("")
chart_slot = st.empty()

# Attach updated chart ---
chart_slot.plotly_chart(
    plot_syndicate_quadrant(lloyds, cob, syndicates, net=10),
    use_container_width=True,
)
