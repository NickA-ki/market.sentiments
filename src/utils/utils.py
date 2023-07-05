from plotly.graph_objects import Figure
import numpy as np
import streamlit as st


class Utils:
    def __init__(self) -> None:
        self.card_style = (
            {
                "card": {
                    "height": "150px",
                    "width": "150px",
                    "border-radius": "40px",
                    "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                    "background-color": "lightgrey",
                },
            },
        )

    def figure_layout(self, fig: Figure) -> Figure:
        fig = fig.update_layout(template="plotly_white")

        return fig

    def weighted_mean(self, x: np.array, weights: np.array) -> int:
        try:
            return np.average(x, weights=weights)
        except ZeroDivisionError:
            return 0

    def page_title(self, title: str) -> None:
        st.set_page_config(layout="wide")
        col1, col2 = st.columns([1, 8], gap="large")
        with col1:
            st.image(
                "assets/dr_nick.jpeg",
                width=100,
            )
        with col2:
            st.title(f"{title}")

        hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    def show_syndicate_name(self, syndicates: list, synd_dict: dict) -> None:
        if syndicates:
            for code in syndicates:
                st.sidebar.markdown(f"- {synd_dict[code]}")
                st.sidebar.markdown(
                    """
                <style>
                [data-testid="stMarkdownContainer"] ul{
                    list-style-position: inside;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )


utils = Utils()
