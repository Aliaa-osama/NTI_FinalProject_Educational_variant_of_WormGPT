# ============================================
# RAG over PDFs — LangChain (modern APIs)
# Requirements (install once):
#   pip install -U langchain langchain-google-genai langchain-huggingface langchain-chroma sentence-transformers pypdf
# ============================================

import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

# --------------------------
# Config
# --------------------------
google_api_key=os.getenv("GOOGLE_API_KEY") # Set this in your environment or .env
DOCS_DIR = "./documents_cleaned"  # Directory with your PDF files
CHROMA_DIR = "./chroma_db"
TOP_K = 4

if not google_api_key:
    raise RuntimeError("GOOGLE_API_KEY env var is not set.")

# --------------------------
# 1) Load & split documents
# --------------------------
loader = PyPDFDirectoryLoader(DOCS_DIR)
documents = loader.load()
if not documents:
    raise RuntimeError(f"No PDF files found in '{DOCS_DIR}'. Add PDFs and try again.")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_docs = text_splitter.split_documents(documents)

# --------------------------
# 2) Embeddings
# --------------------------
# Solid default sentence-embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# --------------------------
# 3) Vector store (Chroma)
#    NOTE: With langchain-chroma, persistence is automatic if you pass persist_directory=...
# --------------------------
# First run (build from docs):
vectordb = Chroma.from_documents(
    documents=split_docs,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
)

# If you run this script again later and want to reuse the existing DB instead of rebuilding:
# vectordb = Chroma(persist_directory=CHROMA_DIR, embedding=embeddings)

retriever = vectordb.as_retriever(search_kwargs={"k": TOP_K})

# --------------------------
# 4) LLM (Gemini with AI Studio key)
# --------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",     # You can also try "gemini-1.5-flash"
    google_api_key=google_api_key,       # <-- correct kwarg
    temperature=0.1,
)

# --------------------------
# 5) Prompt & Chains (modern)
# --------------------------
prompt = ChatPromptTemplate.from_template(
    "You are a helpful assistant specialized in cybersecurity.\n\n"
    "Use ONLY the provided context to answer concisely. "
    "If the answer is not in the context, say you don't know.\n\n"
    "Context:\n{context}\n\n"
    "Question: {input}\n\n"
    "Answer:"
)

# Combine retrieved docs via "stuff" strategy
document_chain = create_stuff_documents_chain(llm, prompt)

# Full retrieval chain: retrieve -> stuff -> LLM
rag_chain = create_retrieval_chain(retriever, document_chain)

# --------------------------
# 6) Ask a question
# --------------------------
query = "now i have a server and i wanna to scan the opend ports how this can be done?"
result = rag_chain.invoke({"input": query})

print("\n=== Answer ===")
print(result.get("answer", ""))

print("\n=== Sources ===")
for i, doc in enumerate(result.get("context", []), 1):
    src = doc.metadata.get("source", "Unknown source")
    page = doc.metadata.get("page", "N/A")
    print(f"[{i}] {src} (page {page})")
