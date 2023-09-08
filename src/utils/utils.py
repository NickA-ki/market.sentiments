from plotly.graph_objects import Figure
import numpy as np
import base64
import streamlit as st
from typing import Callable, List


class Utils:
    def __init__(self) -> None:
        self.card_style = (
            {
                "card": {
                    "height": "150px",
                    "width": "175px",
                    "border-radius": "40px",
                    "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                    "background-color": "lightgrey",
                    "padding": "0px",
                    "margin": "10px",
                },
            },
        )
        self.hide_bar = """
            <style>
            [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
                visibility:hidden;
                width: 0px;
            }
            [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
                visibility:hidden;
            }
            </style>
        """

    def highlight_column(self, val: float, greater_than: float):
        color = "#FF3333" if val >= greater_than else "#33ff99"
        return f"background-color: {color}"

    def vectorize(self, f: Callable, *args) -> List[float]:
        return np.vectorize(f)(*args)

    def figure_layout(self, fig: Figure) -> Figure:
        fig = fig.update_layout(template="plotly_white")
        return fig

    def weighted_mean(self, x: np.array, weights: np.array) -> int:
        try:
            return np.average(x, weights=weights)
        except ZeroDivisionError:
            return 0

    def display_pdf(self, file) -> None:
        # Opening file from file path
        with open(file, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")

        # Embedding PDF in HTML
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'

        # Displaying File
        st.markdown(pdf_display, unsafe_allow_html=True)

    def page_title(self, title: str, n: int = 0) -> None:
        st.set_page_config(
            page_title="Market Dashboard",
            page_icon="🔖",
            layout="wide",
        )
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
