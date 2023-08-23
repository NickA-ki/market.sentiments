import streamlit as st
import pandas as pd

from src.components.lloyds_quadrant import plot_syndicate_quadrant
from src.components.lloyds_rank import plot_cor_change
from src.components.lloyds_modelling import LloydsModel
from src.utils.utils import utils
from data.source import source

# NOTE: loading data ----
lloyds = source.load_lloyds()
synd_dict = source.lloyds_syndicate_dict()

# Page Header ----
utils.page_title("Syndicate Performance")

# sidebar controls ----
st.sidebar.subheader("Lloyd's Filters")
cob = st.sidebar.selectbox(
    "Select Lloyd's COB:",
    (
        "Property",
        "Casualty",
        "Marine",
        "Energy",
        "Reinsurance",
        "Aviation",
        "Motor",
    ),
)

timeframe = st.sidebar.number_input(
    "Select last 'n' years:", min_value=2, max_value=10, value=9, step=1
)

syndicates = st.sidebar.multiselect(
    "Select Syndcates:",
    options=lloyds.SyndicateCode.unique(),
)

utils.show_syndicate_name(syndicates, synd_dict)

# Set up tab structure:
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "YoY CoR Change",
        "Syndicate Performance",
        "YoY CoR Distributions",
        "Rank Prediction",
    ]
)

with st.spinner("Loading Modelling..."):
    # Model ----
    model = LloydsModel(lloyds, cob, start_year=2022 - timeframe)

    # Chart ----
    with tab1:
        st.text("")
        st.pyplot(plot_cor_change(lloyds, cob, syndicates), use_container_width=True)

    with tab2:
        st.text("")
        chart_slot = st.empty()

    with tab3:
        st.text("")
        st.pyplot(model.plot_event_year_kde(), use_container_width=True)

    with tab4:
        st.text("")
        head, tail = st.columns(2)
        head.pyplot(
            model.plot_model_output(alpha=1, codes=syndicates),
            use_container_width=True,
        )
        tail.pyplot(
            model.plot_model_output(alpha=1, head=False, codes=syndicates),
            use_container_width=True,
        )
        st.text(f"* Modelling based on years: {2022 - timeframe} to 2022")

    # Attach updated chart ---
    chart_slot.plotly_chart(
        plot_syndicate_quadrant(lloyds, cob, syndicates, net=15, timeframe=timeframe),
        use_container_width=True,
    )
