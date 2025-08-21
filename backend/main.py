"""
FastAPI main application for Cybersecurity RAG Chatbot
Provides API endpoints for chat, document management, and system health
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Import our custom modules
from backend.vector_db import VectorDBConfig, check_database_health
from backend.rag_service import CybersecurityRAG
from backend.document_loader import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for services_hi
rag_service: Optional[CybersecurityRAG] = None
doc_processor: Optional[DocumentProcessor] = None
db_config: Optional[VectorDBConfig] = None
embedding_model = None  # Global embedding model

# Pydantic models for API requests/responses
class ChatMessage(BaseModel):
    message: str = Field(..., description="User's question or message")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation tracking")
    include_sources: bool = Field(default=True, description="Whether to include source documents")
    max_sources: int = Field(default=3, description="Maximum number of source documents to return")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")
    sources: List[Dict[str, Any]] = Field(default=[], description="Source documents used")
    session_id: str = Field(..., description="Session ID")
    response_time: float = Field(..., description="Response time in seconds")
    timestamp: str = Field(..., description="Response timestamp")

class DocumentUpload(BaseModel):
    filename: str
    content: str
    document_type: str = "text"
    metadata: Dict[str, Any] = {}

class DocumentResponse(BaseModel):
    message: str
    document_id: str
    chunks_created: int
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    services: Dict[str, str]
    timestamp: str
    uptime: Optional[float] = None

class SystemStats(BaseModel):
    total_documents: int
    total_chunks: int
    database_type: str
    embedding_model: str
    chat_sessions: int
    uptime: float

# Startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Cybersecurity RAG Chatbot API...")
    
    global rag_service, doc_processor, db_config, embedding_model
    
    try:
        # Initialize database configuration
        db_config = VectorDBConfig()
        logger.info("✅ Database configuration loaded")
        
        # Initialize embedding model (global to avoid reloading)
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Global embedding model loaded")
        
        # Initialize RAG service
        rag_service = CybersecurityRAG(db_config=db_config)
        await rag_service.initialize()
        logger.info("✅ RAG service initialized")
        
        # Initialize document processor
        doc_processor = DocumentProcessor(rag_service=rag_service)
        logger.info("✅ Document processor initialized")
        
        # Process existing documents if any - DO THIS FIRST
        raw_docs_path = "./data/raw_documents"
        if os.path.exists(raw_docs_path) and os.listdir(raw_docs_path):
            logger.info("📄 Processing existing documents...")
            chunks_processed = await doc_processor.process_directory(raw_docs_path)
            logger.info(f"✅ Existing documents processed - {chunks_processed} chunks")
        else:
            logger.info("📄 No existing documents found in data/raw_documents/")
        
        # Test RAG with actual documents
        await _test_rag_with_documents()
        
        logger.info("🎉 API startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down API...")
    if rag_service:
        await rag_service.cleanup()
    logger.info("✅ Shutdown complete")

async def _test_rag_with_documents():
    """Test RAG with actual documents after loading"""
    try:
        # Test if we have any documents
        db_info = rag_service.vector_db.get_collection_info()
        doc_count = db_info.get("document_count", 0)
        
        if doc_count > 0:
            test_query = "cybersecurity"
            query_embedding = await asyncio.to_thread(
                embedding_model.encode, [test_query]
            )
            query_embedding = query_embedding[0].tolist()
            
            docs, scores, ids = await asyncio.to_thread(
                rag_service.vector_db.search, query_embedding, 1
            )
            
            if docs:
                logger.info(f"🎯 RAG system ready! Found {doc_count} documents, sample retrieval works")
            else:
                logger.info(f"📊 RAG system ready with {doc_count} documents")
        else:
            logger.info("📋 RAG system ready (no documents loaded yet)")
            
    except Exception as e:
        logger.warning(f"RAG test completed: {e}")

# Create FastAPI app
app = FastAPI(
    title="Cybersecurity RAG Chatbot API",
    description="API for cybersecurity knowledge chatbot using RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - SECURE VERSION
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Global variables for tracking
start_time = datetime.now()
chat_sessions = set()

# Dependency to get RAG service
async def get_rag_service() -> CybersecurityRAG:
    """Dependency to get RAG service instance"""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

async def get_doc_processor() -> DocumentProcessor:
    """Dependency to get document processor instance"""
    if doc_processor is None:
        raise HTTPException(status_code=503, detail="Document processor not initialized")
    return doc_processor

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Cybersecurity RAG Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    rag: CybersecurityRAG = Depends(get_rag_service)
):
    """
    Main chat endpoint - ask questions about cybersecurity topics
    """
    start_time = datetime.now()
    
    try:
        # Generate session ID if not provided
        session_id = message.session_id or str(uuid.uuid4())
        chat_sessions.add(session_id)
        
        logger.info(f"Chat request - Session: {session_id}, Message: {message.message[:100]}...")
        
        # Get response from RAG service
        response_data = await rag.generate_response(
            question=message.message,
            max_sources=message.max_sources,
            include_sources=message.include_sources
        )
        
        # Calculate response time
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Format sources for response
        sources = []
        if message.include_sources and response_data.get("sources"):
            for i, (doc, score, doc_id) in enumerate(zip(
                response_data["sources"],
                response_data.get("scores", []),
                response_data.get("source_ids", [])
            )):
                sources.append({
                    "rank": i + 1,
                    "content": doc[:500] + "..." if len(doc) > 500 else doc,
                    "similarity_score": round(float(score), 3) if score else 0.0,
                    "document_id": doc_id or f"doc_{i}",
                    "content_length": len(doc)
                })
        
        return ChatResponse(
            response=response_data["answer"],
            sources=sources,
            session_id=session_id,
            response_time=round(response_time, 3),
            timestamp=end_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )

@app.post("/upload-document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_processor: DocumentProcessor = Depends(get_doc_processor)
):
    """
    Upload and process a new document
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Document upload - Filename: {file.filename}")
        
        # Security: Validate file size (max 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes")
        
        # Security: Validate file type
        allowed_extensions = {'.txt', '.pdf', '.md', '.csv', '.json', '.xml'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {allowed_extensions}")
        
        # Read file content
        content = await file.read()
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Save file temporarily with secure filename
        safe_filename = f"{doc_id}{file_extension}"
        temp_file_path = f"./data/temp/{safe_filename}"
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        # Process document
        chunks_created = await doc_processor.process_file(
            file_path=temp_file_path,
            document_id=doc_id
        )
        
        # Clean up temp file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Document processed - ID: {doc_id}, Chunks: {chunks_created}")
        
        return DocumentResponse(
            message="Document uploaded and processed successfully",
            document_id=doc_id,
            chunks_created=chunks_created,
            processing_time=round(processing_time, 3)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@app.post("/upload-text", response_model=DocumentResponse)
async def upload_text(
    doc: DocumentUpload,
    doc_processor: DocumentProcessor = Depends(get_doc_processor)
):
    """
    Upload text content directly (without file)
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Text upload - Filename: {doc.filename}")
        
        # Security: Validate text size (max 1MB)
        MAX_TEXT_SIZE = 1 * 1024 * 1024
        if len(doc.content) > MAX_TEXT_SIZE:
            raise HTTPException(status_code=413, detail=f"Text too large. Max size: {MAX_TEXT_SIZE} characters")
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Process text content
        chunks_created = await doc_processor.process_text(
            text=doc.content,
            filename=doc.filename,
            document_id=doc_id,
            metadata=doc.metadata
        )
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Text processed - ID: {doc_id}, Chunks: {chunks_created}")
        
        return DocumentResponse(
            message="Text uploaded and processed successfully",
            document_id=doc_id,
            chunks_created=chunks_created,
            processing_time=round(processing_time, 3)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process text: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint - verify system status
    """
    try:
        # Check database health
        db_health = {"status": "unknown"}
        if db_config:
            try:
                db = db_config.get_database()
                db_health = check_database_health(db)
            except Exception as e:
                db_health = {"status": "error", "error": str(e)}
        
        # Check services
        services = {
            "rag_service": "running" if rag_service else "not_initialized",
            "document_processor": "running" if doc_processor else "not_initialized",
            "database_config": "running" if db_config else "not_initialized",
            "embedding_model": "loaded" if embedding_model else "not_loaded"
        }
        
        # Calculate uptime
        uptime = (datetime.now() - start_time).total_seconds()
        
        # Determine overall status
        overall_status = "healthy"
        if db_health.get("status") == "error" or any(status != "running" and status != "loaded" for status in services.values()):
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            database=db_health,
            services=services,
            timestamp=datetime.now().isoformat(),
            uptime=round(uptime, 2)
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )

@app.get("/stats", response_model=SystemStats)
async def get_stats(
    rag: CybersecurityRAG = Depends(get_rag_service)
):
    """
    Get system statistics
    """
    try:
        # Get database info
        db_info = rag.vector_db.get_collection_info()
        
        # Calculate uptime
        uptime = (datetime.now() - start_time).total_seconds()
        
        return SystemStats(
            total_documents=db_info.get("document_count", 0),
            total_chunks=db_info.get("document_count", 0),  # Assuming 1:1 for simplicity
            database_type=db_info.get("type", "unknown"),
            embedding_model="all-MiniLM-L6-v2",
            chat_sessions=len(chat_sessions),
            uptime=round(uptime, 2)
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    rag: CybersecurityRAG = Depends(get_rag_service)
):
    """
    Delete a document by ID
    """
    try:
        # Delete from vector database
        success = rag.vector_db.delete([document_id])
        
        if success:
            logger.info(f"Document deleted - ID: {document_id}")
            return {"message": "Document deleted successfully", "document_id": document_id}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

@app.get("/search")
async def search_documents(
    query: str,
    top_k: int = 5,
    rag: CybersecurityRAG = Depends(get_rag_service)
):
    """
    Search documents without generating a response (just retrieval)
    """
    try:
        logger.info(f"Search request - Query: {query[:100]}...")
        
        # Use global embedding model with async thread pool
        query_embedding = await asyncio.to_thread(
            embedding_model.encode, [query]
        )
        query_embedding = query_embedding[0].tolist()
        
        # Search using async database operations
        docs, scores, ids = await asyncio.to_thread(
            rag.vector_db.search, query_embedding, top_k
        )
        
        # Format results
        results = []
        for i, (doc, score, doc_id) in enumerate(zip(docs, scores, ids)):
            results.append({
                "rank": i + 1,
                "content": doc[:300] + "..." if len(doc) > 300 else doc,
                "similarity_score": round(float(score), 3),
                "document_id": doc_id,
                "content_length": len(doc)
            })
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

# Admin endpoint to manually process documents
@app.post("/admin/process-documents")
async def admin_process_documents(doc_processor: DocumentProcessor = Depends(get_doc_processor)):
    """Admin endpoint to process documents manually"""
    try:
        raw_docs_path = "./data/raw_documents"
        if os.path.exists(raw_docs_path) and os.listdir(raw_docs_path):
            chunks = await doc_processor.process_directory(raw_docs_path)
            return {"status": "success", "chunks_processed": chunks, "message": f"Processed {chunks} document chunks"}
        return {"status": "no_documents", "message": "No documents found in data/raw_documents/"}
    except Exception as e:
        raise HTTPException(500, f"Failed to process documents: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status_code": 500}

# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )