from src.utils.copula import Copula
from functools import lru_cache
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px


class LloydsModel(Copula):
    def __init__(
        self, lloyds: pd.DataFrame, lloyds_cob: str, start_year: int = 2012
    ) -> None:
        super().__init__()
        self._lloyds = lloyds
        self.lloyds_cob = lloyds_cob
        self.start_year = start_year
        self.no_sims = 10000
        self.weight_dict = self.create_default_weight()

    @lru_cache(maxsize=1)
    def create_syndicate_year_df(self) -> pd.DataFrame:
        syndicate_results = (
            self._lloyds[
                (self._lloyds["LloydsGlobalCOB"] == self.lloyds_cob)
                & (self._lloyds.Year >= self.start_year)
                & (self._lloyds.ActiveSyndicateFlag == "Active")
                & (self._lloyds.LineItem.isin(["Combined ratio", "Net"]))
                & (self._lloyds.Amount > 0)
            ]
            .groupby(["ManagingAgent", "SyndicateCode", "Year", "LineItem"])
            .agg({"Amount": sum})
            .reset_index()
            .pivot(
                index=["ManagingAgent", "SyndicateCode", "Year"],
                columns="LineItem",
                values="Amount",
            )
            .reset_index()
        )

        return self.apply_weightings(syndicate_results)

    @lru_cache(maxsize=1)
    def create_mu_std_df(self, net: float = 20) -> pd.DataFrame:
        syndicate_df = self.create_syndicate_year_df()
        syndicate_mu_sd = (
            syndicate_df.dropna()
            .groupby(["ManagingAgent", "SyndicateCode"])
            .apply(
                lambda x: pd.Series(
                    [
                        np.average(x["Combined ratio"], weights=x["weight"]),
                        np.std(x["Combined ratio"]),
                        np.mean(x.Net),
                    ],
                    index=["Mean", "Std", "Net"],
                )
            )
            .reset_index()
            .dropna(subset=["Mean"])
            .query(f"Net >= {net}")
            .reset_index(drop=True)
        )
        return syndicate_mu_sd

    @lru_cache(maxsize=1)
    def create_model(self, alpha: float = 2, net: float = 20) -> pd.DataFrame:
        syndicate_mu_sd = self.create_mu_std_df(net)
        model = np.zeros(shape=(syndicate_mu_sd.shape[0], self.no_sims))
        # Generate lognormal distribution ----
        for index, row in syndicate_mu_sd.iterrows():
            m = syndicate_mu_sd.loc[index, "Mean"]
            v = syndicate_mu_sd.loc[index, "Std"]
            sigma = np.sqrt(np.log(1 + (v / m**2)))
            mu = np.log(m) - (0.5 * (sigma) ** 2)
            model[index] = np.random.lognormal(mu, sigma, self.no_sims)

        # Apply correlation ---
        corr = np.transpose(
            self.copulaInvClayton(self.no_sims, model.shape[0], alpha=alpha)
        )
        for row in range(0, model.shape[0], 1):
            model[row, :] = [x for _, x in sorted(zip(corr[row, :], model[row, :]))]

        # Convert to quartile results ---
        model_q = model.copy()
        for col in range(0, model.shape[1], 1):
            model_q[:, col] = pd.qcut(model[:, col], 4).codes + 1

        model_final = syndicate_mu_sd.copy()
        for i in [1, 2, 3, 4]:
            model_final[f"Q{i}"] = pd.Series(
                np.where(model_q == i, 1, 0).sum(axis=1) / self.no_sims
            )

        return model_final

    def create_quartile_monements(self) -> pd.DataFrame:
        syn_df = self.create_syndicate_year_df()
        data = (
            syn_df.query(f"Year >= {syn_df.Year.max() - 1}")
            .pivot(
                index=["ManagingAgent", "SyndicateCode"],
                columns=["Year"],
                values=["Combined ratio"],
            )
            .droplevel(level=0, axis=1)
            .reset_index()
            .dropna()
        )
        data[syn_df.Year.max()] = pd.qcut(data[syn_df.Year.max()].values, 4).codes + 1
        data[syn_df.Year.max() - 1] = (
            pd.qcut(data[syn_df.Year.max() - 1].values, 4).codes + 1
        )
        data = (
            data.groupby([2020, 2021])
            .agg(Count=("SyndicateCode", "nunique"))
            .reset_index()
            .assign(Count=lambda x: x.Count / x.Count.sum())
            .pivot(index=[2020], columns=[2021], values=["Count"])
            .droplevel(level=0, axis=1)
            .reset_index()
        )
        return data

    def plot_model_output(
        self,
        alpha: float,
        net: float = 20,
        head: bool = True,
        syndicates: bool = False,
        n: int = 20,
        codes: list = [],
    ) -> sns.FacetGrid:
        model_final = self.create_model(alpha, net)
        if head:
            model_df = (
                model_final.sort_values("Q1", ascending=False)[
                    ["SyndicateCode", "Q1", "Q2", "Q3", "Q4"]
                ]
                .head(n)
                .set_index("SyndicateCode")
            )
        else:
            model_df = (
                model_final.sort_values("Q4", ascending=False)[
                    ["SyndicateCode", "Q1", "Q2", "Q3", "Q4"]
                ]
                .head(n)
                .set_index("SyndicateCode")
            )
        if syndicates:
            model_df = (
                model_final.sort_values("Q1", ascending=False)[
                    ["SyndicateCode", "Q1", "Q2", "Q3", "Q4"]
                ]
                .query(f"SyndicateCode.isin({codes})")
                .set_index("SyndicateCode")
            )
        fig = plt.figure(figsize=(5, 10))
        sns.heatmap(
            model_df, annot=True, fmt=".1%", linewidths=0.5, cmap="viridis", cbar=False
        ).set_title(f"{self.lloyds_cob} - Quartile")
        # for t in ax.texts: t.set_text(f"{float(t.get_text())*100}%")
        plt.tick_params(
            axis="both",
            which="major",
            labelsize=10,
            labelbottom=False,
            bottom=False,
            top=False,
            labeltop=True,
        )
        ax = plt.gca()
        if codes:
            for syn in codes:
                try:
                    pos = model_df.index.get_loc(syn)
                    plt.setp(ax.get_yticklabels()[pos], color="red")
                except:
                    pass
        return fig

    def plot_correlation_alpha(self, alpha: int = 2) -> px.scatter:
        corr = np.transpose(self.copulaInvClayton(10000, 2, alpha=alpha))
        fig = px.scatter(
            x=corr[0], y=corr[1], color_discrete_sequence=sns.color_palette("Spectral")
        )
        fig.update_layout(template="plotly_white")
        return fig

    def plot_event_year_kde(self) -> sns.FacetGrid:
        sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
        data = self.create_syndicate_year_df()
        # Set data
        df = data[(data["Combined ratio"] < 200)]

        # Initialize the FacetGrid object
        pal = sns.cubehelix_palette(10, rot=-0.25, light=0.7)
        g = sns.FacetGrid(
            df, row="Year", hue="Year", aspect=15, height=0.8, palette="viridis"
        )  # Can sub viridis for pal etc

        # Draw the densities in a few steps
        g.map(
            sns.kdeplot,
            "Combined ratio",
            bw_adjust=0.6,
            clip_on=False,
            fill=True,
            alpha=1,
            linewidth=1.5,
        )
        g.map(
            sns.kdeplot, "Combined ratio", clip_on=False, color="w", lw=2, bw_adjust=0.6
        )

        for ax in g.axes.flat:
            for line in ax.lines:
                j = 4
                colours2 = sns.color_palette("Spectral")[::-1]
                for i in [1, 0.8, 0.6, 0.4, 0.2]:
                    first_x = np.quantile(line.get_xdata(), i)
                    x = line.get_xydata()[:, 0][line.get_xydata()[:, 0] <= first_x]
                    first_y = line.get_xydata()[:, 1][
                        line.get_xydata()[:, 0] <= first_x
                    ]
                    ax.fill_between(x, first_y, color=colours2[j])
                    j -= 1

        # passing color=None to refline() uses the hue mapping
        g.refline(y=0, linewidth=2, linestyle="-", color="black", clip_on=False)

        # Define and use a simple function to label the plot in axes coordinates
        def label(x, color, label):
            ax = plt.gca()
            ax.text(
                0,
                0.2,
                label,
                fontweight="bold",
                color=color,
                ha="left",
                va="center",
                transform=ax.transAxes,
            )

        g.map(label, "Combined ratio")

        # Set the subplots to overlap
        g.figure.subplots_adjust(hspace=-0.3)

        # Remove axes details that don't play well with overlap
        g.set_titles("")
        g.set(yticks=[], ylabel="")
        g.despine(bottom=True, left=True)
        legend_items = []
        q = 1
        for i in colours2[:-1]:
            legend_items.append(mpatches.Patch(color=i, label=f"Q{q}"))
            q += 1
        plt.legend(
            handles=legend_items, bbox_to_anchor=(1, 8.6), title="Quintiles"
        ).get_frame().set_facecolor("white")
        return g

    def create_default_weight(self) -> pd.DataFrame:
        values = [1] * len(self._lloyds.Year.unique())
        keys = list(range(self._lloyds.Year.min(), self._lloyds.Year.max() + 1, 1))
        weights_dict = {keys[i]: values[i] for i in range(len(keys))}
        return weights_dict

    def update_dict(self, key: int, value: int) -> dict:
        self.weight_dict[key] = value
        return self.weight_dict

    def apply_weightings(self, data: pd.DataFrame) -> pd.DataFrame:
        weight_df = pd.DataFrame.from_dict(
            self.weight_dict, orient="index"
        ).reset_index()
        weight_df.columns = ["Year", "weight"]
        data = data.merge(weight_df, how="left", on="Year")
        return data

    def get_weight_dict(self) -> dict:
        return self.weight_dict
