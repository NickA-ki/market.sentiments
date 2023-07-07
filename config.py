from pydantic import BaseSettings


class Config(BaseSettings):
    # HF API
    HF_API: str = "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"

    # OpenAI API
    OPENAI_API: str = "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"


config = Config()
