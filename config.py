from pydantic import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    # ChatGPT API:
    CHAT_PDF_API: str = os.getenv("CHAT_PDF_API")

    # HF API
    HF_API: str = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    # OpenAI API
    OPENAI_API: str = os.getenv("OPENAI_API")


config = Config()
