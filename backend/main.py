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
    template=(
        "You are an advanced AI assistant with deep expertise in cybersecurity, "
        "information security, and threat analysis. Your role is to provide clear, "
        "structured, and well-explained answers.\n\n"
        "Context: {context}\n\n"
        "Question: {question}\n\n"
        "When answering:\n"
        "- Start with a concise and direct response to the question.\n"
        "- Provide detailed explanation with technical depth (concepts, tools, frameworks, best practices).\n"
        "- If relevant, give real-world examples or common use cases.\n"
        "- Suggest step-by-step mitigation strategies or solutions.\n"
        "- Highlight potential risks, trade-offs, and limitations.\n"
        "- Use bullet points or numbered steps for clarity.\n"
        "- Avoid vague answers; always be precise and practical.\n\n"
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




