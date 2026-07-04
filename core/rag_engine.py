import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

RAG_PROMPT = """You are an expert video/meeting assistant. Answer the user's question 
based on the transcript context provided below.

Instructions:
- If the answer is clearly in the context, answer it directly and concisely.
- If the answer is not directly stated but can be inferred from the context, infer it and mention that.
- If the answer is truly not in the context, say: "I could not find this information in the transcript."
- If quoting someone, mention it clearly.
- Always be helpful and try your best to answer from the context.

Context from transcript:
{context}"""

def build_rag_chain(transcript: str):

    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=6)  # k=4 se k=6 kiya — zyada context
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_PROMPT),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def load_rag_chain():
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store)  # typo fix: retriver -> retriever
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_PROMPT),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str) -> str:
    print(f"Question : {question}")
    answer = rag_chain.invoke(question)
    print(f"answer :{answer}")
    return answer