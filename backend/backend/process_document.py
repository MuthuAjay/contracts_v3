#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from contract_analyzer.database import VectorDB
from Doc_Processor.document_handler import DocumentHandler
from Doc_Processor.config_validator import validate_config
from contract_analyzer.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_collection_name(file_path: Path) -> str:
    # Create a collection name based on the file name and size
    collection_name = file_path.stem
    collection_name = collection_name.replace("-", "_").lower().replace(" ", "_")
    collection_name = f"{collection_name}_{file_path.stat().st_size}"
    
    return collection_name

def process_document(file_path: Path) -> tuple[Optional[str], Optional[str]]:
    try:
        
        if isinstance(file_path, str):
            file_path = Path(file_path)
        # Add debug logs
        logger.info(f"Processing document: {file_path}")
        
        processor_config = {
            "pdf": {
                "ocr_enabled": Config.PROCESSOR_CONFIG.ocr_enabled,
                "language": Config.PROCESSOR_CONFIG.language,
                "dpi": Config.PROCESSOR_CONFIG.dpi,
            },
            "image": {
                "ocr_language": Config.PROCESSOR_CONFIG.language,
                "preprocessing_steps": ["denoise", "deskew", "contrast"],
            },
            "structured": {"schema_validation": True},
        }

        doc_handler = DocumentHandler(processor_config)
        result = doc_handler.process_document(file_path)
        
        logger.info(f"Document processing result: {result}")

        if not result or result.get("status") != "success":
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            return None, None

        content = result.get("result", {}).get("content", [])
        text_content = process_content(content)  # Extract this to a function
        
        if not text_content:
            logger.error("Failed to extract text content")
            return None, None

        vector_client = VectorDB()
        collection_name = create_collection_name(file_path)
        
        if collection_name not in vector_client.client.list_collections():
            print(f"Creating collection: {collection_name}")
            vector_client.create_collection(collection_name)
        
            logger.info(f"Adding to collection: {collection_name}")
            
            added_docs = vector_client.add_documents(text_content)
            if not added_docs:
                logger.error("Failed to add documents to vector DB")
                return None, None

        logger.info("Successfully processed document")
        return text_content.strip(), collection_name

    except Exception as e:
        logger.error(f"Document processing failed with exception: {str(e)}")
        return None, None

def process_content(content) -> Optional[str]:
    try:
        if isinstance(content, list):
            if content and isinstance(content[0], dict) and "text" in content[0]:
                return "\n".join(page["text"] for page in content if page.get("text"))
            return "\n".join(str(item) for item in content if item)
        return str(content)
    except Exception as e:
        logger.error(f"Content processing failed: {str(e)}")
        return None
    
# Python
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: process_document.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    document_content, collection_name = process_document(file_path)
    
    if document_content and collection_name:
        print(f"{document_content}|||{collection_name}")
        sys.exit(0)
    else:
        sys.exit(1)