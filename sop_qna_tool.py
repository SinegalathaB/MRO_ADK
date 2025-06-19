from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from vertexai import init
from langchain_core.output_parsers import StrOutputParser
from google.adk.agents import Agent
from read_env import *

# # Initialize Vertex AI
init(project="certain-mystery-305507", location="us-central1") 

def load_pdf_text(file_path):
    """
    Extracts all text from a PDF file.
    """
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """
    Splits long text into smaller overlapping chunks.
    """
    splitter = CharacterTextSplitter(separator="\n", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_parts_usage_tool(part_names: list[str]) -> list[dict]:
    """
    Given a list of part names, returns their usage from the SOP PDF.
    """
    # Load and chunk the text
    pdf_path = "SOP_Document/SOP_Document.pdf"
    text = load_pdf_text(pdf_path)
    doc_chunks = chunk_text(text)
    documents = [Document(page_content=chunk) for chunk in doc_chunks]

    # Create embedding model and vectorstore
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_documents(documents, embeddings)
    retriever = vector_store.as_retriever()

    # Define LLM and QA chain
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    prompt = ChatPromptTemplate.from_template(
        """Answer the question based only on the context provided.

Context:
{context}

Question:
{question}"""
    )
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Helper function
    def get_single_part_usage(part_name):
        query = f"""
You are an expert in industrial machinery and maintenance.
Based on the part name provided, determine the specific usage of that part in the machine.
If direct information about the part's usage is not available, analyze the part name and its likely role in the process to provide a generic but relevant usage.

Your response should be a concise, informative 2-3 line description.

Part Name: '{part_name}'

What is the usage of this part in the machine?
"""
        result = qa_chain.invoke(query)
        return result.strip() if result else None

    # Iterate and build response
    results = []
    for part_name in part_names:
        usage = get_single_part_usage(part_name)
        results.append({
            "part": part_name,
            "part_usage": usage if usage.lower() != "none" else None
        })
    print("******RESULTS: ",results)

    return results


part_usage_agent = Agent(
    model='gemini-2.0-flash',
    name='part_usage_agent',
    instruction="""
You are an agent specialized in retrieving the usage of parts used in machinery.
Use the tool to fetch usage of parts from SOP.
Return the result strictly in the following JSON array format:
[
  {
    "part": "<Part Name>",
    "part_usage": "<usage of the particular part>"
  },
  ...
]
""",
    description='This agent retrieves part usage information from the SOP document.',
    tools=[get_parts_usage_tool],
)
