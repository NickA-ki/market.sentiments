import logging
import datetime
import openai
import os
from typing import Mapping, Any

from langchain import HuggingFaceHub
from langchain import PromptTemplate, LLMChain

from data.source import DataSource, DataSchema
from config import config


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LLMIns(DataSource, DataSchema):
    def __init__(self, temperature: float = 0.3) -> None:
        super().__init__()
        self.temp = temperature
        openai.api_key = config.OPENAI_API
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = config.HF_API
        self.model = "gpt-3.5-turbo"
        self.falcon = "tiiuae/falcon-40b-instruct"
        self.llm = HuggingFaceHub(
            repo_id=self.falcon,
            model_kwargs={"temperature": self.temp, "max_new_tokens": 2000},
        )

    def create_training_docs(self) -> None:
        LOGGER.info(" Loading data to docs folder for training... ")
        data = self.load_data()

        dataset = data[
            data[self.DATE] > datetime.date(year=2021, month=1, day=1)
        ].reset_index(drop=True)[[self.SUMMARY]]

        dataset.to_csv("./docs/training.csv")

    def gpt_generate(self, input: str) -> str:
        system_msg = "You are a helpful assistant who understands insurance."
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": input},
            ],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=self.temp,
        )

        return response.choices[0].text

    def falcon_generate(self, question: str) -> str:
        template = """
        You are an artificial intelligence assistant who understands insurance.
        The assitant gives market insight updates to the user's question.
        Question: {question}\n\nAnswer: Let's think step by step.
        """
        prompt = PromptTemplate(template=template, input_variables=["question"])
        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        return llm_chain.run(question)
