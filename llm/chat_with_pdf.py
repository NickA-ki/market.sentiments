import platform
from langchain.llms import OpenAI
from langchain import HuggingFaceHub
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

"""
Reference repo: https://github.com/jnekrasov/chat-with-pdfs-demo/blob/main/chat-with-pdfs.py
"""


class bcolors:
    GREEN = "\033[92m"
    ENDCOLOR = "\033[0m"


# Load, convert to text and split pdf file into pages
loader = PyPDFLoader("llm/hiscox_2022.pdf")
pages = loader.load_and_split()

# Chunk each page into sections
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=100, length_function=len
)
sections = text_splitter.split_documents(pages)

# Create FAISS index
faiss_index = FAISS.from_documents(sections, HuggingFaceEmbeddings())

# Define chain
retriever = faiss_index.as_retriever()
memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True, output_key="answer"
)

llm = HuggingFaceHub(
    repo_id="tiiuae/falcon-7b-instruct",
    model_kwargs={
        "temperature": 0.1,
        "max_new_tokens": 2000,
        "max_length": 512,
    },
)
chain = ConversationalRetrievalChain.from_llm(
    llm=llm, retriever=retriever, memory=memory
)


# Collect user input and simulate chat with pdf
if platform.system() == "Windows":
    eof_key = "<Ctrl+Z>"
else:
    eof_key = "<Ctrl+D>"

print(
    f"Lets talk with Hiscox 2022 Report. What would you like to know? Or press {eof_key} to exit."
)
while True:
    try:
        user_input = input("Q:")
        print(
            f"{bcolors.GREEN} A: {chain({'question': user_input})['answer'].strip()}{bcolors.ENDCOLOR}"
        )
    except EOFError:
        break
    except KeyboardInterrupt:
        break

print("Bye!")


# print(chain({'question': 'What was Tesla total revenues and net income?'}))
# print(chain({'question': 'Sum these values?'}))
# print(chain({'question': 'What was the main risk factors for Tesla?'}))
