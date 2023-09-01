import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dateutil import parser
from datetime import datetime
from functools import reduce
from math import prod
from typing import Callable, Optional, Any, List, Dict
from dataclasses import dataclass

DOWW_LISTED_INDICATOR_PUBLIC: str = "No ADR"


@dataclass
class MetaData:
    metadata = pd.read_csv("./data/do_metadata.csv")

    DOMICILE_RATE = dict(zip(*metadata.iloc[:, 0:2].dropna().values.T))

    INDUSTRY_RATE = dict(zip(*metadata.iloc[:, 2:4].dropna().values.T))

    LISTING_RATE = dict(zip(*metadata.iloc[:, 4:6].dropna().values.T))

    LISTINGADR_RATE = dict(zip(*metadata.iloc[:, 6:8].dropna().values.T))

    COVER_RATE = dict(zip(*metadata.iloc[:, 8:10].dropna().values.T))

    RETRO_RATE = dict(zip(*metadata.iloc[:, 10:12].dropna().values.T))

    FIXED_FACTOR = 1.1

    def ilf_cuve(x: float) -> float:
        """
        Ilf Curve

        params:
            x is the limit/excess value (eg 1e6)

        returns:
            ilf factor for a given x
        """
        base_limit = 1e6
        z = 1.9704
        return (x / base_limit) ** np.emath.logn(1 + z, 2)


@dataclass
class RequestDOWW:
    y_o_a: int
    limit: float
    other_commissions: float
    assets: float
    country_id: int
    industry_id: int
    listed_indicator_id: int
    cover_id: int
    retro_option_id: int
    brokerage: float
    excess: float
    deductible: float
    inception_date: datetime
    expiry_date: datetime
    listing_array: Optional[str] = None
    adr_id: Optional[int] = None

    def __post_init__(self):
        self.inception_date = parser.parse(self.inception_date, dayfirst=True)
        self.expiry_date = parser.parse(self.expiry_date, dayfirst=True)


@dataclass
class FactorsDOWW:
    limit_plus_excess: float
    excess: float
    country: float
    industry: float
    listed_indicator: float
    listingadr: float
    cover: float
    retro_date: float
    fixed: float  # Adjustments to Model Price
    brokerage: float
    profit: float

    @property
    def ilf(self) -> float:
        if self.limit_plus_excess != self.excess:
            return self.limit_plus_excess - self.excess

        return self.excess

    @property
    def multiplier(self):
        return prod(
            [
                self.ilf,
                self.country,
                self.industry,
                self.listed_indicator,
                self.listingadr,
                self.cover,
                self.retro_date,
                self.fixed,
            ]
        )


@dataclass
class ResponsePrice:
    base_loss_cost: float
    annual_risk_premium: float
    risk_premium: float
    risk_premium_with_commission_loading: float
    risk_premium_with_commission_inflation_loadings: float
    price: Any
    bar_chart_features: List
    bar_chart_multipliers: List
    sub_divided_price: Optional[Any] = None

    def waterfall(self) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(
            go.Waterfall(
                measure=[
                    "absolute",
                    "relative",
                    "relative",
                    "relative",
                    "relative",
                    "total",
                ],
                x=[
                    "Base - Assets ($USD)",
                    "Factors",
                    "Term Adjustment",
                    "Brokerage",
                    "Profit Target (ULR)",
                    "Price ($USD)",
                ],
                y=[
                    self.base_loss_cost,
                    self.annual_risk_premium - self.base_loss_cost,
                    self.risk_premium - self.annual_risk_premium,
                    self.risk_premium_with_commission_inflation_loadings
                    - self.risk_premium,
                    self.price - self.risk_premium_with_commission_inflation_loadings,
                    self.price,
                ],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                text=[
                    f"${self.base_loss_cost:,.2f}",
                    f"${self.annual_risk_premium - self.base_loss_cost:,.2f}",
                    f"${self.risk_premium - self.annual_risk_premium:,.2f}",
                    f"${self.risk_premium_with_commission_inflation_loadings - self.risk_premium:,.2f}",
                    f"${self.price - self.risk_premium_with_commission_inflation_loadings:,.2f}",
                    f"${self.price:,.2f}",
                ],
            )
        )
        fig.update_layout(
            template="plotly_white",
            title="Pricing Walkthrough",
            yaxis=dict(title="Premium ($USD)", tickprefix="$"),
            xaxis=dict(title="Adjustments"),
        )
        return fig

    def bar_chart(self) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=self.bar_chart_features,
                y=self.bar_chart_multipliers,
                text=[f"{x:.2f}" for x in self.bar_chart_multipliers],
                marker=dict(
                    color=np.where(
                        np.array(self.bar_chart_multipliers) >= 1, "black", "red"
                    )
                ),
            )
        )
        fig.add_hline(y=1, line_dash="dash")
        fig.add_hline(
            y=np.prod(self.bar_chart_multipliers), line_dash="dash", line_color="blue"
        )
        fig.add_annotation(
            x=8,
            y=np.prod(self.bar_chart_multipliers),
            text=f"Overall multipler: {np.prod(self.bar_chart_multipliers):.2f}",
        )
        fig.update_layout(
            template="plotly_white",
            title="Factor Breakdown",
            yaxis=dict(title="Multiplier", tickprefix=""),
            xaxis=dict(title="Factors", categoryorder="total descending"),
        )
        return fig


