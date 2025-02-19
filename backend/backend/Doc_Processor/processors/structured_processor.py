from pathlib import Path
from typing import Dict, Any
import json
import xmltodict
import pandas as pd
import markdown
from .base_processor import BaseProcessor
from docx import Document

class StructuredProcessor(BaseProcessor):
    SUPPORTED_FORMATS = {
        '.json': 'json',
        '.xml': 'xml',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.md': 'markdown',
        '.txt': 'text',
        '.docx': 'docx',
    }
    
    def _validate_config(self) -> None:
        required_keys = ['schema_validation']
        if not all(key in self.config for key in required_keys):
            raise ValueError(f"Missing required config keys: {required_keys}")
    
    def process(self, file_path: Path) -> Dict[str, Any]:
        self._log_processing_status("Started processing", file_path)
        try:
            file_format = self.SUPPORTED_FORMATS.get(file_path.suffix.lower())
            if not file_format:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            processor = getattr(self, f"_process_{file_format}")
            return processor(file_path)
            
        except Exception as e:
            self._log_processing_status(f"Error: {str(e)}", file_path)
            raise

    def _process_docx(self, file_path: Path) -> Dict[str, Any]:
        """Process DOCX files."""
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        word_count = sum(len(para.split()) for para in paragraphs)
        
        return {
            'content': '\n'.join(paragraphs),
            'metadata': {
                'format': 'docx',
                'size': file_path.stat().st_size,
                'paragraphs': len(paragraphs),
                'word_count': word_count
            }
        }

    def _process_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Process Markdown files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = markdown.markdown(md_content, extensions=['extra', 'tables', 'fenced_code'])
            return {
                'content': {
                    'raw': md_content,
                    'html': html_content
                },
                'metadata': {
                    'format': 'markdown',
                    'size': file_path.stat().st_size,
                    'has_code': '```' in md_content,
                    'has_tables': '|' in md_content
                }
            }
    
    def _process_json(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path) as f:
            data = json.load(f)
            return {
                'content': data,
                'metadata': {
                    'format': 'json',
                    'size': file_path.stat().st_size
                }
            }
    
    def _process_xml(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path) as f:
            data = xmltodict.parse(f.read())
            return {
                'content': data,
                'metadata': {
                    'format': 'xml',
                    'size': file_path.stat().st_size
                }
            }
    
    def _process_excel(self, file_path: Path) -> Dict[str, Any]:
        df = pd.read_excel(file_path)
        return {
            'content': df.to_dict(),
            'metadata': {
                'format': 'excel',
                'rows': len(df),
                'columns': list(df.columns),
                'size': file_path.stat().st_size
            }
        }
        
    def _process_text(self, file_path: Path) -> Dict[str, Any]:
        """Process text files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return {
                'content': content,
                'metadata': {
                    'format': 'text',
                    'size': file_path.stat().st_size,
                    'lines': len(content.splitlines())
                }
            }
