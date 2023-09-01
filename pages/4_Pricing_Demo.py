import streamlit as st
import pandas as pd
import datetime

from src.utils.utils import utils
from data.source import source
from src.components.pricing_demo import get_price_doww, RequestDOWW, MetaData

# NOTE: loading data ----
lloyds = source.load_lloyds()
synd_dict = source.lloyds_syndicate_dict()

# Page Header ----
utils.page_title("Pricing Demo (D&O WW)")

# Set up tab structure:
tab1, tab2 = st.tabs(["Inputs", "Summary"])


# Input form to collect features:
with tab1:
    price_out = st.empty()
    form = st.form("do_ww")
    col1, col2 = form.columns([0.5, 0.5])

    ## Column 1 ##
    industry_id = col1.selectbox(
        "Select Industry:", list(MetaData.INDUSTRY_RATE.keys())
    )

    country_id = col1.selectbox("Select Domicile:", list(MetaData.DOMICILE_RATE.keys()))

    listing_id = col1.selectbox(
        "Select Listing Type:", list(MetaData.LISTING_RATE.keys())
    )
    col1.divider()

    cover_id = col1.selectbox("Select Cover:", list(MetaData.COVER_RATE.keys()))

    retro_id = col1.selectbox("Select Retro Option:", list(MetaData.RETRO_RATE.keys()))

    adr_id = col1.selectbox("Select ADR:", list(MetaData.LISTINGADR_RATE.keys()))

    ## Column 2 ##
    limit = col2.number_input(
        "Select Limit ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=10e6,
        step=1e0,
        format="%f",
    )

    attachment = col2.number_input(
        "Select Attachment ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=5e6,
        step=1e0,
        format="%f",
    )

    assets = col2.number_input(
        "Company Assets ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=5e4,
        step=1e0,
        format="%f",
    )
    col2.divider()

    comm = col2.number_input(
        "Select Brokerage (%):", min_value=0, max_value=100, value=20, step=1
    )

    inception = col2.date_input("Inception date", datetime.date.today())

    expiry = col2.date_input(
        "Expiry date", datetime.date.today() + datetime.timedelta(days=365)
    )

    submitted = form.form_submit_button("Submit")

with tab2:
    chart_slot = st.empty()
    st.divider()
    chart_slot_2 = st.empty()


if submitted:
    input_doww = RequestDOWW(
        y_o_a=2023,
        limit=limit,
        other_commissions=0.1,
        assets=assets,
        country_id=country_id,
        industry_id=industry_id,
        listed_indicator_id=listing_id,
        cover_id=cover_id,
        retro_option_id=retro_id,
        brokerage=comm / 100,
        excess=attachment,
        deductible=0,
        inception_date=datetime.datetime.strftime(inception, "%d/%m/%Y"),
        expiry_date=datetime.datetime.strftime(expiry, "%d/%m/%Y"),
        adr_id=adr_id,
    )
    price = get_price_doww(input_doww)
    chart_slot.plotly_chart(
        price.waterfall(),
        use_container_width=True,
    )
    chart_slot_2.plotly_chart(
        price.bar_chart(),
        use_container_width=True,
    )
    price_out.subheader(f"Model Premium: ${price.price:,.2f}")

else:
    tab2.write("Please submit risk details!")
