import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats


from dataclasses import dataclass
from src.utils.utils import utils


class ExposureSeverity(stats.rv_continuous):
    """
    Class function to convert bernegger cdf into pdf and rvs functions.
    cdf is: F(x) = { 1- G'(x)/G'(0), 1 for 0<= x < 1, x = 1
    """

    def __init__(self, xtol=1e-14, seed=None):
        super().__init__(a=0, xtol=xtol, seed=seed)

    def _cdf(self, x, b, g):
        if x[0] >= 1:
            return 1
        else:
            """
            Equation from PIGI, page 415 (eq. 22.17)
            Assumes c=4 to calculate bernegger params b, g
            """
            return (b * (g - 1) * (1 - (b**x))) / (
                (b * (g - 1)) + ((1 - b * g) * b**x)
            )


@dataclass
class ExposureRating:
    swiss_re_c: str
    selected_loss_ratio: float
    _exposure: pd.DataFrame
    attachment: float
    limit: float
    subject_premium: float

    def __post_init__(self):
        self.b = np.exp(3.1 + (-0.15 * self.swiss_re_c * (1 + self.swiss_re_c)))
        self.g = np.exp((0.78 + (0.12 * self.swiss_re_c)) * self.swiss_re_c)
        self.mean_damage_ratio = (np.log(self.b * self.g) * (1 - self.b)) / (
            np.log(self.b) * (1 - self.b * self.g)
        )

    def bernegger(self, x: float) -> float:
        """
        Bernegger curve for b > 0, b != 1, bg != 1 and g > 1.
        Refer to PIGI for alternative forms if conditions breach the criteria above.
        Reference page 414 (eq. 22.16)
        """
        if x > 1:
            return 1.0
        else:
            return np.log(
                ((self.g - 1) * self.b + (1 - self.b * self.g) * self.b**x)
                / (1 - self.b)
            ) / np.log(self.b * self.g)

    def exposure_rating(
        self, results: bool = False, results_type: str = "dict", verbose: bool = True
    ) -> pd.DataFrame:
        exposure = self._exposure.copy()
        exposure["expected_loss"] = exposure["Premium"] * self.selected_loss_ratio
        exposure["premium_pct"] = exposure["Premium"] / self.subject_premium
        exposure["d"] = self.attachment / ((exposure.Upper + exposure.Lower) / 2)
        exposure["d + l"] = (self.attachment + self.limit) / (
            (exposure.Upper + exposure.Lower) / 2
        )
        exposure["d + 1"] = (self.attachment + 1) / (
            (exposure.Upper + exposure.Lower) / 2
        )

        exposure["G(d)"] = utils.vectorize(self.bernegger, exposure["d"])
        exposure["G(d+l)"] = utils.vectorize(self.bernegger, exposure["d + l"])
        exposure["G(d+1)"] = utils.vectorize(self.bernegger, exposure["d + 1"])

        exposure["claim_pct"] = exposure["G(d+l)"] - exposure["G(d)"]
        exposure["claim_freq_pct"] = exposure["G(d+1)"] - exposure["G(d)"]
        exposure["loss_cost_to_layer"] = exposure.expected_loss * exposure.claim_pct
        exposure["freq_to_layer"] = (
            self.subject_premium
            * self.selected_loss_ratio
            * exposure["premium_pct"]
            * exposure["claim_freq_pct"]
        )
        if verbose:
            print("-" * 80)
            print(f"Layer: ${self.attachment/1e6:.0f}m xs ${self.limit/1e6:.0f}m")
            print("-" * 80)
            print(f"Overall cost to layer: ${exposure.loss_cost_to_layer.sum():,.2f}")
            print(f"No of claims: {exposure.freq_to_layer.sum():.2f}")
            print("-" * 80)
        if results:
            match results_type:
                case "dict":
                    return {
                        "claims": exposure.loss_cost_to_layer.sum(),
                        "frequency": exposure.freq_to_layer.sum(),
                    }
                case "dataframe":
                    return exposure
                case _:
                    print("unspecified type. Please select dict or dataframe")

    def plot_exposure_curve(self) -> go.Figure:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        x = np.arange(0, 1.01, 0.01)
        exp_sev_rv = ExposureSeverity()
        fig.add_trace(
            go.Scatter(
                name="Exposure Curve",
                mode="lines",
                x=x,
                y=utils.vectorize(self.bernegger, x),
                line_color="#FF3333",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Severity Curve",
                x=x,
                y=exp_sev_rv.cdf(x, self.b, self.g),
                mode="lines",
                line_color="#33ff99",
            ),
            secondary_y=True,
        )
        fig.update_yaxes(matches="y")
        fig.update_layout(
            yaxis=dict(title="Probability damage ratio does not exceed value"),
            yaxis2=dict(title="Percentage of risk retained by (re)insured"),
            xaxis=dict(title="Dame Ratio / Deductible as a % of SI"),
            legend=dict(yanchor="bottom", xanchor="right"),
        )
        return utils.figure_layout(fig)
