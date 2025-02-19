from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for document processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._validate_config()
        
    @abstractmethod
    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process the document and return extracted data."""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate processor configuration."""
        pass
    
    def _log_processing_status(self, status: str, file_path: Path) -> None:
        """Log document processing status."""
        logger.info(f"{self.__class__.__name__}: {status} - {file_path}")