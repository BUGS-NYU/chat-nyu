import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate

def train_rag_model(documents_file):
    # Set up OpenAI API key if using GPT-4
    os.environ["OPENAI_API_KEY"] = "your_api_key"

    # Load the Paper
    with open(documents_file, "r", encoding="utf-8") as f:
        paper_text = f.read()

    # Chunking the Document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(paper_text)

    # Create embeddings (Using Hugging Face to avoid OpenAI costs)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Convert text chunks into vector store
    vector_store = FAISS.from_texts(chunks, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    prompt = PromptTemplate.from_template(
        "Given the following documents, answer the question:\n\n{context}\n\nQuestion: {input}"
    )

    # Use GPT-4 for synthesis
    llm = ChatOpenAI(model_name="gpt-4o")

    # Create a document combination chain
    combine_documents_chain = create_stuff_documents_chain(llm, prompt)

    # Create the RAG retrieval chain
    rag_chain = create_retrieval_chain(retriever, combine_documents_chain)
    return rag_chain

def ask_query(rag_chain, query):
    response = rag_chain.invoke({"input": query})
    return response["answer"]

if __name__ == "__main__":
    rag_chain = train_rag_model("backend/test_article.txt")

    # Example Query:
    # answer = ask_query(rag_chain, "how to contact the open source office?")
    # print(answer)

    # Continuously ask for user input
    while True:
        query = input("Enter your query (or type 'exit' to quit): ")
        # Allow the user to exit the loop
        if query.strip().lower() == "exit":
            break
        answer = ask_query(rag_chain, query)
        print(answer)