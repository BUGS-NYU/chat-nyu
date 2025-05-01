import os
import json
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate

# Clears console
def clear_console() -> None:
    """Clear the terminal screen on macOS/Linux/Windows."""
    command = "cls" if os.name == "nt" else "clear"
    os.system(command)

# Disable tokenizer parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def load_jsonl(file_path):
    """
    Loads documents from a JSONL file.

    Each line in the file should contain a JSON object with 'content' and 'url' fields.

    Args:
        file_path (str): Path to the JSONL file.

    Returns:
        list[dict]: List of dictionaries with 'content' and 'url' keys.

    Raises:
        FileNotFoundError: If the specified file is not found.
        json.JSONDecodeError: If any line in the file contains invalid JSON.
    """
    docs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            docs.append(
                {
                    "content": entry["content"],
                    "url": entry["url"],
                }
            )
    return docs


def chunk_documents(docs, chunk_size=2000, chunk_overlap=200):
    """
    Splits document content into smaller, overlapping chunks while preserving source URL.

    Each resulting chunk retains metadata linking back to the source URL.

    Args:
        docs (list[dict]): List of documents with 'content' and 'url' keys.
        chunk_size (int, optional): Maximum characters per chunk. Defaults to 1000.
        chunk_overlap (int, optional): Number of overlapping characters between adjacent chunks. Defaults to 200.

    Returns:
        tuple:
            - chunks (list[str]): List of text chunks.
            - metadatas (list[dict]): Metadata for each chunk, including source URL.
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
    Initializes and returns a RAG (Retrieval-Augmented Generation) chain.

    Steps:
    1. Loads documents from a JSONL file.
    2. Chunks the documents into smaller pieces.
    3. Generates vector embeddings.
    4. Builds a vector store for similarity search.
    5. Sets up a retrieval chain with an LLM for query answering

    Args:
        documents_file (str): Path to the JSONL document file.

    Returns:
        RetrievalChain: A LangChain retrieval chain capable of answering queries.
    """
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
    # llm = ChatOpenAI(model_name="gpt-4o")
    # llm = ChatOpenAI(model_name="gpt-4.1")

    # Use Gemini 2.0 Flash for synthesizing answers from retrieved documents
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2  # adjust as needed
    )

    # Create a document combination chain that processes the retrieved documents
    combine_documents_chain = create_stuff_documents_chain(llm, prompt)

    # Create the RAG retrieval chain
    rag_chain = create_retrieval_chain(retriever, combine_documents_chain)
    return rag_chain


def ask_query(rag_chain, query):
    """
    Queries the RAG chain and returns the generated answer.

    Args:
        rag_chain (RetrievalChain): The configured RAG chain.
        query (str): The user query.

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
    # answer = ask_query(rag_chain, "which majors include computer science courses?")
    # print(answer)

    # Continuously ask for user input
    while True:
        query = input("Enter your query (or type 'exit' to quit): ")
        # Allow the user to exit the loop
        if query.strip().lower() == "exit":
            break
        # Clear console 
        if query == "cls":
            clear_console()
            continue
        answer = ask_query(rag_chain, query)
        print(answer)
