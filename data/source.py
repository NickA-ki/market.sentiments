import sqlite3
import logging
import pandas as pd
import streamlit as st

from datetime import date
from dataclasses import dataclass

logging.getLogger().setLevel(logging.INFO)


@dataclass
class DataSchema:
    DATE: str = "Date"
    SUMMARY: str = "Summary"
    TITLE: str = "Title"
    LINK: str = "Link"
    YMDATE: str = "YearMonth"
    SEARCH: str = "TextSearch"
    CODE: str = "SyndicateCode"
    AGENT: str = "ManagingAgent"


class DataSource:
    # @st.cache_data(ttl=5000)
    def load_data(self, table: str = "market_articles") -> pd.DataFrame:
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

        return self.tidy_data(pd.read_sql(query, conn))

    def load_lloyds(self) -> pd.DataFrame:
        lloyds = pd.read_csv("./data/lloyds.csv")
        lloyds = lloyds[(lloyds.ActiveSyndicateFlag == "Active")].reset_index(drop=True)

        return lloyds

    def lloyds_syndicate_dict(self) -> dict:
        lloyds = self.load_lloyds()
        df = (
            lloyds[[DataSchema.AGENT, DataSchema.CODE]]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        return dict(zip(df[DataSchema.CODE], df[DataSchema.AGENT]))

    def make_markdown(self, title: str, link: str) -> str:
        markdown = "[{}]({})".format(title, link)
        return markdown

    def date_formatter(self, date: date) -> str:
        if date.month < 10:
            new_date = str(date.year) + "-" + "0" + str(date.month)

        else:
            new_date = str(date.year) + "-" + str(date.month)

        return new_date

    def tidy_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values(DataSchema.DATE, ascending=False).reset_index(drop=True)
        df.rename(columns={"Description": DataSchema.SUMMARY}, inplace=True)
        df[DataSchema.DATE] = pd.to_datetime(df[DataSchema.DATE]).dt.date
        df[DataSchema.SEARCH] = (
            df[DataSchema.TITLE].str.lower() + df[DataSchema.SUMMARY].str.lower()
        )
        df[DataSchema.TITLE] = df.apply(
            lambda x: self.make_markdown(x.Title, x.Link), axis=1
        )
        df[DataSchema.YMDATE] = df[DataSchema.DATE].apply(self.date_formatter)
        try:
            df = df.drop([DataSchema.LINK, "neg", "pos", "neu"], axis=1)
        except:
            df = df.drop([DataSchema.LINK], axis=1)

        return df.dropna().reset_index(drop=True)


source = DataSource()
