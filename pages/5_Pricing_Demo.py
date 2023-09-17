import streamlit as st
import pandas as pd
import numpy as np
import datetime

from src.utils.utils import utils
from data.source import source
from src.components.pricing_demo import (
    get_price_doww,
    aggregate_loss_model,
    aggregate_table,
    confidence_interval,
    aggregate_chart,
    frequency_chart,
    severity_chart,
    RequestDOWW,
    MetaData,
)
from src.components.exposure import ExposureRating

# NOTE: load data ------
exposure = source.load_init_exposure()

# Page Header ----
utils.page_title("Pricing Demo")

# Set up tab structure:
tab1, tab2, tab3, tab4 = st.tabs(
    ["Inputs", "Summary", "Aggregate Loss Model", "Exposure Rating"]
)

# Input form to collect features:
with tab1:
    layer_out = st.empty()
    loss_out = st.empty()
    price_out = st.empty()
    form = st.form("do_ww")
    form.subheader("D&O")
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
    layer_out.subheader(f"Layer: &#36;{limit/1e6:.0f}m xs &#36;{attachment/1e6:.0f}m")
    loss_out.subheader(f"Expected loss cost: ${price.risk_premium:,.2f}")
    price_out.subheader(f"Model Premium: ${price.price:,.2f}")

else:
    tab2.write("Please submit risk details!")

with tab3:
    col_a, col_b = st.columns(2)
    agg_form = col_a.form("agg_form")
    frequency = agg_form.selectbox(
        "Frequency Distribution", ["Poisson", "NBinomial", "Zero-Inflated Poisson"]
    )
    freq_mean = agg_form.number_input(
        "Average Claim Frequency:",
        min_value=0.0,
        max_value=200.0,
        value=10.0,
        step=0.1,
    )
    freq_sd = agg_form.number_input(
        "Std Dev Claim Frequency:",
        min_value=0.0,
        max_value=200.0,
        value=4.6,
        step=0.1,
    )
    freq_zi_p = agg_form.number_input(
        "Claim Rate (%) (only for Zero Inflated):",
        min_value=0.0,
        max_value=100.0,
        value=20.0,
        step=0.1,
    )
    freq_zi_p /= 100
    if freq_sd**2 / freq_mean < 1 and frequency == "NBinomial":
        agg_form.warning(
            "Var/Mean ratio is < 1, consider Poisson distribution", icon="⚠️"
        )
    agg_form.divider()
    severity = agg_form.selectbox("Severity Distribution", ["LogNormal", "Gamma"])
    sev_mean = agg_form.number_input(
        "Average Claim Severity:",
        min_value=0,
        max_value=10000000,
        value=215000,
        step=1,
    )
    sev_sd = agg_form.number_input(
        "Std Dev Claim Severity:",
        min_value=0,
        max_value=10000000,
        value=750000,
        step=1,
    )
    agg_form.divider()
    rp = agg_form.slider("@ Risk Return Period:", 1, 1000, 250)
    agg_form.divider()
    limit2 = agg_form.number_input(
        "Select Limit ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=1e5,
        step=1e0,
        format="%f",
    )

    attachment2 = agg_form.number_input(
        "Select Attachment ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=2.5e4,
        step=1e0,
        format="%f",
    )
    aad = agg_form.number_input(
        "Select AAD ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=0e6,
        step=1e0,
        format="%f",
    )
    aal = agg_form.number_input(
        "Select AAL ($USD):",
        min_value=0e6,
        max_value=100e6,
        value=0e6,
        step=1e0,
        format="%f",
    )
    ground_up = agg_form.checkbox("Apply layer details")

    agg_results = col_b.empty()
    agg_table = col_b.empty()
    agg_chart = col_b.empty()
    agg_submitted = agg_form.form_submit_button("Submit")

