from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
import os
import logging
from pathlib import Path
import json

# Core vector database interface
class VectorDatabase(ABC):
    """Abstract base class for vector database implementations"""
    
    @abstractmethod
    def add_documents(self, docs: List[str], embeddings: List[List[float]], 
                     ids: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Add documents with their embeddings to the database"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> Tuple[List[str], List[float], List[str]]:
        """Search for similar documents and return docs, scores, and IDs"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by their IDs"""
        pass
    
    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection (count, etc.)"""
        pass

# ChromaDB Implementation (34an e7na 3-day project)
class ChromaDBClient(VectorDatabase):
    """ChromaDB implementation - local, persistent, zero-setup"""
    
    def __init__(self, collection_name: str = "cybersec_docs", persist_directory: str = "./vector_store/chroma_db"):
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create directory if it doesn't exist
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize persistent client
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity (if any one want to change fell)
            )
            
            self.collection_name = collection_name
            logging.info(f"ChromaDB initialized: {collection_name}")
            
        except ImportError:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        except Exception as e:
            raise Exception(f"Failed to initialize ChromaDB: {str(e)}")
    
    def add_documents(self, docs: List[str], embeddings: List[List[float]], 
                     ids: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        try:
            # Prepare metadata
            if metadata is None:
                metadata = [{"source": f"doc_{i}", "text_length": len(doc)} for i, doc in enumerate(docs)]
            
            # Add to collection
            self.collection.add(
                documents=docs,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadata
            )
            
            logging.info(f"Added {len(docs)} documents to ChromaDB")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add documents to ChromaDB: {str(e)}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> Tuple[List[str], List[float], List[str]]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'distances', 'metadatas']
            )
            
            docs = results['documents'][0] if results['documents'] else []
            # Convert distances to similarity scores (ChromaDB returns distances)
            distances = results['distances'][0] if results['distances'] else []
            scores = [1.0 - dist for dist in distances]  # Convert distance to similarity
            ids = results['ids'][0] if results['ids'] else []
            
            return docs, scores, ids
            
        except Exception as e:
            logging.error(f"Failed to search ChromaDB: {str(e)}")
            return [], [], []
    
    def delete(self, ids: List[str]) -> bool:
        try:
            self.collection.delete(ids=ids)
            logging.info(f"Deleted {len(ids)} documents from ChromaDB")
            return True
        except Exception as e:
            logging.error(f"Failed to delete documents from ChromaDB: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "type": "ChromaDB",
                "document_count": count,
                "status": "connected"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

# Pinecone Implementation (Optional cloud upgrade) but needs more time
class PineconeClient(VectorDatabase):
    """Pinecone implementation - cloud-hosted, scalable"""
    
    def __init__(self, api_key: str, environment: str, index_name: str, dimension: int = 384):
        try:
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(api_key=api_key, environment=environment)
            
            # Create index if it doesn't exist
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric="cosine"
                )
                logging.info(f"Created new Pinecone index: {index_name}")
            
            self.index = pinecone.Index(index_name)
            self.index_name = index_name
            logging.info(f"Pinecone initialized: {index_name}")
            
        except ImportError:
            raise ImportError("Pinecone not installed. Run: pip install pinecone-client")
        except Exception as e:
            raise Exception(f"Failed to initialize Pinecone: {str(e)}")
    
    def add_documents(self, docs: List[str], embeddings: List[List[float]], 
                     ids: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        try:
            # Prepare vectors for Pinecone
            vectors = []
            for i, (doc_id, embedding) in enumerate(zip(ids, embeddings)):
                meta = metadata[i] if metadata else {"text": docs[i][:1000]}  # Pinecone metadata limit
                meta["full_text"] = docs[i]  # Store full text
                vectors.append((doc_id, embedding, meta))
            
            # Upsert in batches (Pinecone has batch limits)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logging.info(f"Added {len(docs)} documents to Pinecone")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add documents to Pinecone: {str(e)}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> Tuple[List[str], List[float], List[str]]:
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            docs = [match['metadata']['full_text'] for match in results['matches']]
            scores = [match['score'] for match in results['matches']]
            ids = [match['id'] for match in results['matches']]
            
            return docs, scores, ids
            
        except Exception as e:
            logging.error(f"Failed to search Pinecone: {str(e)}")
            return [], [], []
    
    def delete(self, ids: List[str]) -> bool:
        try:
            self.index.delete(ids=ids)
            logging.info(f"Deleted {len(ids)} documents from Pinecone")
            return True
        except Exception as e:
            logging.error(f"Failed to delete documents from Pinecone: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        try:
            stats = self.index.describe_index_stats()
            return {
                "name": self.index_name,
                "type": "Pinecone",
                "document_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "status": "connected"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}

# Vector Database Factory
class VectorDBFactory:
    """Factory class to create vector database instances"""
    
    @staticmethod
    def create_database(db_type: str, config: Dict[str, Any]) -> VectorDatabase:
        """Create a vector database instance based on type and configuration"""
        
        if db_type.lower() == "chromadb":
            return ChromaDBClient(
                collection_name=config.get("collection_name", "cybersec_docs"),
                persist_directory=config.get("persist_directory", "./vector_store/chroma_db")
            )
        
        elif db_type.lower() == "pinecone":
            required_fields = ["api_key", "environment", "index_name"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Pinecone requires '{field}' in config")
            
            return PineconeClient(
                api_key=config["api_key"],
                environment=config["environment"],
                index_name=config["index_name"],
                dimension=config.get("dimension", 384)
            )
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

# Configuration Manager
class VectorDBConfig:
    """Configuration manager for vector databases"""
    
    def __init__(self, config_file: str = "vector_db_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        
        default_config = {
            "default_db": "chromadb",
            "databases": {
                "chromadb": {
                    "collection_name": "cybersec_docs",
                    "persist_directory": "./vector_store/chroma_db"
                },
                "pinecone": {
                    "api_key": os.getenv("PINECONE_API_KEY", ""),
                    "environment": os.getenv("PINECONE_ENVIRONMENT", ""),
                    "index_name": "cybersec-chatbot",
                    "dimension": 384
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logging.info(f"Loaded config from {self.config_file}")
                return config
            except Exception as e:
                logging.warning(f"Failed to load config: {e}. Using defaults.")
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Saved config to {self.config_file}")
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    def get_database(self, db_type: Optional[str] = None) -> VectorDatabase:
        """Get configured database instance"""
        
        if db_type is None:
            db_type = self.config["default_db"]
        
        if db_type not in self.config["databases"]:
            raise ValueError(f"Database type '{db_type}' not configured")
        
        db_config = self.config["databases"][db_type]
        return VectorDBFactory.create_database(db_type, db_config)
    
    def update_config(self, db_type: str, new_config: Dict[str, Any]) -> None:
        """Update configuration for a database type"""
        
        self.config["databases"][db_type] = new_config
        self._save_config(self.config)
        logging.info(f"Updated config for {db_type}")

# Database Health Checker
def check_database_health(db: VectorDatabase) -> Dict[str, Any]:
    """Check the health and status of a vector database"""
    
    try:
        info = db.get_collection_info()
        
        # Test basic functionality
        test_embedding = [0.1] * 384  # Test embedding
        test_docs, test_scores, test_ids = db.search(test_embedding, top_k=1)
        
        info["search_functional"] = True
        info["last_check"] = "success"
        
        return info
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "search_functional": False,
            "last_check": "failed"
        }