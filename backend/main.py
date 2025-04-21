import json
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate


def load_jsonl(file_path):
    """
    Loads documents from a JSONL file into a list of dictionaries.

    Each line in the JSONL file should contain a JSON object with at least 'content' and 'url' fields. This function extracts these fields into a simplified structure for further processing.

    Args:
        file_path (str): Path to the JSONL file containing the documents.
    Returns:
        list: A list of dictionaries, each containing 'content' and 'url' keys.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If a line contains invalid JSON.
    """
    docs = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            docs.append({"content": entry["content"], "url": entry["url"]})

    return docs


def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
    """
    Splits document content into smaller, overlapping chunks while preserving source URL.

    This function uses recursive character splitting to break down long documents into smaller chunks suitable for embedding and retrieval. The URL of each original document is preserved as metadata for each chunk to maintain provenance.

    Args:
        docs (list): List of dictionaries, each containing 'content' and 'url' keys.
        chunk_size (int, optional): Maximum size of each chunk in characters. Defaults to 1000.
        chunk_overlap (int, optional): Number of overlapping characters between adjacent chunks.
                                       Defaults to 200.

    Returns:
        tuple: A tuple containing:
            - chunks (list): List of text chunks.
            - metadatas (list): List of metadata dictionaries with 'url' keys
              corresponding to each chunk.

    Note:
        The overlap helps maintain context across chunk boundaries.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    chunks = []
    metadatas = []

    for doc in docs:
        # Split the document content into chunks
        doc_chunks = text_splitter.split_text(doc["content"])
        chunks.extend(doc_chunks)

        # Create metadata for each chunk, preserving the source URL
        metadatas.extend([{"url": doc["url"]}] * len(doc_chunks))

    return chunks, metadatas


def train_rag_model(documents_file):
    """
    Creates a RAG (Retrieval-Augmented Generation) chain from a JSONL document file.

    This function performs the following steps:
    1. Loads documents from a JSONL file
    2. Chunks the documents into smaller pieces
    3. Creates embeddings for each chunk
    4. Builds a vector store for similarity search
    5. Sets up a retrieval chain with an LLM for query answering

    Args:
        documents_file (str): Path to the JSONL file containing documents.

    Returns:
        langchain.chains.RetrievalChain: A chain that can retrieve relevant
                                         document chunks and generate answers.

    Note:
        Requires environment variables for API keys (loaded from .env file).
    """
    # Load environment variables from .env (typically contains API keys)
    load_dotenv()

    # Load and chunk documents
    docs = load_jsonl(documents_file)
    chunks, metadatas = chunk_documents(docs)

    # Create embeddings (Using Hugging Face to avoid OpenAI costs)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Convert text chunks into vector store, preserving metadata
    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=metadatas)

    # Create a retriever that will return the top 3 most relevant chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # Define the prompt template for the LLM to answer based on the retrieved documents
    prompt = PromptTemplate.from_template(
        "Given the following documents, answer the question:\n\n{context}\n\nQuestion: {input}"
    )

    # Use GPT-4 for synthesizing answers from retrieved documents
    llm = ChatOpenAI(model_name="gpt-4o")

    # Create a document combination chain that processes the retrieved documents
    combine_documents_chain = create_stuff_documents_chain(llm, prompt)

    # Create the RAG retrieval chain
    rag_chain = create_retrieval_chain(retriever, combine_documents_chain)
    return rag_chain


def ask_query(rag_chain, query):
    """
    Queries the RAG chain with a user query and returns the generated answer.

    This function passes the user query to the RAG chain, which retrieves
    relevant document chunks and generates an answer using the LLM.

    Args:
        rag_chain (langchain.chains.RetrievalChain): The RAG chain to query.
        query (str): The user's query.

    Returns:
        str: The generated answer based on retrieved documents.
    """
    # Invoke the chain with the user query
    response = rag_chain.invoke({"input": query})

    # Extract and return the answer portion of the response
    return response["answer"]


if __name__ == "__main__":
    # Initialize the RAG model with documents from data.jsonl
    rag_chain = train_rag_model("data.jsonl")

    # Example Query:
    # answer = ask_query(rag_chain, "how to contact the open source office?")
    # print(answer)

    # Continously ask for user input
    while True:
        query = input("Enter your query (or type 'exit' to quit): ")
        # Allow the user to exit the loop
        if query.strip().lower() == "exit":
            break
        answer = ask_query(rag_chain, query)
        print(answer)
