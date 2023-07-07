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
    sorted(
        (
            "Aviation",
            "Property",
            "Casualty",
            "Marine",
            "Energy",
            "Motor",
            "Reinsurance",
        )
    ),
)

syndicates = st.sidebar.multiselect(
    "Select Syndcates",
    options=lloyds.SyndicateCode.unique(),
)

utils.show_syndicate_name(syndicates, synd_dict)

# Set up tab structure:
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Syndicate Performance",
        "YoY CoR Change",
        "YoY CoR Distributions",
        "Rank Prediction",
    ]
)

with st.spinner("Loading Modelling..."):
    # Model ----
    model = LloydsModel(lloyds, cob)

    # Chart ----
    with tab1:
        st.text("")
        chart_slot = st.empty()

    with tab2:
        st.text("")
        st.pyplot(plot_cor_change(lloyds, cob, syndicates), use_container_width=True)

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

    # Attach updated chart ---
    chart_slot.plotly_chart(
        plot_syndicate_quadrant(lloyds, cob, syndicates, net=10),
        use_container_width=True,
    )
