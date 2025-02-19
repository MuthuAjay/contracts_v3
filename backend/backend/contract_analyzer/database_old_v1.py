import chromadb
import tiktoken
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Dict, Any
import logging
from functools import lru_cache
import os
import re
from chromadb.utils import embedding_functions
from .config import Config
from Doc_Processor.processors.text_pre_processor import process_agreement

logger = logging.getLogger(__name__)

import re

def extract_sections_to_dict(text):
    """
    Extracts sections from text and creates a dictionary with hierarchical structure
    including sections, subsections, and lettered points. Handles multiple sections
    with same numbers and saves introduction.
    """
    # Save introduction (first 1000-5000 characters)
    introduction = text[:min(len(text), 5000)]
    
    # Pattern to match main sections with name possibly on next line
    main_section_pattern = r'^\s*(\d+)\.\s*\n*([A-Z][A-Z\s\'\-]+)(?:\n|$)'
    
    # Pattern to match lettered sections
    letter_section_pattern = r'^\s*([A-Z])\s*\n*([A-Z][A-Z\s\'\-]+)(?:\n|$)'
    
    # Pattern to match sections without letters (like SCOPE OF WORK)
    regular_section_pattern = r'^([A-Z][A-Z\s\'\-]+)(?:\n|$)'
    
    # Pattern to match subsections
    subsection_pattern = r'^\s*(\d+\.\d+)\s*$'
    
    # Pattern to match lettered points
    letter_pattern = r'^\s*\(([a-z])\)\s*$'
    
    # Pattern for special sections
    whereas_pattern = r'^WHEREAS\s'
    signatories_pattern = r'^SIGNATORIES\s*$'
    
    sections = {
        'introduction': introduction,
        'sections': {}
    }
    current_section = None
    current_section_name = None
    current_subsection = None
    current_letter = None
    current_content = []
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        current_line = lines[i].strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        combined_lines = f"{current_line}\n{next_line}"
        
        # Check for WHEREAS section
        whereas_match = re.match(whereas_pattern, current_line)
        if whereas_match:
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            current_section = 'whereas'
            current_section_name = 'WHEREAS'
            sections['sections'][current_section] = {
                'name': current_section_name,
                'content': '',
                'subsections': {}
            }
            current_content = [current_line]
            i += 1
            continue
            
        # Check for SIGNATORIES section
        sig_match = re.match(signatories_pattern, current_line)
        if sig_match:
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            current_section = 'signatories'
            current_section_name = 'SIGNATORIES'
            sections['sections'][current_section] = {
                'name': current_section_name,
                'content': '',
                'subsections': {}
            }
            current_content = []
            i += 1
            continue
        
        # Check for regular sections without letters
        regular_match = re.match(regular_section_pattern, current_line)
        if regular_match:
            section_name = regular_match.group(1).strip()
            # Skip if it's likely a false positive or part of another section
            if (len(section_name) < 3 or 
                section_name in ['CEO', 'CFO'] or 
                current_line.startswith('Email:') or
                current_line.startswith('Address:')):
                current_content.append(current_line)
                i += 1
                continue
                
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            
            section_key = section_name.lower().replace(' ', '_')
            if section_key not in sections['sections']:
                sections['sections'][section_key] = {
                    'name': section_name,
                    'content': '',
                    'subsections': {}
                }
            current_section = section_key
            current_section_name = section_name
            current_subsection = None
            current_letter = None
            current_content = []
            i += 1
            continue
            
        # Check for lettered sections (like A, B, C)
        letter_match = re.match(letter_section_pattern, combined_lines)
        if letter_match:
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            
            section_letter = letter_match.group(1)
            section_name = letter_match.group(2).strip()
            section_key = f"{section_letter}_{section_name.lower().replace(' ', '_')}"
            
            if section_key not in sections['sections']:
                sections['sections'][section_key] = {
                    'letter': section_letter,
                    'name': section_name,
                    'content': '',
                    'subsections': {}
                }
            current_section = section_key
            current_section_name = section_name
            current_subsection = None
            current_letter = None
            current_content = []
            i += 2
            continue
        
        # Check for subsection
        subsection_match = re.match(subsection_pattern, current_line)
        if subsection_match:
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            
            current_subsection = subsection_match.group(1)
            if current_section and current_subsection:
                if 'subsections' not in sections['sections'][current_section]:
                    sections['sections'][current_section]['subsections'] = {}
                if current_subsection not in sections['sections'][current_section]['subsections']:
                    sections['sections'][current_section]['subsections'][current_subsection] = {
                        'content': '',
                        'letters': {}
                    }
            current_letter = None
            current_content = []
            i += 1
            continue
        
        # Check for lettered points
        point_match = re.match(letter_pattern, current_line)
        if point_match:
            if current_content:
                _save_current_content(sections['sections'], current_section,
                                   current_section_name, current_subsection,
                                   current_letter, current_content)
            
            current_letter = point_match.group(1)
            current_content = []
            i += 1
            continue
        
        if current_line:
            current_content.append(current_line)
        i += 1
    
    # Save final content
    if current_content:
        _save_current_content(sections['sections'], current_section,
                           current_section_name, current_subsection,
                           current_letter, current_content)
    
    return sections

