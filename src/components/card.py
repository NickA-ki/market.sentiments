from uuid import uuid4
from streamlit_elements import elements, mui
import urllib.parse
from data.links import links


def mui_card(title: str, content: str, date: str, link: str):
    link_dict = links[urllib.parse.urlparse(link).netloc]
    with elements(
        key=str(uuid4()),
    ):
        with mui.Card(
            sx={
                "display": "flex",
                "flexDirection": "column",
                "borderRadius": 3,
                "overflow": "hidden",
            },
            elevation=1,
        ):
            mui.CardHeader(
                title=title,
                subheader=str(date),
                avatar=mui.Avatar(
                    link_dict["name"],
                    sx={"bgcolor": link_dict["color"]},
                ),
            )

            with mui.CardContent(sx={"flex": 1}):
                mui.Typography(content + "...")

            with mui.CardActions(disableSpacing=True):
                mui.IconButton(mui.icon.Share, href=link, target="_blank")


def mui_kpi(kpi: str, name: str):
    background = "#FF3333"
    if kpi == "Positive":
        background = "#33ff99"
    with elements(
        key=str(uuid4()),
    ):
        with mui.Card(
            sx={
                "display": "flex",
                "flexDirection": "column",
                "borderRadius": 3,
                "overflow": "hidden",
                "borderStyle": "solid",
                "borderColor": background,
                # "color": "white",
            },
            elevation=1,
        ):
            mui.CardHeader(
                title=mui.Typography(kpi, sx={"fontSize": 32, "textAlign": "center"}),
                # avatar=mui.icon.Numbers,
            )

            with mui.CardContent(sx={"flex": 2}):
                mui.Typography(
                    name,
                    sx={"fontSize": 22, "textAlign": "center"},
                )
