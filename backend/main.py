from langchain_community.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# ------------------------
#  SecureBERT+ Embeddings
# ------------------------
emb_model = HuggingFaceEmbeddings(model_name="ehsanaghaei/SecureBERT_Plus")

vectordb = Chroma(persist_directory="./chroma_db", embedding_function=emb_model)

retriever = vectordb.as_retriever(search_kwargs={"k": 4})



llm = HuggingFaceHub(
    repo_id="meta-llama/Llama-2-7b-chat-hf",   
    model_kwargs={"temperature": 0.1, "max_length": 512},
    huggingfacehub_api_token="HF_API_TOKEN_HERE"  
)


prompt = PromptTemplate(
    template="You are a helpful assistant specialized in cybersecurity.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:",
    input_variables=["context", "question"]
)


qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True
)


