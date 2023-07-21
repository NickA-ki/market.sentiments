from langchain.document_loaders import PDFPlumberLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import (
    CharacterTextSplitter,
    TokenTextSplitter,
    RecursiveCharacterTextSplitter,
)
from transformers import pipeline
from langchain import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain import HuggingFacePipeline
from langchain.embeddings import HuggingFaceInstructEmbeddings, HuggingFaceEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.llms import GPT4All
from llm.constants import *
from transformers import AutoTokenizer
from pdf2image import convert_from_path
from pathlib import Path
import torch
import os
import re


class PdfQA:
    def __init__(self, config: dict = {}):
        self.config = config
        self.embedding = None
        self.vectordb = None
        self.llm = None
        self.qa = None
        self.retriever = None

    # The following class methods are useful to create global GPU model instances
    # This way we don't need to reload models in an interactive app,
    # and the same model instance can be used across multiple user sessions
    @classmethod
    def create_instructor_xl(cls):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return HuggingFaceInstructEmbeddings(
            model_name=EMB_INSTRUCTOR_XL, model_kwargs={"device": device}
        )

    @classmethod
    def create_sbert_mpnet(cls):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return HuggingFaceEmbeddings(
            model_name=EMB_SBERT_MPNET_BASE, model_kwargs={"device": device}
        )

    @classmethod
    def create_sbert_minilm(cls):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return HuggingFaceEmbeddings(
            model_name=EMB_SBERT_MINILM, model_kwargs={"device": device}
        )

    @classmethod
    def create_flan_t5_xxl(cls, load_in_8bit=False):
        # Local flan-t5-xxl with 8-bit quantization for inference
        # Wrap it in HF pipeline for use with LangChain
        return pipeline(
            task="text2text-generation",
            model="google/flan-t5-xxl",
            max_new_tokens=200,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_flan_t5_xl(cls, load_in_8bit=False):
        return pipeline(
            task="text2text-generation",
            model="google/flan-t5-xl",
            max_new_tokens=200,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_flan_t5_small(cls, load_in_8bit=False):
        # Local flan-t5-small for inference
        # Wrap it in HF pipeline for use with LangChain
        model = "google/flan-t5-small"
        tokenizer = AutoTokenizer.from_pretrained(model)
        return pipeline(
            task="text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=100,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_flan_t5_base(cls, load_in_8bit=False):
        # Wrap it in HF pipeline for use with LangChain
        model = "google/flan-t5-base"
        tokenizer = AutoTokenizer.from_pretrained(model)
        return pipeline(
            task="text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=100,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_flan_t5_large(cls, load_in_8bit=False):
        # Wrap it in HF pipeline for use with LangChain
        model = "google/flan-t5-large"
        tokenizer = AutoTokenizer.from_pretrained(model)
        return pipeline(
            task="text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=100,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_fastchat_t5_xl(cls, load_in_8bit=False):
        return pipeline(
            task="text2text-generation",
            model="lmsys/fastchat-t5-3b-v1.0",
            max_new_tokens=100,
            model_kwargs={
                "device_map": "auto",
                "load_in_8bit": load_in_8bit,
                "max_length": 512,
                "temperature": 0.0,
            },
        )

    @classmethod
    def create_falcon_instruct_small(cls):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
        falcon_llm = HuggingFaceHub(
            repo_id="tiiuae/falcon-7b-instruct",
            task="text2text-generation",
            model_kwargs={
                "device_map": "auto",
                "temperature": 0.5,
                "max_new_tokens": 200,
                "max_length": 512,
            },
        )
        return falcon_llm

    @classmethod
    def create_gpt4all(cls):
        model_path = LLM_GPT4ALL
        return GPT4All(model=model_path, backend="gptj", verbose=False)

    def init_embeddings(self) -> None:
        # OpenAI ada embeddings API
        if self.config["embedding"] == EMB_OPENAI_ADA:
            self.embedding = OpenAIEmbeddings()
        elif self.config["embedding"] == EMB_INSTRUCTOR_XL:
            # Local INSTRUCTOR-XL embeddings
            if self.embedding is None:
                self.embedding = PdfQA.create_instructor_xl()
        elif self.config["embedding"] == EMB_SBERT_MPNET_BASE:
            ## this is for SBERT
            if self.embedding is None:
                self.embedding = PdfQA.create_sbert_mpnet()
        elif self.config["embedding"] == EMB_SBERT_MINILM:
            if self.embedding is None:
                self.embedding = PdfQA.create_sbert_minilm()
        else:
            self.embedding = None  ## DuckDb uses sbert embeddings
            # raise ValueError("Invalid config")

    def init_models(self) -> None:
        """Initialize LLM models based on config"""
        load_in_8bit = self.config.get("load_in_8bit", False)
        # OpenAI GPT 3.5 API
        if self.config["llm"] == LLM_OPENAI_GPT35:
            # OpenAI GPT 3.5 API
            pass
        elif self.config["llm"] == LLM_FLAN_T5_SMALL:
            if self.llm is None:
                self.llm = PdfQA.create_flan_t5_small(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FLAN_T5_BASE:
            if self.llm is None:
                self.llm = PdfQA.create_flan_t5_base(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FLAN_T5_LARGE:
            if self.llm is None:
                self.llm = PdfQA.create_flan_t5_large(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FLAN_T5_XL:
            if self.llm is None:
                self.llm = PdfQA.create_flan_t5_xl(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FLAN_T5_XXL:
            if self.llm is None:
                self.llm = PdfQA.create_flan_t5_xxl(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FASTCHAT_T5_XL:
            if self.llm is None:
                self.llm = PdfQA.create_fastchat_t5_xl(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_FALCON_SMALL:
            if self.llm is None:
                self.llm = PdfQA.create_falcon_instruct_small(load_in_8bit=load_in_8bit)
        elif self.config["llm"] == LLM_GPT4ALL:
            if self.llm is None:
                self.llm = PdfQA.create_gpt4all()

        else:
            raise ValueError("Invalid config")

    def vector_db_pdf(self, gpt4all: bool = True) -> None:
        """
        creates vector db for the embeddings and persists them or loads a vector db from the persist directory
        """
        pdf_path = self.config.get("pdf_path", None)
        persist_directory = self.config.get("persist_directory", None)
        if persist_directory and Path.exists(persist_directory):
            self.vectordb = Chroma(
                persist_directory=persist_directory, embedding_function=self.embedding
            )
        elif pdf_path and os.path.exists(pdf_path):
            if gpt4all:
                loader = DirectoryLoader(pdf_path, glob="*.pdf", loader_cls=PyPDFLoader)
                documents = loader.load_and_split()
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1024, chunk_overlap=64
                )
                texts = text_splitter.split_documents(documents)
            else:
                ## 1. Extract the documents
                loader = DirectoryLoader(pdf_path, glob="*.pdf", loader_cls=PyPDFLoader)
                documents = loader.load()
                ## 2. Split the texts
                text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
                texts = text_splitter.split_documents(documents)
                # text_splitter = TokenTextSplitter(chunk_size=100, chunk_overlap=10, encoding_name="cl100k_base")  # This the encoding for text-embedding-ada-002
                token_splitter = TokenTextSplitter(
                    chunk_size=100, chunk_overlap=10
                )  # This the encoding for text-embedding-ada-002
                texts = token_splitter.split_documents(texts)

            ## 3. Create Embeddings and add to chroma store
            ##TODO: Validate if self.embedding is not None
            self.vectordb = Chroma.from_documents(
                documents=texts,
                embedding=self.embedding,
                persist_directory=persist_directory,
            )
        else:
            raise ValueError("NO PDF found")

    def retreival_qa_chain(self):
        """
        Creates retrieval qa chain using vectordb as retrivar and LLM to complete the prompt
        """
        ##TODO: Use custom prompt
        self.retriever = self.vectordb.as_retriever(search_kwargs={"k": 3})

        if self.config["llm"] == LLM_OPENAI_GPT35:
            # Use ChatGPT API
            self.qa = RetrievalQA.from_chain_type(
                llm=OpenAI(model_name=LLM_OPENAI_GPT35, temperature=0.0),
                chain_type="stuff",
                retriever=self.vectordb.as_retriever(search_kwargs={"k": 3}),
            )
        elif self.config["llm"] == LLM_GPT4ALL:
            template = """
                    You are an artificial intelligence assistant who understands insurance.
                    Use the following pieces of context to answer the question at the end.
                    Extract numbers where appropriate to help answer questions.
                    If you don't know the answer, just say you don't know. DO NOT try to make up an answer.

                    {context}

                    Question: {question}
                    Helpful answer in markdown:
                    """
            prompt = PromptTemplate(
                template=template, input_variables=["context", "question"]
            )
            self.qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectordb.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True,
                # chain_type_kwargs={"prompt": prompt},
                verbose=False,
            )
        else:
            hf_llm = HuggingFacePipeline(pipeline=self.llm, model_id=self.config["llm"])

            self.qa = RetrievalQA.from_chain_type(
                llm=hf_llm, chain_type="stuff", retriever=self.retriever
            )
            if (
                self.config["llm"] == LLM_FLAN_T5_SMALL
                or self.config["llm"] == LLM_FLAN_T5_BASE
                or self.config["llm"] == LLM_FLAN_T5_LARGE
            ):
                question_t5_template = """
                context: {context}
                question: {question}
                answer: 
                """
                QUESTION_T5_PROMPT = PromptTemplate(
                    template=question_t5_template,
                    input_variables=["context", "question"],
                )
                self.qa.combine_documents_chain.llm_chain.prompt = QUESTION_T5_PROMPT
            self.qa.combine_documents_chain.verbose = True
            self.qa.return_source_documents = True

    def answer_query(self, question: str) -> str:
        """
        Answer the question
        """

        answer_dict = self.qa(
            {
                "query": question,
            }
        )
        # print(answer_dict)
        answer = answer_dict["result"]
        pages = []
        for ref in range(0, len(answer_dict["source_documents"])):
            pages.append(answer_dict["source_documents"][ref].metadata["page"] + 1)
        source_pdf = answer_dict["source_documents"][0].metadata["source"]
        # extract = self.extract_source(page_no)
        if self.config["llm"] == LLM_FASTCHAT_T5_XL:
            answer = self._clean_fastchat_t5_output(answer)
        return answer, pages, source_pdf

    def extract_source(self, page_no: int):
        pdf_path = self.config.get("pdf_path", None)
        images = convert_from_path(pdf_path, dpi=88)
        return images[page_no]

    def _clean_fastchat_t5_output(self, answer: str) -> str:
        # Remove <pad> tags, double spaces, trailing newline
        answer = re.sub(r"<pad>\s+", "", answer)
        answer = re.sub(r"  ", " ", answer)
        answer = re.sub(r"\n$", "", answer)
        return answer