if agg_submitted:
    n_sims = 1000
    sim_losses = aggregate_loss_model(
        severity,
        frequency,
        sev_mean,
        sev_sd,
        freq_mean,
        freq_sd,
        freq_zi_p,
        limit2,
        attachment2,
        aad,
        aal,
        n_sims,
        not ground_up,
    )
    ci = confidence_interval(sim_losses, 0.95)
    up_down = aggregate_table(sim_losses)
    agg_results.markdown(
        f"""
        Agg Model Results
        {"-"*60}
        - Mean Agg loss: &#36;{np.mean(sim_losses):,.0f} with 95% CI: &#36;{ci[0]:,.0f}, &#36;{ci[1]:,.0f}
        - Std Agg loss: ${np.std(sim_losses):,.0f}
        - CoV: {(np.std(sim_losses)/np.mean(sim_losses))*100:.0f}%
        - VaR @1-in-{rp}: ${np.mean(sim_losses[int(n_sims/rp)]):,.0f}
        - SVaR @1-in-{rp}+/-25: ${np.mean(sim_losses[int(n_sims/(rp + 25)):int(n_sims/(rp-25))]):,.0f}
        - TVaR @1-in-{rp}: ${np.mean(sim_losses[:int(n_sims/rp)]):,.0f}
        """
    )
    agg_table.dataframe(
        up_down,
        hide_index=True,
        use_container_width=True,
    )
    # agg_table.dataframe(
    #     up_down.style.applymap(utils.highlight_column, subset=["Percentile"]),
    #     hide_index=True,
    #     use_container_width=True,
    # )
    tab_a, tab_b, tab_c = agg_chart.tabs(["Agg Distribution", "Frequency", "Severity"])
    with tab_a:
        st.plotly_chart(
            aggregate_chart(sim_losses, rp, n_sims),
            use_container_width=True,
        )
    with tab_b:
        st.plotly_chart(
            frequency_chart(frequency, freq_mean, freq_sd, freq_zi_p, n_sims),
            use_container_width=True,
        )
    with tab_c:
        st.plotly_chart(
            severity_chart(severity, sev_mean, sev_sd, n_sims),
            use_container_width=True,
        )

else:
    agg_results.write("Submit distribution features...")

with tab4:
    col_i, col_ii = st.columns(2)
    swiss_re_c = col_i.number_input(
        "Swiss Re C Param:",
        min_value=0.0,
        max_value=8.0,
        value=5.83,
        step=0.2,
    )
    selected_loss_ratio = col_i.number_input(
        "Loss Ratio (%):",
        min_value=0.0,
        max_value=200.0,
        value=48.4,
        step=0.5,
    )
    col_i.divider()
    subject_premium = col_i.number_input(
        "Subject Premium ($USD):",
        min_value=0e6,
        max_value=10e9,
        value=6.109637565e9,
        step=1e0,
        format="%f",
    )
    limit3 = col_i.number_input(
        "Select Limit ($USD):",
        min_value=0e6,
        max_value=10e9,
        value=20e6,
        step=1e0,
        format="%f",
    )
    attachment3 = col_i.number_input(
        "Select Attachment ($USD):",
        min_value=0e6,
        max_value=10e9,
        value=20e6,
        step=1e0,
        format="%f",
    )
    col_i.divider()
    edited_df = col_i.data_editor(
        exposure, use_container_width=True, hide_index=True, num_rows="dynamic"
    )
    exposure_rating = ExposureRating(
        swiss_re_c,
        selected_loss_ratio / 100,
        edited_df,
        attachment3,
        limit3,
        subject_premium,
    )
    results = exposure_rating.exposure_rating(
        results=True, results_type="dict", verbose=False
    )
    col_ii.markdown(
        f"""
        Results
        {"-"*60}
        - Loss Cost ($USD): **&#36;{results['claims']:,.2f}**
        - No. Claims: **{results['frequency']:.2f}**
        - Mean Damage Ratio: **{exposure_rating.mean_damage_ratio:.2f}**
        """
    )
    col_ii.plotly_chart(
        exposure_rating.plot_exposure_curve(),
        use_container_width=True,
    )
