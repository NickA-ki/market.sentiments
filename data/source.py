import sqlite3
import logging
import pandas as pd
import streamlit as st

from datetime import date

logging.getLogger().setLevel(logging.INFO)


# @st.cache_data(ttl=5000)
def load_data(table: str = "market_articles") -> pd.DataFrame:
    """
    Function to extract data from sqlite db and produce a dataframe
    """
    logging.info("loading data")
    conn = sqlite3.connect("./data/Database.sqlite")

    query = f"""
    SELECT * FROM {table}
    ORDER BY Date DESC
    """
    logging.info("data loaded")

    return tidy_data(pd.read_sql(query, conn))


def make_markdown(title: str, link: str) -> str:
    markdown = "[{}]({})".format(title, link)
    return markdown


def date_formatter(date: date) -> str:
    if date.month < 10:
        new_date = str(date.year) + "-" + "0" + str(date.month)

    else:
        new_date = str(date.year) + "-" + str(date.month)

    return new_date


def tidy_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    df.rename(columns={"Description": "Summary"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["TextSearch"] = df.Title.str.lower() + df.Summary.str.lower()
    df["Title"] = df.apply(lambda x: make_markdown(x.Title, x.Link), axis=1)
    df["YearMonth"] = df["Date"].apply(date_formatter)
    try:
        df = df.drop(["Link", "neg", "pos", "neu"], axis=1)
    except:
        df = df.drop(["Link"], axis=1)

    return df.dropna().reset_index(drop=True)
