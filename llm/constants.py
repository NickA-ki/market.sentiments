# Constants
EMB_OPENAI_ADA = "text-embedding-ada-002"
EMB_INSTRUCTOR_XL = "hkunlp/instructor-xl"
EMB_SBERT_MPNET_BASE = "sentence-transformers/all-mpnet-base-v2"  # Chroma takes care if embeddings are None
EMB_SBERT_MINILM = (
    "sentence-transformers/all-MiniLM-L6-v2"  # Chroma takes care if embeddings are None
)

LLM_OPENAI_GPT35: str = "gpt-3.5-turbo"
LLM_FLAN_T5_XXL: str = "google/flan-t5-xxl"
LLM_FLAN_T5_XL: str = "google/flan-t5-xl"
LLM_FASTCHAT_T5_XL: str = "lmsys/fastchat-t5-3b-v1.0"
LLM_FLAN_T5_SMALL: str = "google/flan-t5-small"
LLM_FLAN_T5_BASE: str = "google/flan-t5-base"
LLM_FLAN_T5_LARGE: str = "google/flan-t5-large"
LLM_FALCON_SMALL: str = "tiiuae/falcon-7b-instruct"
LLM_GPT4ALL: str = "./ggml-gpt4all-j-v1.3-groovy.bin"
