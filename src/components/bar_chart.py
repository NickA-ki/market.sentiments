import pandas as pd
import plotly.express as px


def plot_article_sentiments(df: pd.DataFrame, percentage: bool = True) -> px.bar:
    df_fig = df.groupby(["Date", "Score"]).size().to_frame(name="Count").reset_index()

    df_fig["Percentage"] = (
        df_fig["Count"] / df_fig.groupby("Date")["Count"].transform("sum")
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
        x="Date",
        y=y_value,
        color="Score",
        color_discrete_map=color_discrete_map,
    )

    fig.update_layout(
        template="plotly_white",
        yaxis=dict(ticksuffix=suffix),
    )

    return fig