def get_target_loss_ratio(class_name: str, year_of_account: int) -> float:
    """
    Method to get target loss ratio information from the metadata api

    params:
        class_name: class name (eg "Cyber")
        year_of_account: Year of account (eg 2021)

    returns:
        Target loss ratio
    """

    # params = {"class_name": class_name, "year_of_account": year_of_account}
    # result: Dict = self._get_request_json(self.base_url + self.target_lr_path, params)
    # result["target_loss_ratio_value"]

    return 0.731


class EnvironmentVariableError(Exception):
    """Environment Variable missing or incorrect"""


def ensure_config_variables(required_config_variables: Dict[str, Any]):
    if any(var_value == -1 for _, var_value in required_config_variables.items()):
        raise EnvironmentVariableError(
            f"not all of the required config variables were set: "
            f"{required_config_variables}"
        )


def brokerage_adjustment(
    brokerage: float, other_commissions: float, brokerage_multiplier: float = 1
) -> float:
    if brokerage + other_commissions == 1:
        brokerage_adj = 1
    else:
        brokerage_adj = brokerage_multiplier / (1 - brokerage - other_commissions)
    return brokerage_adj


def term_adjustment(
    expiry_date: datetime,
    inception_date: datetime,
    model_premium: float,
) -> float:
    if abs((expiry_date - inception_date).days - 365) <= 2:
        adjustment = 1
    else:
        adjustment = ((expiry_date - inception_date).days + 1) / 365

    return model_premium * adjustment


def get_doww_factors(input_doww: RequestDOWW, metadata: MetaData) -> FactorsDOWW:
    class_name = "DO WW"

    country_factor = metadata.DOMICILE_RATE[input_doww.country_id]

    industry_factor = metadata.INDUSTRY_RATE[input_doww.industry_id]

    listed_indicator_factor = metadata.LISTING_RATE[input_doww.listed_indicator_id]

    if input_doww.adr_id != DOWW_LISTED_INDICATOR_PUBLIC:
        listingadr_factor = metadata.LISTINGADR_RATE[input_doww.adr_id]
    else:
        listingadr_factor = 1

    cover_factor = metadata.COVER_RATE[input_doww.cover_id]

    retro_factor = metadata.RETRO_RATE[input_doww.retro_option_id]

    fixed_factor = metadata.FIXED_FACTOR

    limit_plus_excess_factor = metadata.ilf_cuve(input_doww.limit + input_doww.excess)
    excess_factor = metadata.ilf_cuve(input_doww.excess)

    brokerage_factor = brokerage_adjustment(
        input_doww.brokerage, input_doww.other_commissions
    )

    profit_factor = 1 / get_target_loss_ratio(
        class_name=class_name, year_of_account=input_doww.y_o_a
    )

    factors = FactorsDOWW(
        limit_plus_excess=limit_plus_excess_factor,
        excess=excess_factor,
        country=country_factor,
        industry=industry_factor,
        listed_indicator=listed_indicator_factor,
        listingadr=listingadr_factor,
        cover=cover_factor,
        retro_date=retro_factor,
        fixed=fixed_factor,
        brokerage=brokerage_factor,
        profit=profit_factor,
    )
    return factors


def get_price_doww(input_doww: RequestDOWW) -> float:
    ensure_config_variables(
        {
            "DOWW_LISTED_INDICATOR_PUBLIC": DOWW_LISTED_INDICATOR_PUBLIC,
        }
    )
    # Populate factors
    metadata = MetaData

    factors: FactorsDOWW = get_doww_factors(input_doww, metadata)
    # record_factors(input_doww, factors, DOWW) NOTE: send to a db to record values

    # Annual Risk Premium: Price from pricing model
    multiplier = factors.multiplier

    base_loss_cost = input_doww.assets

    model_premium = multiplier * base_loss_cost

    # Risk Premium: Price adjusted for term
    adjusted_model_premium = term_adjustment(
        input_doww.expiry_date, input_doww.inception_date, model_premium
    )

    # Risk Premium With Commission Loading: Price adjusted for commission/brokerage
    gross_premium = adjusted_model_premium * factors.brokerage

    # Risk Premium With Commission Inflation Loadings: Price adjusted for inflation
    # net_inflation = get_inflation_figures(
    #     yoa=input_doww.y_o_a, class_name="DO WW", metadata_api=metadata_api, inflating_exposure_measure=True
    # )

    inflated_price = gross_premium  # * (net_inflation)

    # Price: Calculated final price
    price = inflated_price * factors.profit

    # Set params for factors bar chart
    features = [
        a
        for a in dir(factors)
        if not a.startswith("__")
        and not a.startswith("limit_plus")
        and not a.startswith("multi")
        and not a.startswith("excess")
    ]
    multipliers = [factors.__getattribute__(i) for i in features]

    return ResponsePrice(
        base_loss_cost=base_loss_cost,
        annual_risk_premium=model_premium,
        risk_premium=adjusted_model_premium,
        risk_premium_with_commission_loading=gross_premium,
        risk_premium_with_commission_inflation_loadings=inflated_price,
        price=price,
        bar_chart_features=features,
        bar_chart_multipliers=multipliers,
    )
