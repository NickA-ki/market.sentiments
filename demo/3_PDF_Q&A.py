import streamlit as st
from llm.pdf_qa import PdfQA
from pathlib import Path
from tempfile import NamedTemporaryFile
import time
import shutil
from llm.constants import *
from src.utils.utils import utils
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header


utils.page_title("Q&A Bot for PDF")


if "pdf_qa_model" not in st.session_state:
    st.session_state["pdf_qa_model"]: PdfQA = PdfQA()  ## Intialisation


## To cache resource across multiple session
@st.cache_resource
def load_llm(llm, load_in_8bit):
    if llm == LLM_OPENAI_GPT35:
        pass
    elif llm == LLM_FLAN_T5_SMALL:
        return PdfQA.create_flan_t5_small(load_in_8bit)
    elif llm == LLM_FLAN_T5_BASE:
        return PdfQA.create_flan_t5_base(load_in_8bit)
    elif llm == LLM_FLAN_T5_LARGE:
        return PdfQA.create_flan_t5_large(load_in_8bit)
    elif llm == LLM_FASTCHAT_T5_XL:
        return PdfQA.create_fastchat_t5_xl(load_in_8bit)
    elif llm == LLM_FALCON_SMALL:
        return PdfQA.create_falcon_instruct_small(load_in_8bit)
    else:
        raise ValueError("Invalid LLM setting")


## To cache resource across multiple session
@st.cache_resource
def load_emb(emb):
    if emb == EMB_INSTRUCTOR_XL:
        return PdfQA.create_instructor_xl()
    elif emb == EMB_SBERT_MPNET_BASE:
        return PdfQA.create_sbert_mpnet()
    elif emb == EMB_SBERT_MINILM:
        pass  ##ChromaDB takes care
    else:
        raise ValueError("Invalid embedding setting")


with st.sidebar:
    emb = st.radio(
        "**Select Embedding Model**",
        [EMB_INSTRUCTOR_XL, EMB_SBERT_MPNET_BASE, EMB_SBERT_MINILM],
        index=1,
    )
    llm = st.radio(
        "**Select LLM Model**",
        [
            LLM_FASTCHAT_T5_XL,
            LLM_FLAN_T5_SMALL,
            LLM_FLAN_T5_BASE,
            LLM_FLAN_T5_LARGE,
            LLM_FLAN_T5_XL,
            LLM_FALCON_SMALL,
        ],
        index=2,
    )
    load_in_8bit = st.radio("**Load 8 bit**", [True, False], index=1)
    pdf_file = st.file_uploader("**Upload PDF**", type="pdf")

    if st.button("Submit") and pdf_file is not None:
        with st.spinner(text="Uploading PDF and Generating Embeddings.."):
            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                shutil.copyfileobj(pdf_file, tmp)
                tmp_path = Path(tmp.name)
                st.session_state["pdf_qa_model"].config = {
                    "pdf_path": str(tmp_path),
                    "embedding": emb,
                    "llm": llm,
                    "load_in_8bit": load_in_8bit,
                }
                st.session_state["pdf_qa_model"].embedding = load_emb(emb)
                st.session_state["pdf_qa_model"].llm = load_llm(llm, load_in_8bit)
                st.session_state["pdf_qa_model"].init_embeddings()
                st.session_state["pdf_qa_model"].init_models()
                st.session_state["pdf_qa_model"].vector_db_pdf()
                st.sidebar.success("PDF uploaded successfully")

# question = st.text_input("Ask a question", "What is this document?")

if "generated" not in st.session_state:
    st.session_state["generated"] = [
        "I'm PDF Bot, Ask me questions about your uploaded file?"
    ]
## past stores User's questions
if "past" not in st.session_state:
    st.session_state["past"] = ["Hi!"]

# Layout of input/response containers
input_container = st.container()
colored_header(label="", description="", color_name="blue-30")
response_container = st.container()


# User input
## Function for taking user provided prompt as input
def get_text():
    input_text = st.text_input("You: ", "", key="input")
    return input_text


## Applying the user input box
with input_container:
    user_input = get_text()


def generate_response(prompt):
    try:
        st.session_state["pdf_qa_model"].retreival_qa_chain()
        answer = st.session_state["pdf_qa_model"].answer_query(prompt)
    except Exception as e:
        answer = f"Error answering the question: {str(e)}"
    return answer


with response_container:
    if user_input:
        response = generate_response(user_input)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(response)

    if st.session_state["generated"]:
        for i in range(len(st.session_state["generated"])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
            message(st.session_state["generated"][i], key=str(i))

# if st.button("Answer"):
#     try:
#         st.session_state["pdf_qa_model"].retreival_qa_chain()
#         answer = st.session_state["pdf_qa_model"].answer_query(question)
#         st.write(f"{answer}")
#     except Exception as e:
#         st.error(f"Error answering the question: {str(e)}")
