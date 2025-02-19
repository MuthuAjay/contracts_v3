from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from dataclasses import dataclass
from enum import Enum
import os
import time
from concurrent.futures import ThreadPoolExecutor
import tempfile

from Doc_Processor.document_handler import DocumentHandler
from Doc_Processor.config_validator import validate_config
from .config import Config, ProcessorConfig
from .error_handler import handle_errors, DocumentProcessError
from .database import VectorDB

logger = logging.getLogger(__name__)

class ContractStage(Enum):
    """Contract processing stages"""
    DRAFT = "draft"
    NEGOTIATION = "negotiation"
    REVIEW = "review"
    APPROVAL = "approval"
    FINAL = "final"

@dataclass
class ContractMetadata:
    """Contract metadata information"""
    contract_id: str
    stage: ContractStage
    version: int
    created_at: str
    modified_at: str
    processed_by: List[str]
    file_info: Dict[str, Any]

class ContractProcessor:
    """Enhanced contract processor with negotiation capabilities"""
    
    def __init__(self, vector_db: VectorDB, config: Optional[ProcessorConfig] = None):
        """
        Initialize the contract processor.
        
        Args:
            vector_db: Vector database instance
            config: Optional processing configuration
        """
        self.config = config or Config.PROCESSOR_CONFIG
        self.vector_db = vector_db
        self.doc_handler = self._initialize_handler()
        self.logger = logging.getLogger(__name__)

    @handle_errors(error_type=DocumentProcessError, default_return=None)
    def _initialize_handler(self) -> DocumentHandler:
        """Initialize document handler with configuration"""
        try:
            processor_config = {
                'pdf': {
                    'ocr_enabled': self.config.ocr_enabled,
                    'language': self.config.language,
                    'dpi': self.config.dpi
                },
                'image': {
                    'ocr_language': self.config.language,
                    'preprocessing_steps': ['denoise', 'deskew', 'contrast']
                },
                'structured': {
                    'schema_validation': True
                }
            }
            
            # Validate configuration
            validated_config = validate_config(processor_config)
            return DocumentHandler(validated_config)
            
        except Exception as e:
            raise DocumentProcessError(f"Failed to initialize document handler: {str(e)}")

    def process_contract(
        self, 
        file_data: bytes, 
        filename: str,
        stage: ContractStage = ContractStage.DRAFT
    ) -> Dict[str, Any]:
        """
        Process contract document with metadata tracking.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            stage: Current contract stage
            
        Returns:
            Dictionary containing processed content and metadata
        """
        tmp_file = None
        tmp_path = None

        try:
            # Validate file extension
            file_path = Path(filename)
            if not self._validate_extension(file_path):
                raise DocumentProcessError(f"Unsupported file type: {file_path.suffix}")

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_path.suffix) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(file_data)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            # Process document using Doc_Processor
            result = self.doc_handler.process_document(tmp_path)
            
            if not self._validate_result(result):
                raise DocumentProcessError("Invalid processing result")

            # Extract content and create metadata
            processed_data = self._extract_content(result)
            
            # Store in vector database
            collection_name = f"contract_{time.time()}"
            logging.info(f"saving to collection {collection_name}")
            if self.vector_db.create_collection(collection_name):
                if not self.vector_db.add_documents([processed_data['content']]):
                    self.logger.warning("Failed to add document to vector database")

            # Add metadata
            processed_data['metadata'] = self._create_metadata(
                filename=filename,
                stage=stage,
                file_info=processed_data['file_info']
            )

            return processed_data

        except Exception as e:
            self.logger.error(f"Contract processing error: {str(e)}")
            raise DocumentProcessError(str(e))

        finally:
            # Cleanup temporary file
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temporary file: {str(e)}")

    def process_batch(
        self, 
        contract_files: List[Dict[str, Any]],
        max_workers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple contracts in parallel.
        
        Args:
            contract_files: List of contract file data
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of processing results
        """
        max_workers = max_workers or self.config.max_workers
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for contract in contract_files:
                future = executor.submit(
                    self.process_contract,
                    contract['file_data'],
                    contract['filename'],
                    contract.get('stage', ContractStage.DRAFT)
                )
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Batch processing error: {str(e)}")
                    results.append({
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results

    def update_contract_stage(
        self, 
        contract_id: str,
        new_stage: ContractStage,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update contract stage and process new version if provided.
        
        Args:
            contract_id: Contract identifier
            new_stage: New contract stage
            file_data: Optional new file data
            filename: Optional new filename
            
        Returns:
            Updated contract data
        """
        try:
            # If new file provided, process it
            if file_data and filename:
                result = self.process_contract(file_data, filename, new_stage)
                
                # Update metadata
                result['metadata']['contract_id'] = contract_id
                result['metadata']['version'] += 1
                
                return result
            
            # Otherwise just update stage in metadata
            collection = self.vector_db.active_collection
            if not collection:
                raise DocumentProcessError("No active collection")
                
            # Get existing metadata
            metadata = collection.get(ids=[contract_id])
            if not metadata:
                raise DocumentProcessError(f"Contract {contract_id} not found")
                
            # Update stage
            metadata['stage'] = new_stage
            metadata['modified_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            return {'metadata': metadata}
            
        except Exception as e:
            self.logger.error(f"Stage update failed: {str(e)}")
            raise DocumentProcessError(str(e))

    @staticmethod
    def _validate_extension(file_path: Path) -> bool:
        """Validate file extension is supported"""
        SUPPORTED_EXTENSIONS = {
            '.pdf', '.txt', '.docx',
            '.jpg', '.jpeg', '.png',
            '.json', '.xml', '.xlsx'
        }
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    
    @staticmethod
    def _validate_result(result: Dict[str, Any]) -> bool:
        """Validate processing result structure"""
        return (
            isinstance(result, dict) and
            'status' in result and
            result.get('status') == 'success' and
            'result' in result
        )
    
    def _extract_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format content from processing result"""
        content = result['result'].get('content', [])
        
        # Handle different content types
        if isinstance(content, list):
            if content and isinstance(content[0], dict) and 'text' in content[0]:
                # List of page dictionaries
                document_text = '\n'.join(
                    page['text'] for page in content 
                    if page.get('text')
                )
            else:
                # List of strings
                document_text = '\n'.join(str(item) for item in content if item)
        else:
            document_text = str(content)
            
        if not document_text.strip():
            raise DocumentProcessError("No content extracted from document")
            
        return {
            'content': document_text,
            'metadata': result['result'].get('metadata', {}),
            'file_info': {
                'original_name': result.get('file_path', ''),
                'mime_type': result.get('mime_type', ''),
                'size': len(document_text)
            }
        }

    def _create_metadata(
        self, 
        filename: str,
        stage: ContractStage,
        file_info: Dict[str, Any]
    ) -> ContractMetadata:
        """Create metadata for processed contract"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return ContractMetadata(
            contract_id=f"contract_{time.time()}",
            stage=stage,
            version=1,
            created_at=timestamp,
            modified_at=timestamp,
            processed_by=["contract_processor"],
            file_info=file_info
        )