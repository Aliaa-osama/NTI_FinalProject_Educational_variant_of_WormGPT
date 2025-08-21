"""
RAG Service with FREE LLM alternatives for Cybersecurity Chatbot
Supports Ollama (local), Hugging Face Transformers, and Google Colab T4 options
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime
import requests
import json

# Import vector_db modules
from backend.vector_db import VectorDBConfig, VectorDatabase

logger = logging.getLogger(__name__)

class CybersecurityRAG:
    """
    RAG service with multiple FREE LLM backends
    """
    
    def __init__(self, db_config: VectorDBConfig, embedding_model: str = "all-MiniLM-L6-v2"):
        self.db_config = db_config
        self.vector_db: Optional[VectorDatabase] = None
        self.embedding_model_name = embedding_model
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # LLM Configuration - Multiple free options
        self.llm_backend = self._detect_available_llm()
        
        # RAG parameters
        self.max_context_length = 2000  # Reduced for free models
        self.chunk_overlap_threshold = 0.8
        
        # Cybersecurity-specific prompt template (shortened for free models)
        self.system_prompt = """You are a cybersecurity expert. Answer based on the provided context.

Context:
{context}

Question: {question}

Answer (be concise and accurate):"""

    def _detect_available_llm(self) -> str:
        """Detect which free LLM backend is available"""
        
        # Option 1: Check if Ollama is running locally
        if self._check_ollama():
            logger.info("🦙 Using Ollama (local) for LLM")
            return "ollama"
        
        # Option 2: Check if Hugging Face token is available
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            logger.info("🤗 Using Hugging Face Inference API")
            return "huggingface"
        
        # Option 3: Use local transformers (slower but completely free)
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("🔥 Using local GPU transformers")
                return "local_gpu"
            else:
                logger.info("💻 Using local CPU transformers")
                return "local_cpu"
        except ImportError:
            pass
        
        # Fallback: Template-based responses
        logger.warning("⚠️ No LLM backend available, using template responses")
        return "template"

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    async def initialize(self):
        """Initialize the RAG service with free LLM"""
        try:
            logger.info("Initializing FREE RAG service...")
            
            # Initialize vector database
            self.vector_db = self.db_config.get_database()
            logger.info(f"✅ Vector database initialized: {type(self.vector_db).__name__}")
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"✅ Embedding model loaded: {self.embedding_model_name}")
            
            # Initialize LLM backend
            await self._initialize_llm()
            
            # Test the setup (modified to not fail if no documents)
            await self._test_setup()
            
            logger.info("🎉 FREE RAG service initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    async def _initialize_llm(self):
        """Initialize the selected LLM backend"""
        
        if self.llm_backend == "ollama":
            await self._init_ollama()
        elif self.llm_backend == "huggingface":
            await self._init_huggingface()
        elif self.llm_backend in ["local_gpu", "local_cpu"]:
            await self._init_local_transformers()
        else:
            logger.info("Using template-based responses (no LLM initialization needed)")

    async def _init_ollama(self):
        """Initialize Ollama - completely free local LLM"""
        try:
            # Check available models
            response = requests.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            
            # Prefer smaller, faster models for 3-day project
            preferred_models = ["llama2:7b-chat", "mistral:7b", "codellama:7b", "llama2"]
            
            self.ollama_model = None
            for model in preferred_models:
                if any(m["name"].startswith(model) for m in models):
                    self.ollama_model = model
                    break
            
            if not self.ollama_model and models:
                # Use first available model
                self.ollama_model = models[0]["name"]
            
            if self.ollama_model:
                logger.info(f"✅ Ollama initialized with model: {self.ollama_model}")
            else:
                logger.error("❌ No Ollama models found. Run: ollama pull llama2")
                raise Exception("No Ollama models available")
                
        except Exception as e:
            logger.error(f"Ollama initialization failed: {e}")
            raise

    async def _init_huggingface(self):
        """Initialize Hugging Face Inference API (free tier)"""
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.hf_model = "microsoft/DialoGPT-medium"  # Free model
        
        # Test API
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": "test"})
            if response.status_code == 200:
                logger.info(f"✅ Hugging Face API initialized with {self.hf_model}")
            else:
                raise Exception(f"API test failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Hugging Face initialization failed: {e}")
            raise

    async def _init_local_transformers(self):
        """Initialize local transformers model"""
        try:
            from transformers import pipeline
            import torch
            
            # Use smaller model for speed
            model_name = "microsoft/DialoGPT-small"
            
            device = 0 if self.llm_backend == "local_gpu" and torch.cuda.is_available() else -1
            
            self.local_pipeline = pipeline(
                "text-generation",
                model=model_name,
                device=device,
                torch_dtype=torch.float16 if device >= 0 else torch.float32
            )
            
            logger.info(f"✅ Local transformers initialized: {model_name}")
            
        except Exception as e:
            logger.error(f"Local transformers initialization failed: {e}")
            raise

    async def _test_setup(self):
        """Test the RAG setup - Modified to not fail if no documents"""
        try:
            test_query = "cybersecurity test"
            test_embedding = self.embedding_model.encode([test_query])[0].tolist()
            docs, scores, ids = self.vector_db.search(test_embedding, top_k=1)
            
            if len(docs) > 0:
                logger.info(f"✅ RAG setup test passed - found {len(docs)} documents")
            else:
                logger.info("✅ RAG setup complete - ready for document ingestion")
                
        except Exception as e:
            logger.warning(f"RAG setup test completed (documents will be loaded later): {e}")

    async def generate_response(
        self,
        question: str,
        max_sources: int = 3,
        include_sources: bool = True,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate response using free LLM"""
        try:
            start_time = datetime.now()
            
            # Step 1: Retrieve documents
            logger.info(f"Processing question: {question[:100]}...")
            query_embedding = self.embedding_model.encode([question])[0].tolist()
            
            docs, scores, ids = await self._retrieve_documents(query_embedding, max_sources * 2)
            
            if not docs:
                return {
                    "answer": "I don't have enough information in my knowledge base to answer this question. Please try rephrasing or check if relevant documents have been uploaded.",
                    "sources": [],
                    "scores": [],
                    "source_ids": [],
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
            
            # Step 2: Filter documents
            filtered_docs, filtered_scores, filtered_ids = self._filter_documents(
                docs, scores, ids, max_sources
            )
            
            # Step 3: Generate answer with free LLM
            answer = await self._generate_answer(question, filtered_docs, temperature)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "answer": answer,
                "processing_time": processing_time
            }
            
            if include_sources:
                result.update({
                    "sources": filtered_docs,
                    "scores": filtered_scores,
                    "source_ids": filtered_ids
                })
            
            logger.info(f"Response generated in {processing_time:.2f}s using {self.llm_backend}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def _retrieve_documents(self, query_embedding: List[float], top_k: int) -> Tuple[List[str], List[float], List[str]]:
        """Retrieve relevant documents"""
        try:
            docs, scores, ids = self.vector_db.search(query_embedding, top_k=top_k)
            logger.info(f"Retrieved {len(docs)} documents, top score: {scores[0] if scores else 'N/A'}")
            return docs, scores, ids
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return [], [], []

    def _filter_documents(self, docs: List[str], scores: List[float], ids: List[str], max_docs: int) -> Tuple[List[str], List[float], List[str]]:
        """Filter documents to avoid redundancy"""
        if len(docs) <= max_docs:
            return docs, scores, ids
        
        filtered_docs = []
        filtered_scores = []
        filtered_ids = []
        
        for i, (doc, score, doc_id) in enumerate(zip(docs, scores, ids)):
            if len(filtered_docs) >= max_docs:
                break
                
            if len(doc.strip()) < 50:
                continue
            
            # Simple similarity check
            is_similar = False
            for existing_doc in filtered_docs:
                doc_words = set(doc.lower().split())
                existing_words = set(existing_doc.lower().split())
                
                if len(doc_words & existing_words) / len(doc_words | existing_words) > self.chunk_overlap_threshold:
                    is_similar = True
                    break
            
            if not is_similar:
                filtered_docs.append(doc)
                filtered_scores.append(score)
                filtered_ids.append(doc_id)
        
        logger.info(f"Filtered to {len(filtered_docs)} unique documents")
        return filtered_docs, filtered_scores, filtered_ids

    async def _generate_answer(self, question: str, context_docs: List[str], temperature: float) -> str:
        """Generate answer using available free LLM"""
        
        # Prepare context
        context = "\n\n".join([f"Doc {i+1}: {doc}" for i, doc in enumerate(context_docs)])
        
        # Truncate context for free models
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "\n[...truncated...]"
        
        # Generate based on available backend
        if self.llm_backend == "ollama":
            return await self._generate_with_ollama(question, context, temperature)
        elif self.llm_backend == "huggingface":
            return await self._generate_with_huggingface(question, context)
        elif self.llm_backend in ["local_gpu", "local_cpu"]:
            return await self._generate_with_local(question, context)
        else:
            return self._generate_template_response(question, context_docs)

    async def _generate_with_ollama(self, question: str, context: str, temperature: float) -> str:
        """Generate with Ollama (completely free)"""
        try:
            prompt = self.system_prompt.format(context=context, question=question)
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 400  # Limit response length
                }
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "http://localhost:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Sorry, I couldn't generate a response.").strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return self._generate_template_response(question, [context])

    async def _generate_with_huggingface(self, question: str, context: str) -> str:
        """Generate with Hugging Face API (free tier)"""
        try:
            prompt = f"Context: {context[:1000]}\nQ: {question}\nA:"
            
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = await asyncio.to_thread(
                requests.post,
                api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    generated = result[0].get("generated_text", "")
                    # Extract answer part
                    answer = generated.split("A:")[-1].strip()
                    return answer if answer else "I couldn't generate a proper response."
                
            raise Exception(f"HF API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Hugging Face generation error: {e}")
            return self._generate_template_response(question, [context])

    async def _generate_with_local(self, question: str, context: str) -> str:
        """Generate with local transformers"""
        try:
            prompt = f"Based on this context: {context[:800]}\nAnswer: {question}\nResponse:"
            
            result = await asyncio.to_thread(
                self.local_pipeline,
                prompt,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.local_pipeline.tokenizer.eos_token_id
            )
            
            if result and isinstance(result, list):
                generated = result[0]["generated_text"]
                # Extract the new part
                answer = generated.replace(prompt, "").strip()
                return answer if answer else "I couldn't generate a response."
                
        except Exception as e:
            logger.error(f"Local generation error: {e}")
            return self._generate_template_response(question, [context])

    def _generate_template_response(self, question: str, context_docs: List[str]) -> str:
        """Fallback template-based response"""
        
        # Simple keyword matching for cybersecurity topics
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['vulnerability', 'exploit', 'cve']):
            topic = "vulnerability assessment"
        elif any(word in question_lower for word in ['network', 'firewall', 'router']):
            topic = "network security"
        elif any(word in question_lower for word in ['penetration', 'pentest', 'ethical hacking']):
            topic = "penetration testing"
        elif any(word in question_lower for word in ['kali', 'tool', 'nmap', 'metasploit']):
            topic = "security tools"
        else:
            topic = "cybersecurity"
        
        return f"""Based on the available documents about {topic}, here's what I found:

{chr(10).join([f"• {doc[:200]}..." for doc in context_docs[:2]])}

Key points from the documentation:
- The information above provides context for your question about {topic}
- For detailed procedures and commands, refer to the full source documents
- Consider consulting official documentation for the most current information

Note: I'm using a simplified response system. For enhanced answers, consider setting up Ollama (free local LLM) by running:"""
    
    async def add_documents(self, docs: List[str], ids: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Add documents to vector database"""
        try:
            logger.info(f"Generating embeddings for {len(docs)} documents...")
            embeddings = self.embedding_model.encode(docs).tolist()
            
            success = self.vector_db.add_documents(docs, embeddings, ids, metadata)
            
            if success:
                logger.info(f"✅ Added {len(docs)} documents to vector database")
            else:
                logger.error("❌ Failed to add documents to vector database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up RAG service...")
            # Cleanup local models if needed
            if hasattr(self, 'local_pipeline'):
                del self.local_pipeline
            logger.info("✅ RAG service cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        try:
            db_info = self.vector_db.get_collection_info()
            
            return {
                "embedding_model": self.embedding_model_name,
                "llm_backend": self.llm_backend,
                "vector_database": type(self.vector_db).__name__,
                "document_count": db_info.get("document_count", 0),
                "max_context_length": self.max_context_length,
                "free_tier": True
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
   