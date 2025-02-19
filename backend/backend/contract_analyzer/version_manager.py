# version_manager.py
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from .version_control import ContractVersion, ContractVersionManager

class VersionDatabaseManager:
    """Manages version control database operations"""

    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.version_manager = ContractVersionManager(vector_db)
        self.logger = logging.getLogger(__name__)

    def store_contract_version(
        self, 
        contract_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store contract version in database"""
        try:
            collection_name = f"contract_{self._sanitize_name(contract_id)}"
            
            # Create or get collection
            if not self.vector_db._collection_exists(collection_name):
                if not self.vector_db.create_collection(collection_name):
                    return False
            
            if not self.vector_db.set_active_collection(collection_name):
                return False
            
            # Add document with metadata
            return self.vector_db.add_documents([content], [metadata])
            
        except Exception as e:
            self.logger.error(f"Version storage failed: {str(e)}")
            return False

    def get_contract_versions(
        self, 
        contract_id: str
    ) -> List[Dict[str, Any]]:
        """Get all versions of a contract"""
        try:
            collection_name = f"contract_{self._sanitize_name(contract_id)}"
            if not self.vector_db.set_active_collection(collection_name):
                return []
            
            # Get all documents from collection
            results = self.vector_db.active_collection.get()
            versions = []
            
            for doc, metadata in zip(results['documents'], results['metadatas']):
                versions.append({
                    'content': doc,
                    'metadata': metadata
                })
            
            return sorted(versions, key=lambda x: x['metadata']['version_number'])
            
        except Exception as e:
            self.logger.error(f"Version retrieval failed: {str(e)}")
            return []

    def find_similar_contracts(
        self, 
        content: str, 
        min_similarity: float = 0.7, 
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar contracts in database"""
        try:
            # Get all contract collections
            contract_collections = [
                name for name in self.vector_db.client.list_collections()
                if name.startswith('contract_')
            ]
            
            similar_contracts = []
            for collection_name in contract_collections:
                if self.vector_db.set_active_collection(collection_name):
                    context = self.vector_db.get_context(content, num_results=1)
                    if context:
                        similar_contracts.append({
                            'contract_id': collection_name.split('_')[1],
                            'content': context,
                            'similarity_score': 0.0  # To be calculated by version manager
                        })
            
            # Use version manager to enhance results
            return self.version_manager.find_similar_contracts(
                content,
                similar_contracts,
                min_similarity,
                max_results
            )
            
        except Exception as e:
            self.logger.error(f"Similarity search failed: {str(e)}")
            return []

    def create_new_version(
        self,
        contract_id: str,
        content: str,
        author: str,
        comments: str,
        status: str = "draft"
    ) -> Optional[ContractVersion]:
        """Create new contract version"""
        try:
            return self.version_manager.create_version(
                contract_id=contract_id,
                content=content,
                author=author,
                comments=comments,
                status=status
            )
        except Exception as e:
            self.logger.error(f"Version creation failed: {str(e)}")
            return None

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize names for database use"""
        return "".join(c if c.isalnum() else "_" for c in name)