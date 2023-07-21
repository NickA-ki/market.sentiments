import streamlit as st
from llm.pdf_qa import PdfQA
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time
import os
import shutil
from llm.constants import *
from src.utils.utils import utils
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header

tmpdir = Path("../docs")

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
        return PdfQA.create_falcon_instruct_small()
    elif llm == LLM_GPT4ALL:
        return PdfQA.create_gpt4all()
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


load_in_8bit = False
# tmpdir = TemporaryDirectory()

if "submitted" not in st.session_state:
    st.session_state.submitted = True


def activate_text_input() -> None:
    st.session_state.submitted = False


with st.sidebar:
    pdf_file = st.file_uploader(
        "**Upload PDF**", type="pdf", accept_multiple_files=True
    )
    if not pdf_file:
        for filename in os.listdir(tmpdir):
            file_path = os.path.join(tmpdir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (file_path, e))

    if (
        st.button("Submit", key="submit_button", on_click=activate_text_input)
        and pdf_file is not None
    ):
        with st.spinner(text="Uploading PDF and Generating Embeddings.."):
            for file in pdf_file:
                uploaded_file_path = Path(tmpdir.name) / file.name
                with open(uploaded_file_path, "wb") as output_temporary_file:
                    output_temporary_file.write(file.read())

            st.session_state["pdf_qa_model"].config = {
                "pdf_path": tmpdir,
                "embedding": EMB_SBERT_MINILM,
                "llm": LLM_FLAN_T5_BASE,
                "load_in_8bit": load_in_8bit,
            }
            st.session_state["pdf_qa_model"].embedding = load_emb(EMB_SBERT_MINILM)
            st.session_state["pdf_qa_model"].llm = load_llm(
                LLM_FLAN_T5_BASE, load_in_8bit
            )
            st.session_state["pdf_qa_model"].init_embeddings()
            st.session_state["pdf_qa_model"].init_models()
            st.session_state["pdf_qa_model"].vector_db_pdf(gpt4all=True)
            st.sidebar.success("PDF uploaded successfully")

# question = st.text_input("Ask a question", "What is this document?")
## past stores User's questions
if "past" not in st.session_state:
    st.session_state["past"] = ["Hi!"]

if "generated" not in st.session_state:
    st.session_state["generated"] = [
        "I'm PDF Bot, Ask me questions about your uploaded file?"
    ]
    st.session_state["pdf_image"] = []
    st.session_state["pdf_source"] = None


# Set tabs ----
message_tab, pdf_tab = st.tabs(["Q&A", "PDF"])


# User input
## Function for taking user provided prompt as input
def get_text(active: bool):
    input_text = st.text_input("You: ", "", disabled=active, key="input")
    return input_text


def generate_response(prompt):
    try:
        st.session_state["pdf_qa_model"].retreival_qa_chain()
        answer = st.session_state["pdf_qa_model"].answer_query(prompt)
    except Exception as e:
        answer = f"Error answering the question: {str(e)}", None, None
    return answer


with message_tab:
    # Layout of input/response containers
    input_container = st.container()
    colored_header(label="", description="", color_name="blue-30")
    response_container = st.container()
    ## Applying the user input box
    with input_container:
        user_input = get_text(st.session_state.submitted)
        if st.session_state.submitted:
            st.warning("Please load and submit pdf files before asking questions...")
    with response_container:
        if user_input:
            response = generate_response(user_input)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(response[0])
            st.session_state.pdf_image.append(response[1])
            st.session_state.pdf_source = response[2]

        if st.session_state["generated"]:
            for i in range(len(st.session_state["generated"])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
                message(st.session_state["generated"][i], key=str(i))

with pdf_tab:
    if st.session_state["pdf_image"]:
        st.write(f"Anwser obtained from pages: {st.session_state['pdf_image'][-1]}")
        utils.display_pdf(st.session_state.pdf_source)
    else:
        st.warning("Please ask a question first!")
