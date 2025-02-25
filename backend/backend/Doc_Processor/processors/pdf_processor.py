import gc
import os
from pathlib import Path
import torch
from typing import Dict, Any, List
import logging
from .base_processor import BaseProcessor
from tqdm.auto import tqdm

# Import marker libraries
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

import warnings
warnings.filterwarnings("ignore")

print("Torch CUDA available: ", torch.cuda.is_available())

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.chunk_size = config.get("chunk_size", 10)  # Process pages in chunks
        self.save_processed_files = config.get("save_processed_files", True)
        self.save_processed_files_dir = config.get("save_processed_files_dir", "processed_files")
        
        # Initialize marker PDF converter
        self.converter = PdfConverter(
            artifact_dict=create_model_dict(),
        )

    def _validate_config(self) -> None:
        """Validate processor configuration with extended checks."""
        required_keys = ["language"]
        if not all(key in self.config for key in required_keys):
            raise ValueError(f"Missing required config keys: {required_keys}")

    def process(self, file_path: Path) -> Dict[str, Any]:
        try:
            print("Processing PDF file:", file_path)
            logger.info(f"Processing PDF file: {file_path}")
            
            # Use marker to convert PDF
            rendered = self.converter(str(file_path))
            text, _,images = text_from_rendered(rendered)
            
            # Create page content structure similar to original format
            pages_content = []
            
            # Split text by page (assuming double newlines separate pages)
            text_pages = text.split("\n\n")
            
            for page_num, page_text in enumerate(text_pages):
                try:
                    page_content = self._create_page_content(page_text.strip(), "marker", page_num)
                    pages_content.append(page_content)
                except Exception as e:
                    logger.error(f"Page {page_num} failed: {str(e)}")
                    pages_content.append(self._create_error_page(page_num, str(e)))
            
            # Save content if configured
            if self.save_processed_files:
                self._save_content({"content": pages_content}, self.save_processed_files_dir, file_path.stem)
            
            return {"content": pages_content, "metadata": self._get_metadata(file_path, len(text_pages)), "images": images}
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            return {"content": [], "metadata": self._get_metadata(file_path, 0), "error": str(e)}
        finally:
            gc.collect()
                
    def _save_content(self, content: Dict[str, Any], output_dir: str, file_name: str) -> None:
        # Save the text into a text file
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        text_file = output_dir_path / f"{file_name}.txt"
        logger.info(f"Saving text to: {text_file}")
        
        with open(text_file, "w") as f:
            for page in content["content"]:
                f.write(page["text"])
                f.write("\n\n")
        
        print(f"Text saved to: {text_file}")

    def _create_page_content(self, text: str, source: str, page_num: int) -> Dict[str, Any]:
        return {
            "text": text,
            "source": source,
            "page": page_num,
        }

    def _create_error_page(self, page_num: int, error: str) -> Dict[str, Any]:
        return {"text": "", "error": error, "page": page_num}
        
    def _get_metadata(self, file_path: Path, page_count: int) -> Dict[str, Any]:
        return {
            "pages": page_count,
            "format": "PDF",
            "filename": file_path.name,
            "file_path": str(file_path.absolute()),
        }