def _save_current_content(sections, section, section_name, subsection, letter, content):
    """Helper function to save content at appropriate level"""
    if not section or not sections:
        return
    
    content_text = ' '.join(content).strip()
    if not content_text:
        return
        
    if subsection:
        if letter:
            if letter not in sections[section]['subsections'][subsection]['letters']:
                sections[section]['subsections'][subsection]['letters'][letter] = ''
            sections[section]['subsections'][subsection]['letters'][letter] = content_text
        else:
            sections[section]['subsections'][subsection]['content'] = content_text
    else:
        sections[section]['content'] = content_text

def process_file(text: str):
    """Processes input file and returns structured dictionary with sections"""
    try:
        sections = extract_sections_to_dict(text)
        return sections
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
    
    
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

    def prepare_documents(self, sections: Dict) -> List[Dict]:
        """
        Creates documents with complete sections including all subsections and letters.
        Handles both lettered and non-lettered sections.
        """
        documents = []
        
        # First handle the introduction if present
        if 'introduction' in sections:
            documents.append({
                'id': 'introduction',
                'text': sections['introduction'],
                'metadata': {
                    'name': 'Introduction'
                }
            })
        
        # Process all sections
        for section_key, section_data in sections.get('sections', {}).items():
            full_text = []
            
            # Handle different section types
            if section_key in ['whereas', 'signatories']:
                # Special sections
                full_text.append(section_data['name'])
                if section_data.get('content'):
                    full_text.append(section_data['content'])
            else:
                # Regular or lettered sections
                section_header = section_data['name']
                if 'letter' in section_data:
                    section_header = f"{section_data['letter']}. {section_header}"
                full_text.append(section_header)
                
                # Add main content if exists
                if section_data.get('content'):
                    full_text.append(section_data['content'])
                
                # Add subsections if they exist
                for subsec_num, subsec_data in section_data.get('subsections', {}).items():
                    full_text.append(f"\nSubsection {subsec_num}:")
                    if subsec_data.get('content'):
                        full_text.append(subsec_data['content'])
                    
                    # Add lettered points if they exist
                    for letter, content in subsec_data.get('letters', {}).items():
                        if content:
                            full_text.append(f"\n({letter}) {content}")
            
            # Create metadata
            metadata = {
                'name': section_data['name']
            }
            
            # Add letter to metadata if it exists
            if 'letter' in section_data:
                metadata['letter'] = section_data['letter']
            
            # Generate document ID
            doc_id = section_key.lower().replace(' ', '_')
            
            documents.append({
                'id': doc_id,
                'text': '\n'.join(full_text),
                'metadata': metadata
            })
        
        return documents
    
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
            
            docs = process_file(texts)
            
            print("********Documents processed")
            
            documents = self.prepare_documents(docs)
            
            print("********Documents prepared")
            
            ids = [doc['id'] for doc in documents]
            texts = [doc['text'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            
            self.logger.info(f"Adding {len(documents)} documents to collection")
            
            print(f"********Adding {len(documents)} documents to collection")
            # adding documents to collection
            self.active_collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )
            
            self.logger.info(f"Added {len(documents)} documents to collection")
            
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