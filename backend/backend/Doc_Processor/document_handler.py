from pathlib import Path
from typing import Dict, Any, List, Union
import magic
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from .processors.pdf_processor import PDFProcessor
from .processors.image_processor import ImageProcessor
from .processors.structured_processor import StructuredProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class DocumentHandler:
    MIME_TYPE_MAPPING = {
        'application/pdf': PDFProcessor,
        'image/jpeg': ImageProcessor,
        'image/png': ImageProcessor,
        'application/json': StructuredProcessor,
        'text/xml': StructuredProcessor,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': StructuredProcessor,
        'text/markdown': StructuredProcessor,
        'text/x-markdown': StructuredProcessor,
        'text/plain': StructuredProcessor,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': StructuredProcessor,  # .docx
        'application/msword': StructuredProcessor,  # .doc
    }


    
    def __init__(
        self,
        config: Dict[str, Any],
        max_workers: int = 4
    ):
        self.config = self._prepare_config(config)
        self.max_workers = max_workers
        
    def _prepare_config(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        if not all(key in config for key in ['pdf', 'image', 'structured']):
            raise ValueError("Missing processor configurations")
        return config
    
    def process_document(
        self,
        file_path: Union[str, Path],
        batch_mode: bool = False
    ) -> Dict[str, Any]:
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Document not found: {path}")
            
            mime_type = self._get_mime_type(path)
            mime_type = mime_type.strip()

            print("Mime Type ", mime_type)

            processor_class = self.MIME_TYPE_MAPPING.get(mime_type)

            print("processor_class ", processor_class)
            
            if not processor_class:
                raise ValueError(f"Unsupported document type: {mime_type}")
            
            config_key = self._get_config_key(mime_type)
            processor = processor_class(self.config[config_key])
            result = processor.process(path)
            
            return {
                'file_path': str(path),
                'mime_type': mime_type,
                'result': result,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            if not batch_mode:
                raise
            return {
                'file_path': str(file_path),
                'error': str(e),
                'status': 'failed'
            }
    
    def _get_mime_type(self, path: Path) -> str:
        if path.suffix.lower() == '.md':
            return 'text/markdown'
        return magic.from_file(str(path), mime=True)
    
    def _get_config_key(self, mime_type: str) -> str:
        mime_to_config = {
            'application/pdf': 'pdf',
            'image/jpeg': 'image',
            'image/png': 'image',
            'application/json': 'structured',
            'text/xml': 'structured',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'structured',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'structured',
            'text/markdown': 'structured',
            'text/x-markdown': 'structured',
            'text/plain': 'structured'
        }
        return mime_to_config.get(mime_type)

    def batch_process(
        self,
        directory: Union[str, Path],
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        path = Path(directory)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        
        pattern = '**/*' if recursive else '*'
        files = [f for f in path.glob(pattern) if f.is_file()]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            process_func = partial(self.process_document, batch_mode=True)
            results = list(executor.map(process_func, files))
        
        return results