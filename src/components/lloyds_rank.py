import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.utils import utils


def quartile_performance(lloyds: pd.DataFrame, COB: str = "") -> pd.DataFrame:
    df = lloyds[
        (lloyds["Year"] >= lloyds.Year.max() - 1)
        & (lloyds["LineItem"].isin(["Combined ratio"]))
        & (lloyds["LloydsGlobalCOB"] == COB)
        & (lloyds.Amount > 0)
    ][["Year", "SyndicateCode", "ManagingAgent", "Amount"]]

    df = (
        df.pivot(
            index=["ManagingAgent", "SyndicateCode"], columns="Year", values="Amount"
        )
        .reset_index()
        .assign(
            Quartile=lambda x: np.where(
                x[lloyds.Year.max()] <= x[lloyds.Year.max()].quantile(0.25),
                1,
                np.where(
                    x[lloyds.Year.max()] <= x[lloyds.Year.max()].quantile(0.5),
                    2,
                    np.where(
                        x[lloyds.Year.max()] <= x[lloyds.Year.max()].quantile(0.75),
                        3,
                        4,
                    ),
                ),
            ),
            Delta=lambda x: x[lloyds.Year.max()] - x[lloyds.Year.max() - 1],
        )
        .sort_values(["Quartile", lloyds.Year.max()])
        .reset_index(drop=True)
    )

    return df


def plot_cor_change(lloyds: pd.DataFrame, cob: str, syndicates: list = []) -> plt:
    df = quartile_performance(lloyds, cob).reset_index(drop=True)
    end_year = lloyds.Year.max()
    start_year = end_year - 1
    plt.style.use("default")

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 16), facecolor="white")
    ax.grid(axis="x")

    plt.hlines(
        y=df.SyndicateCode.astype(str),
        xmin=df[end_year],
        xmax=df[start_year],
        color="black",
        alpha=0.5,
    )
    plt.scatter(
        df[end_year],
        df.SyndicateCode.astype(str),
        alpha=1,
        label=f"{end_year}",
        color="red",
    )
    plt.scatter(
        df[start_year],
        df.SyndicateCode.astype(str),
        alpha=0.8,
        label=f"{start_year}",
    )
    plt.legend(loc="upper right", bbox_to_anchor=(1, 1.05))
    plt.title("Combined Ratio Change 2021 to 2022")
    plt.xlabel("Combined Ratio (%)")
    plt.ylabel("Syndicate")
    plt.axvline(x=100, ymin=0, ymax=1, color="black", linestyle=":")
    if syndicates:
        for syn in syndicates:
            try:
                pos = df[df.SyndicateCode == syn].index[0]
                plt.setp(ax.get_yticklabels()[pos], color="red")
            except:
                pass

    ax.set_facecolor("xkcd:white")
    ax.invert_yaxis()

    return fig
