from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import aiofiles
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
from docx import Document as DocxDocument
import io
import tiktoken
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ChromaDB client for vector storage
chroma_client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    allow_reset=True
))
collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# OPENAI_API_KEY
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Models
class DocumentModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    file_size: int
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "processing"

class DocumentCreate(BaseModel):
    filename: str
    file_type: str
    file_size: int

class Conversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: str  # user or assistant
    content: str
    sources: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    conversation_id: str
    message: str

class ChatResponse(BaseModel):
    message: Message
    sources: List[dict]

# Helper functions
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with overlap"""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF file"""
    reader = PdfReader(io.BytesIO(content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file"""
    doc = DocxDocument(io.BytesIO(content))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_txt(content: bytes) -> str:
    """Extract text from TXT/MD file"""
    return content.decode('utf-8', errors='ignore')

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings using chromadb's default embedding function"""
    # ChromaDB has built-in embedding - we use document IDs for retrieval
    return [[0.0] * 384] * len(texts)  # Placeholder, chromadb handles internally

# Document endpoints
@api_router.post("/documents/upload", response_model=DocumentModel)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    # Validate file type
    allowed_types = {'.pdf', '.txt', '.md', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported. Allowed: {allowed_types}")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Extract text based on file type
    if file_ext == '.pdf':
        text = extract_text_from_pdf(content)
    elif file_ext == '.docx':
        text = extract_text_from_docx(content)
    else:
        text = extract_text_from_txt(content)
    
    # Create document record
    doc_id = str(uuid.uuid4())
    document = DocumentModel(
        id=doc_id,
        filename=file.filename,
        file_type=file_ext,
        file_size=file_size,
        status="processing"
    )
    
    # Chunk the text
    chunks = chunk_text(text)
    document.chunk_count = len(chunks)
    
    if chunks:
        # Add to ChromaDB with metadata
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": doc_id, "filename": file.filename, "chunk_index": i} for i in range(len(chunks))]
        
        collection.add(
            ids=chunk_ids,
            documents=chunks,
            metadatas=metadatas
        )
    
    document.status = "ready"
    
    # Save to MongoDB
    doc_dict = document.model_dump()
    doc_dict['created_at'] = doc_dict['created_at'].isoformat()
    await db.documents.insert_one(doc_dict)
    
    return document

@api_router.get("/documents", response_model=List[DocumentModel])
async def get_documents():
    """Get all documents"""
    documents = await db.documents.find({}, {"_id": 0}).to_list(1000)
    for doc in documents:
        if isinstance(doc['created_at'], str):
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
    return documents

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its chunks"""
    # Delete from MongoDB
    result = await db.documents.delete_one({"id": doc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete chunks from ChromaDB
    try:
        # Get all chunks for this document
        results = collection.get(where={"document_id": doc_id})
        if results['ids']:
            collection.delete(ids=results['ids'])
    except Exception as e:
        logging.error(f"Error deleting chunks from ChromaDB: {e}")
    
    return {"message": "Document deleted"}



# Conversation endpoints
@api_router.post("/conversations", response_model=Conversation)
async def create_conversation():
    """Create a new conversation"""
    conversation = Conversation()
    conv_dict = conversation.model_dump()
    conv_dict['created_at'] = conv_dict['created_at'].isoformat()
    conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
    await db.conversations.insert_one(conv_dict)
    return conversation

@api_router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    """Get all conversations"""
    conversations = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    for conv in conversations:
        if isinstance(conv['created_at'], str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv['updated_at'], str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
    return conversations

@api_router.get("/conversations/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: str):
    """Get a single conversation"""
    conv = await db.conversations.find_one({"id": conv_id}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if isinstance(conv['created_at'], str):
        conv['created_at'] = datetime.fromisoformat(conv['created_at'])
    if isinstance(conv['updated_at'], str):
        conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
    return conv

@api_router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation and its messages"""
    result = await db.conversations.delete_one({"id": conv_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.messages.delete_many({"conversation_id": conv_id})
    return {"message": "Conversation deleted"}

@api_router.get("/conversations/{conv_id}/messages", response_model=List[Message])
async def get_messages(conv_id: str):
    """Get messages for a conversation"""
    messages = await db.messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    for msg in messages:
        if isinstance(msg['created_at'], str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    return messages

# Chat endpoint with RAG
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get AI response with RAG"""
    # Save user message
    user_message = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message
    )
    user_msg_dict = user_message.model_dump()
    user_msg_dict['created_at'] = user_msg_dict['created_at'].isoformat()
    await db.messages.insert_one(user_msg_dict)
    
    # Search for relevant chunks
    sources = []
    context = ""
    
    try:
        results = collection.query(
            query_texts=[request.message],
            n_results=5
        )
        
        if results['documents'] and results['documents'][0]:
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                sources.append({
                    "content": doc[:300] + "..." if len(doc) > 300 else doc,
                    "filename": metadata.get('filename', 'Unknown'),
                    "chunk_index": metadata.get('chunk_index', 0)
                })
                context += f"\n[Source {i+1} - {metadata.get('filename', 'Unknown')}]:\n{doc}\n"
    except Exception as e:
        logging.error(f"Error querying ChromaDB: {e}")
    
    # Generate response with LLM
    system_prompt = """You are a knowledgeable assistant that helps users understand their documents. 
When answering questions:
1. Use the provided context from the knowledge base to answer
2. If the context contains relevant information, cite the source by mentioning which document it came from
3. If no relevant context is found, acknowledge that and provide a general response
4. Be concise but thorough in your explanations
5. Format your response clearly with proper paragraphs"""

    user_prompt = f"""Context from knowledge base:
{context if context else "No relevant documents found in the knowledge base."}

User question: {request.message}

Please provide a helpful response based on the context above. If you reference information from the documents, mention which source it came from."""
   #model="gpt-4.1-mini"
    try:
        chat_instance = ChatOpenAI(
        model="gpt-4.1-mini",   # or gpt-4.1
        api_key=OPENAI_API_KEY,
        temperature=0.7
         )

        messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
         ]

        response = await chat_instance.ainvoke(messages)
        response_text = response.content

    except Exception as e:
        logging.error(f"Error calling LLM: {e}")
        response_text = (
        "I apologize, but I encountered an error processing your request. "
        f"Please try again. Error: {str(e)}"
        )

    
    # Save assistant message
    assistant_message = Message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=response_text,
        sources=sources
    )
    assistant_msg_dict = assistant_message.model_dump()
    assistant_msg_dict['created_at'] = assistant_msg_dict['created_at'].isoformat()
    await db.messages.insert_one(assistant_msg_dict)
    
    # Update conversation title if first message
    messages_count = await db.messages.count_documents({"conversation_id": request.conversation_id})
    if messages_count == 2:  # First user + first assistant message
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        await db.conversations.update_one(
            {"id": request.conversation_id},
            {"$set": {"title": title, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.conversations.update_one(
            {"id": request.conversation_id},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return ChatResponse(message=assistant_message, sources=sources)

# Status endpoint
@api_router.get("/")
async def root():
    return {"message": "Knowledge Assistant API", "status": "running"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
