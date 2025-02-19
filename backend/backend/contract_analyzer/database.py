import chromadb
import tiktoken
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Dict, Any
import logging
from functools import lru_cache
import os
import re
from chromadb.utils import embedding_functions
from contract_analyzer.config import Config
from Doc_Processor.processors.text_pre_processor import process_agreement

logger = logging.getLogger(__name__)

import re

    
class VectorDB:
    """Core vector database operations"""

    def __init__(self):
        """Initialize database components"""
        self.active_collection = None
        self._init_components()
        self.logger = logging.getLogger(__name__)

    def _init_components(self):
        """Initialize required database components"""
        try:
            db_path = str(Config.CHROMA_DB_PATH)
            os.makedirs(db_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=db_path)
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
            
        except Exception as e:
            self.logger.error(f"VectorDB initialization failed: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def _compute_embedding(self, text: str) -> List[float]:
        """
        Compute embedding for text with caching
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        return self.model.encode([text], normalize_embeddings=True).tolist()[0]


    def create_collection(self, collection_name: str) -> bool:
        """
        Create a new collection
        
        Args:
            collection_name: Name for the collection
            
        Returns:
            Success status
        """
        try:
            safe_name = self._sanitize_collection_name(collection_name)
            # print("creating collection ", safe_name)
            if not self._collection_exists(safe_name):
                logging.info(f"Creating new collection: {safe_name}")
                self.active_collection = self.client.create_collection(
                    name=safe_name,
                    embedding_function= self.embedding_fn,
                    metadata={"name": safe_name}
                    )
                logging.info(f"Created new collection: {safe_name}")
                self.logger.info(f"Created new collection: {safe_name}")
            else:
                self.active_collection = self.client.get_collection(name=safe_name)
                self.logger.info(f"Using existing collection: {safe_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Collection creation failed: {str(e)}")
            return False

    def set_active_collection(self, collection_name: str) -> bool:
        """
        Set the active collection for operations
        
        Args:
            collection_name: Name of collection to activate
            
        Returns:
            Success status
        """
        try:
            safe_name = self._sanitize_collection_name(collection_name)
            if not self._collection_exists(safe_name):
                self.logger.error(f"Collection not found: {safe_name}")
                return False
                
            self.active_collection = self.client.get_collection(
                name=safe_name,
                embedding_function= self.embedding_fn
                )
            self.logger.info(f"Set active collection to: {safe_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set active collection: {str(e)}")
            return False

    
    def add_documents(
        self, 
        texts: str,
    ) -> bool:
        """
        Add documents to the active collection
        
        Args:
            docs: List of documents to add
            metadatas: Optional metadata for each document
            
        Returns:
            Success status
        """
        if not self.active_collection:
            print("********No active collection")
            self.logger.error("No active collection")
            return False
            
        try:
            # creating documents
            
            docs = process_agreement(texts)
        
            # create ids
            
            
            print(f"********Adding {len(docs)} documents to collection")
            
            documents = ["content: " + key + " \n " + str(value) for key, value in docs.items()]
            # adding documents to collection
            self.active_collection.add(
                ids = list(docs.keys()),
                documents=documents,
            )
            
            self.logger.info(f"Added {len(docs)} documents to collection")
            
            print("********Documents added")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Document addition failed: {str(e)}")
            return False

    def get_documents(
        self, 
        ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, List]]:
        """
        Get documents from active collection
        
        Args:
            ids: Optional list of document IDs to retrieve
            
        Returns:
            Dictionary containing documents and metadata
        """
        if not self.active_collection:
            print("********No active collection while getting documents")
            self.logger.error("No active collection")
            return None
            
        try:
            return self.active_collection.get(ids=ids)
        except Exception as e:
            self.logger.error(f"Document retrieval failed: {str(e)}")
            return None

    def get_context(
        self, 
        query: str, 
        num_results: int = 3
    ) -> Optional[str]:
        """
        Get relevant context for a query
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Combined context string
        """
        
        if not self.active_collection:
            print("********No active collection while getting context")
            self.logger.error("No active collection")
            return None
            
        try:
            
            results = self.active_collection.query(
                query_texts=[query],
                n_results=num_results,
            )
            
            if not results['documents'] or not results['documents'][0]:
                return None
            
            chunks = results['documents'][0]
            metadatas = results['metadatas'][0]
            
            sorted_results = sorted(
                zip(chunks, metadatas))
            
            return "\n...\n".join(chunk for chunk, _ in sorted_results)
            
        except Exception as e:
            self.logger.error(f"Context retrieval failed: {str(e)}")
            return None

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            Success status
        """
        print("*********Deleting collection")
        try:
            safe_name = self._sanitize_collection_name(collection_name)
            if not self._collection_exists(safe_name):
                self.logger.warning(f"Collection not found: {safe_name}")
                return False
                
            self.client.delete_collection(name=safe_name)
            if self.active_collection and self.active_collection.name == safe_name:
                self.active_collection = None
                
            self.logger.info(f"Deleted collection: {safe_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Collection deletion failed: {str(e)}")
            return False

    def _collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        # print("*********Checking if collection exists")
        # print(collection_name in self.client.list_collections())
        return collection_name in self.client.list_collections()

    def _sanitize_collection_name(self, name: str) -> str:
        """Sanitize collection name for database use"""
        return "".join(c if c.isalnum() else "_" for c in name)

    def _prepare_batch_metadata(
        self,
        batch_start: int,
        batch_size: int,
        token_counts: List[int],
        timestamp: str,
        total_chunks: int,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare metadata for batch processing"""
        if metadatas:
            return [{
                **metadatas[batch_start//batch_size].copy(),
                'tokens': count,
                'timestamp': timestamp,
                'chunk_index': batch_start + j,
                'total_chunks': total_chunks
            } for j, count in enumerate(token_counts)]
        else:
            return [{
                'tokens': count,
                'timestamp': timestamp,
                'chunk_index': batch_start + j,
                'total_chunks': total_chunks
            } for j, count in enumerate(token_counts)]

    def cleanup(self):
        """Cleanup database resources"""
        try:
            print("Cleaning up database")
            self.active_collection = None
            self._compute_embedding.cache_clear()
            self.logger.info("Database cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")