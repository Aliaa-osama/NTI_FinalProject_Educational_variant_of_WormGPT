# from langchain_community.llms import HuggingFaceHub
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
# from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.document_loaders import PyPDFDirectoryLoader
# from langchain_community.vectorstores import Chroma
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# #------------------------
# # Load documents from a directory and creating chunks
# #------------------------
# loader = PyPDFDirectoryLoader("./documents")
# documents = loader.load()

# if not documents:
#     print({"status": "No PDF files found in the folder."})

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# split_docs = text_splitter.split_documents(documents)
# print(split_docs[:2])  # Print first two chunks for verification
# # ------------------------
# #  SecureBERT+ Embeddings
# # ------------------------
# emb_model = HuggingFaceEmbeddings(model_name="ehsanaghaei/SecureBERT_Plus")

# vectordb = Chroma(persist_directory="./chroma_db", embedding_function=emb_model,documents=split_docs)

# retriever = vectordb.as_retriever(search_kwargs={"k": 4})



# llm = HuggingFaceHub(
#     repo_id="meta-llama/Llama-2-7b-chat-hf",   
#     model_kwargs={"temperature": 0.1, "max_length": 512},
#     huggingfacehub_api_token="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"  
# )


# prompt = PromptTemplate(
#     template=(
#         "You are a helpful assistant specialized in cybersecurity.\n\n"
#         "Use the context to answer concisely.\n\n"
#         "Context:\n{context}\n\n"
#         "Question: {question}\n\n"
#         "Answer:"
#     ),
#     input_variables=["context", "question"]
# )


# qa = RetrievalQA.from_chain_type(
#     llm=llm,
#     retriever=retriever,
#     chain_type="stuff",
#     chain_type_kwargs={"prompt": prompt},
#     return_source_documents=True
# )

# query = "What are the latest techniques in network intrusion detection?"
# result = qa({"query": query})

# print("Answer:", result["result"])
# print("Sources:", result["source_documents"])


from langchain_community.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# 1) Load & split docs
loader = PyPDFDirectoryLoader("./documents")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_docs = text_splitter.split_documents(documents)
print(f"Loaded {len(documents)} docs -> {len(split_docs)} chunks")

# 2) Embeddings (start with a known-good model)
emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3) Vector store (correct API)
vectordb = Chroma.from_documents(
    documents=split_docs,
    embedding=emb_model,                 # if error, try: embedding_function=emb_model
    persist_directory="./chroma_db"
)
retriever = vectordb.as_retriever(search_kwargs={"k": 4})

# 4) LLM (use a public model for the first run)
# Set your token in env (PowerShell):  $env:HUGGINGFACEHUB_API_TOKEN="hf_xxx"
llm = HuggingFaceHub(
    repo_id="google/flan-t5-large",
    model_kwargs={"temperature": 0.1, "max_new_tokens": 512}
)

# 5) Prompt + QA
prompt = PromptTemplate(
    template=(
        "You are a helpful assistant specialized in cybersecurity.\n\n"
        "Use the provided context to answer concisely.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
    input_variables=["context", "question"]
)


qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True
)

# 6) Test query
query = "What are the latest techniques in network intrusion detection?"
resp = qa({"query": query})  # if you get a key error, try qa.invoke({"query": query})

print("\nANSWER:\n", resp["result"])
print("\nSOURCES:")
for i, d in enumerate(resp["source_documents"], 1):
    print(f"[{i}] {d.metadata.get('source', d.metadata.get('file_path', 'unknown'))}")



