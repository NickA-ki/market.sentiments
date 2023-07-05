import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import pandas as pd

from src.utils.utils import utils


def add_lloyds(
    cob_df: pd.DataFrame, lloyds: pd.DataFrame, COB: str, timeframe: int = 9
) -> pd.DataFrame:
    df = (
        lloyds[
            (lloyds["LloydsGlobalCOB"] == COB)
            & (lloyds.Year >= lloyds.Year.max() - timeframe)
            & (lloyds.Amount > 0)
        ]
        .groupby(["Year", "ManagingAgent", "SyndicateCode", "LineItem"])
        .agg({"Amount": np.mean})
        .reset_index()
        .pivot(
            index=["ManagingAgent", "SyndicateCode", "Year"],
            columns=["LineItem"],
            values=["Amount"],
        )
        .droplevel(0, axis=1)
        .reset_index()
        .dropna()
        .groupby("Year")
        .apply(
            lambda x: pd.Series(
                [
                    utils.weighted_mean(
                        x["Combined ratio"],
                        weights=x["Net"],
                    ),
                    np.sum(x["Net"]),
                    np.sum(x["Gross"]),
                ],
                index=["Combined ratio", "Net", "Gross"],
            )
        )
        .assign(ManagingAgent="Lloyd's", SyndicateCode="Lloyd's")
        .reset_index()
    )
    cob_df = pd.concat([cob_df, df])
    return cob_df


def historic_cob(
    lloyds: pd.DataFrame,
    COB: str,
    syndicates: list,
    timeframe: int = 9,
    net: float = 20,
) -> pd.DataFrame:
    df = (
        lloyds[
            (lloyds["LloydsGlobalCOB"] == COB)
            & (lloyds.ActiveSyndicateFlag == "Active")
            & (lloyds.Year >= lloyds.Year.max() - timeframe)
            & (lloyds.Amount > 0)
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
    df2 = add_lloyds(df, lloyds, COB, timeframe)
    all_syndicates = np.append(
        syndicates,
        df2[df2["Year"] == lloyds.Year.max()]
        .sort_values("Net", ascending=False)["SyndicateCode"]
        .unique(),
    )
    df2 = (
        df2[df2.SyndicateCode.isin(all_syndicates)]
        .dropna()
        .groupby(["ManagingAgent", "SyndicateCode"])
        .apply(
            lambda x: pd.Series(
                [
                    utils.weighted_mean(
                        x["Combined ratio"],
                        weights=x["Net"],
                    ),
                    (np.std(x["Combined ratio"]) / np.mean(x["Combined ratio"])) * 100,
                    (np.mean(x.Net)),
                ],
                index=["NCOR", "Volatility", "Net"],
            )
        )
        .reset_index()
        .dropna()
        .assign(
            color=lambda x: np.where(
                x.SyndicateCode.isin(syndicates),
                "#e63b20",
                np.where(x.SyndicateCode == "Lloyd's", "blue", "black"),
            ),
            symbol=lambda x: np.where(
                x.SyndicateCode.isin(syndicates),
                "circle",
                np.where(x.SyndicateCode == "Lloyd's", "diamond", "circle"),
            ),
        )
        .query(f"Net >= {net} and NCOR < 200 and Volatility > 0")
        .reset_index(drop=True)
    )

    return df2


def plot_syndicate_quadrant(
    lloyds: pd.DataFrame,
    COB: str,
    syndicates: list,
    timeframe: int = 9,
    net: float = 20,
) -> go.Figure:
    df = historic_cob(lloyds, COB, syndicates, timeframe, net)
    dFig = df[df["ManagingAgent"] != "Lloyd's"]
    lloyds_ref = df[df["ManagingAgent"] == "Lloyd's"]
    dFig = dFig.sort_values(["Net"], ascending=False)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name=f"Size = Average Net Premium (£m)",
            x=dFig["NCOR"],
            y=dFig["Volatility"],
            mode="markers+text",
            text=dFig["SyndicateCode"],
            textposition="top center",
            marker=dict(
                color=dFig["color"],
                symbol=dFig["symbol"],
                size=dFig["Net"].fillna(dFig["Net"].min()),
                sizemode="area",
                sizeref=2 * (dFig["Net"].fillna(dFig["Net"].min()).max()) / (40.0**2),
                sizemin=4,
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Lloyds Reference",
            x=lloyds_ref["NCOR"],
            y=lloyds_ref["Volatility"],
            mode="markers+text",
            text=lloyds_ref["SyndicateCode"],
            textposition="top center",
            marker=dict(color=lloyds_ref["color"], symbol="diamond", size=12),
        )
    )
    fig.update_xaxes(title="Weighted NCOR %", autorange="reversed")
    fig.update_yaxes(title="Volatility", autorange="reversed")
    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="x",
                yref="y",
                x0=100,
                y0=dFig["Volatility"].mean(),
                x1=dFig["NCOR"].min() - 5,
                y1=0.1,
                fillcolor="lightgreen",
                opacity=0.2,
                line_width=0,
                layer="below",
            ),
            dict(
                type="rect",
                xref="x",
                yref="y",
                x0=100,
                y0=dFig["Volatility"].mean(),
                x1=dFig["NCOR"].max() + 1,
                y1=dFig["Volatility"].max() + 1,
                fillcolor="red",
                opacity=0.2,
                line_width=0,
                layer="below",
            ),
            dict(
                type="rect",
                xref="x",
                yref="y",
                x0=100,
                y0=dFig["Volatility"].mean(),
                x1=dFig["NCOR"].max() + 1,
                y1=0.1,
                fillcolor="#CFBC96",
                opacity=0.4,
                line_width=0,
                layer="below",
            ),
            dict(
                type="rect",
                xref="x",
                yref="y",
                x0=100,
                y0=dFig["Volatility"].mean(),
                x1=dFig["NCOR"].min() - 5,
                y1=dFig["Volatility"].max() + 1,
                fillcolor="#CFBC96",
                opacity=0.4,
                line_width=0,
                layer="below",
            ),
        ]
    )
    fig.add_vline(x=100, line_dash="dot")
    fig.add_hline(y=dFig["Volatility"].mean(), line_dash="dot")
    fig.update_layout(
        title=f"Weighted NCOR vs Volatility vs Net - {COB}",
        autosize=False,
        xaxis=dict(ticksuffix="%"),
        yaxis=dict(title="Volatility CoV"),
        width=1600,
        height=800,
        margin=dict(l=50, r=50, b=10, t=50, pad=2),
    )

    return utils.figure_layout(fig)
