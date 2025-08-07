import os
import logging
# import atexit
import threading
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
LANGCHAIN_AVAILABLE = True
import uuid

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HomeLoanRAGSystem:
    """RAG system for home loan requirements using Qdrant vector database"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to prevent multiple instances"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(HomeLoanRAGSystem, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 qdrant_url: str = os.getenv("QDRANT_URL"),
                 collection_name: str = os.getenv("QDRANT_COLLECTION_NAME"),
                 api_key: str = os.getenv("QDRANT_API_KEY"),
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG system
        
        Args:
            qdrant_url: URL for Qdrant Cloud instance
            collection_name: Name of the collection in Qdrant
            api_key: API key for Qdrant Cloud authentication
            embedding_model: Sentence transformer model for embeddings
        """
        # Only initialize once
        if self._initialized:
            return
            
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.api_key = api_key
        self.embedding_model_name = embedding_model
        
        # Initialize components
        self.client = None
        self.embedding_model = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        self._initialize_components()
        
        # Register cleanup function
        # atexit.register(self._cleanup)
        
        # Mark as initialized
        self._initialized = True
    
    def _initialize_components(self):
        """Initialize Qdrant client and embedding model"""
        try:
            # Clean up any existing client first
            # self._cleanup_client()
            
            # Initialize Qdrant Cloud client
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.api_key,
                prefer_grpc=True  # Recommended for better performance with Qdrant Cloud
            )
            logger.info(f"Connected to Qdrant Cloud at {self.qdrant_url}")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            
            # Create collection if it doesn't exist
            self._create_collection_if_not_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {str(e)}")
            # self._cleanup_client()
            self.client = None
            self.embedding_model = None
    
    def _create_collection_if_not_exists(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Get embedding dimension
                sample_embedding = self.embedding_model.encode(["sample text"])
                embedding_dim = len(sample_embedding[0])
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
    
    def ingest_pdf(self, pdf_path: str) -> bool:
        """
        Ingest a PDF document into the vector database
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client or not self.embedding_model:
            logger.error("RAG system not properly initialized")
            return False
        
        try:
            # Load PDF
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False
            
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from PDF")
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Generate embeddings and store in Qdrant
            points = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embedding_model.encode(chunk.page_content).tolist()
                print(embedding)
                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "content": chunk.page_content,
                        "source": pdf_path,
                        "page": chunk.metadata.get("page", 0),
                        "chunk_index": i
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Successfully ingested {len(points)} chunks from {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF: {str(e)}")
            return False
    
    def search_similar_documents(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Search for similar documents based on query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of similar documents with content and metadata
        """
        if not self.client or not self.embedding_model:
            logger.error("RAG system not properly initialized")
            return []
        
        # Debug: Check collection info
        try:
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} has {collection_info.vectors_count} vectors")
        except Exception as e:
            logger.error(f"Collection {self.collection_name} not found or error: {e}")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload["content"],
                    "source": result.payload["source"],
                    "page": result.payload.get("page", 0),
                    "score": result.score,
                    "chunk_index": result.payload.get("chunk_index", 0)
                })
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            return []
    
    def generate_rag_response(self, query: str, llm_conversation=None) -> str:
        """
        Generate response using RAG - retrieve relevant documents and generate answer
        
        Args:
            query: User query
            llm_conversation: LangChain conversation chain for generation
            
        Returns:
            Generated response based on retrieved documents
        """
        try:
            # Retrieve relevant documents
            relevant_docs = self.search_similar_documents(query, top_k=3)
            
            if not relevant_docs:
                return "I apologize, but I couldn't find relevant information about your query in our home loan documentation. Please contact our support team for more specific assistance."
            
            # Prepare context from retrieved documents
            context = "\n\n".join([doc["content"] for doc in relevant_docs])
            
            # Create RAG prompt
            rag_prompt = f"""Based on the following home loan documentation, please answer the user's question accurately and helpfully:
CONTEXT:
{context}
USER QUESTION: {query}
Please provide a comprehensive answer based on the documentation above. If the documentation doesn't 
contain enough information to fully answer the question, please mention that and suggest contacting support for more details."""

            # Generate response using LLM if available
            if llm_conversation:
                try:
                    response = llm_conversation.predict(input=rag_prompt)
                    return response.strip()
                except Exception as e:
                    logger.error(f"LLM generation failed: {str(e)}")
            
            # Fallback response with context
            return f"Based on our home loan documentation:\n\n{context[:1000]}{'...' if len(context) > 1000 else ''}\n\nFor more specific information about your query, please contact our support team."
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {str(e)}")
            return "I apologize, but I'm currently unable to process your query. Please try again later or contact our support team."
    
    def is_initialized(self) -> bool:
        """Check if the RAG system is properly initialized"""
        return self.client is not None and self.embedding_model is not None
    
    # def _cleanup_client(self):
    #     """Clean up existing Qdrant client"""
    #     if hasattr(self, 'client') and self.client is not None:
    #         try:
    #             # Close the client connection
    #             if hasattr(self.client, 'close'):
    #                 self.client.close()
    #             logger.info("Cleaned up existing Qdrant client")
    #         except Exception as e:
    #             logger.warning(f"Error cleaning up Qdrant client: {str(e)}")
    #         finally:
    #             self.client = None
    
    # def _cleanup(self):
    #     """Cleanup method called on exit"""
    #     try:
    #         self._cleanup_client()
    #         logger.info("RAG system cleanup completed")
    #     except Exception as e:
    #         logger.error(f"Error during RAG system cleanup: {str(e)}")
    
    # @classmethod
    # def reset_instance(cls):
    #     """Reset the singleton instance (useful for testing or reinitialization)"""
    #     with cls._lock:
    #         if cls._instance is not None:
    #             cls._instance._cleanup()
    #             cls._instance = None
    #             cls._initialized = False
    #             logger.info("RAG system instance reset")
    
    def get_collection_info(self) -> dict:
        """Get information about the current collection"""
        if not self.client:
            return {"error": "Client not initialized"}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "status": collection_info.status
            }
        except Exception as e:
            return {"error": str(e)}
