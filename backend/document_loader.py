"""
Document Processor - Processes documents for RAG system
"""

import logging
import os
from typing import List, Dict, Any, Optional
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process documents for RAG system"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
    
    async def process_file(self, file_path: str, document_id: str) -> int:
        """Process a single file"""
        try:
            # Read file content based on file type
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
            elif file_extension == '.pdf':
                content = await self._read_pdf_file(file_path)
            else:
                # For other file types, try to read as text
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                except:
                    logger.warning(f"Unsupported file type: {file_extension}")
                    return 0
            
            # Simple chunking - split by paragraphs or sections
            chunks = self._chunk_text(content)
            
            if not chunks:
                logger.warning(f"No content extracted from {file_path}")
                return 0
            
            # Add to vector database
            success = await self.rag_service.add_documents(
                docs=chunks,
                ids=[f"{document_id}_chunk_{i}" for i in range(len(chunks))],
                metadata=[{"source_file": os.path.basename(file_path), "chunk_index": i} for i in range(len(chunks))]
            )
            
            return len(chunks) if success else 0
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return 0
    
    async def _read_pdf_file(self, file_path: str) -> str:
        """Read PDF file content - FIXED VERSION"""
        try:
            import PyPDF2
            content = ""
            
            # Read file in binary mode first, then pass to PyPDF2
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Use BytesIO to create a file-like object for PyPDF2
            from io import BytesIO
            pdf_file = BytesIO(file_content)
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    content += page_text + "\n"
            
            return content
            
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        # Simple paragraph-based chunking first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) <= chunk_size:
                chunks.append(paragraph)
            else:
                # Split long paragraphs
                words = paragraph.split()
                current_chunk = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 > chunk_size:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                            # Keep overlap for context
                            current_chunk = current_chunk[-overlap//20:] if overlap > 0 else []
                            current_length = sum(len(w) + 1 for w in current_chunk)
                        current_chunk.append(word)
                        current_length += len(word) + 1
                    else:
                        current_chunk.append(word)
                        current_length += len(word) + 1
                
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def process_text(self, text: str, filename: str, document_id: str, metadata: Dict[str, Any] = None) -> int:
        """Process text content directly"""
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            
            if not chunks:
                logger.warning(f"No content extracted from text: {filename}")
                return 0
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            # Add to vector database
            success = await self.rag_service.add_documents(
                docs=chunks,
                ids=[f"{document_id}_chunk_{i}" for i in range(len(chunks))],
                metadata=[{"source": filename, "chunk_index": i, **metadata} for i in range(len(chunks))]
            )
            
            return len(chunks) if success else 0
            
        except Exception as e:
            logger.error(f"Error processing text from {filename}: {e}")
            return 0
    
    async def process_directory(self, directory_path: str) -> int:
        """Process all files in a directory"""
        total_chunks = 0
        
        if not os.path.exists(directory_path):
            logger.warning(f"Directory {directory_path} does not exist")
            return 0
        
        # Supported file extensions
        supported_extensions = {'.txt', '.pdf', '.md', '.csv', '.json', '.xml'}
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension in supported_extensions:
                    chunks = await self.process_file(file_path, f"dir_{os.path.splitext(filename)[0]}")
                    total_chunks += chunks
                    logger.info(f"Processed {filename}: {chunks} chunks")
                else:
                    logger.warning(f"Skipping unsupported file type: {filename}")
        
        return total_chunks