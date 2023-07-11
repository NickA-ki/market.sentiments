from pandas import DataFrame, Series
import plotly.express as px
import plotly.graph_objects as go

from src.utils.utils import utils


def plot_article_sentiments(df: DataFrame, percentage: bool = True) -> px.bar:
    try:
        df_fig = (
            df.groupby(["YearMonth", "Score"])
            .size()
            .to_frame(name="Count")
            .reset_index()
        )

        df_fig["Percentage"] = (
            df_fig["Count"] / df_fig.groupby("YearMonth")["Count"].transform("sum")
        ) * 100

        color_discrete_map = {
            "Negative": "red",
            "Neutral": "lightgrey",
            "Positive": "green",
        }

        y_value = "Count"
        suffix = None

        if percentage:
            y_value = "Percentage"
            suffix = "%"

        fig = px.bar(
            df_fig,
            x="YearMonth",
            y=y_value,
            color="Score",
            color_discrete_map=color_discrete_map,
        )

        fig.update_layout(
            height=750,
            legend=dict(title="", orientation="h", xanchor="center", x=0.3, y=1.1),
            yaxis=dict(ticksuffix=suffix),
        )

        return utils.figure_layout(fig)

    except:
        return {}


def plot_major_loss_trend(df: DataFrame, loss_search: str = "Ian") -> go.Figure:
    ave_ml = int(
        round(df.groupby(["YearMonth"]).agg({"Title": Series.nunique}).Title.mean(), 0)
    )
    if len(loss_search) > 0:
        df_search = df[
            ~(df.Title.str.contains(loss_search))
            & ~(df.Summary.str.contains(loss_search))
        ]
    else:
        df_search = df

    df2 = df_search.groupby(["YearMonth"]).agg({"Title": Series.nunique}).reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(name="Articles", x=df2.YearMonth, y=df2.Title, marker_color="#E63b20")
    )
    if len(loss_search) > 0:
        df3 = (
            df[~df.Title.isin(df_search.Title.unique())]
            .groupby(["YearMonth"])
            .agg({"Title": Series.nunique})
            .reset_index()
        )
        fig.add_trace(
            go.Bar(
                name=f"{loss_search} Articles",
                x=df3.YearMonth,
                y=df3.Title,
                marker_color="lightgrey",
            )
        )
    fig.add_hline(
        y=df2.Title.mean(),
        line_width=2,
        line_dash="dash",
        line_color="black",
    )
    fig.add_annotation(
        y=ave_ml + 1,
        x=df2.YearMonth.unique()[-1],
        text=f"Average no. Reported Major Losses: {ave_ml}",
        showarrow=False,
        arrowhead=1,
    )
    # fig.add_vline(
    #     x=sorted(df3.YearMonth.unique())[0],
    #     line_width=2,
    #     line_dash="dash",
    #     line_color="black",
    # )
    # fig.add_annotation(x=5.3, y=50, text="Ian", showarrow=False, arrowhead=1)
    fig.update_layout(
        barmode="stack",
        height=550,
        yaxis=dict(title="# Major Loss Articles"),
        xaxis=dict(title="Date"),
        margin=dict(l=25, r=25, t=20, b=10),
        legend=dict(orientation="h", xanchor="center", x=0.5, y=1.1),
    )

    return utils.figure_layout(fig)
