"""
services/llm_service.py
-----------------------
LLM wrapper for Google Gemini using LangChain.
"""

from typing import List
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import Config
from utils.token_counter import count_tokens, usage_tracker
from utils.logger import get_logger

logger = get_logger(__name__)

_llm_instance = None


SYSTEM_PROMPT = """
You are an Enterprise Document Intelligence Assistant.

Rules:
1. Answer ONLY from the provided context.
2. Never invent information.
3. If the answer is not contained in the context, reply exactly:
"I don't know based on the provided documents."
4. Cite the relevant context using [1], [2], etc.
5. Be concise, professional, and accurate.
"""


USER_TEMPLATE = """
Conversation History:
{history}

Context:
{context}

Citation List:
{citation_list}

Question:
{question}

Answer:
"""


# --------------------------------------------------------
# LLM
# --------------------------------------------------------

def get_llm():

    global _llm_instance

    if _llm_instance is None:
        if not Config.GOOGLE_API_KEY or Config.GOOGLE_API_KEY == "your_google_api_key_here":
            raise RuntimeError(
                "GOOGLE_API_KEY is missing. Add a Gemini API key from Google AI Studio to .env."
            )

        logger.info("Loading Gemini model: %s", Config.GEMINI_MODEL)
        _llm_instance = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.2,
            max_output_tokens=1024,
        )

    return _llm_instance


# --------------------------------------------------------
# Context Builder
# --------------------------------------------------------

def build_context_block(retrieved_chunks: List[dict]):

    parts = []

    for i, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):
        parts.append(
            f"[{i}] {chunk['text']}"
        )

    return "\n\n".join(parts)


# --------------------------------------------------------
# Question Answering
# --------------------------------------------------------

def generate_answer(
    question,
    history,
    context,
    citation_list
):

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_TEMPLATE)
        ]
    )

    chain = prompt | llm

    prompt_text = SYSTEM_PROMPT + USER_TEMPLATE.format(
        history=history,
        context=context,
        citation_list=citation_list,
        question=question
    )

    input_tokens = count_tokens(
        prompt_text
    )

    response = chain.invoke(
        {
            "history": history or "None",
            "context": context,
            "citation_list": citation_list,
            "question": question,
        }
    )

    answer = (
        response.content
        if hasattr(response, "content")
        else str(response)
    )

    output_tokens = count_tokens(answer)

    usage_tracker.record(
        input_tokens,
        output_tokens
    )

    return {
        "answer": answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


# --------------------------------------------------------
# Summary
# --------------------------------------------------------

def generate_document_summary(
    document_text
):

    llm = get_llm()

    response = llm.invoke(
        [
            (
                "system",
                "Summarize the document in 3-5 concise sentences."
            ),
            (
                "human",
                document_text[:8000]
            )
        ]
    )

    return (
        response.content
        if hasattr(response, "content")
        else str(response)
    )


# --------------------------------------------------------
# Suggested Questions
# --------------------------------------------------------

def generate_suggested_questions(
    document_text,
    n=3
):

    llm = get_llm()

    response = llm.invoke(
        [
            (
                "system",
                f"Generate exactly {n} questions about the document. "
                "Return only a numbered list."
            ),
            (
                "human",
                document_text[:6000]
            )
        ]
    )

    text = (
        response.content
        if hasattr(response, "content")
        else str(response)
    )

    questions = []

    for line in text.split("\n"):

        line = line.strip()

        if line:

            line = re.sub(
                r"^\d+[\.\)]\s*",
                "",
                line
            )

            questions.append(line)

    return questions[:n]