import logging
import datetime
import openai
import os
from typing import Mapping, Any

from langchain import HuggingFaceHub
from langchain import PromptTemplate, LLMChain
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain

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
        self.falcon = "tiiuae/falcon-7b-instruct"
        self.llm = HuggingFaceHub(
            repo_id=self.falcon,
            model_kwargs={
                "temperature": self.temp,
                "max_new_tokens": 2000,
                "max_length": 512,
            },
        )

    def create_semantic_txt(self) -> TextLoader:
        LOGGER.info(" Loading data to docs folder for training... ")
        data = self.load_data()

        dataset = (
            data[
                (data[self.DATE] > datetime.date(year=2023, month=1, day=1))
                & (data.Title.str.contains("insuranceinsider"))
            ]
            .reset_index(drop=True)[[self.SUMMARY]]
            .head(1000)
        )

        dataset.to_csv("./docs/training.txt", index=False)

        documents = TextLoader("./docs/training.txt").load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
        docs = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings()
        db = FAISS.from_documents(docs, embeddings)

        return db.as_retriever()

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
        The assistant uses their insurance knowledge to anwser the question.
        Question: {question}\n\nAnswer: Provide technical information.
        """
        prompt = PromptTemplate(template=template, input_variables=["question"])
        llm_chain = LLMChain(prompt=prompt, llm=self.llm)
        return llm_chain.run(question)

    def falcon_with_articles(self, query: str) -> str:
        if not os.path.isfile("./docs/training.txt"):
            self.create_semantic_txt()

        loader = TextLoader("./docs/training.txt")
        pages = loader.load_and_split()

        # Chunk each page into sections
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=10, length_function=len
        )

        # Create FAISS index
        sections = text_splitter.split_documents(pages)
        faiss_index = FAISS.from_documents(sections, HuggingFaceEmbeddings())
        retriever = faiss_index.as_retriever()
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True, output_key="answer"
        )

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, retriever=retriever, memory=memory
        )

        return chain.run(question=query)
