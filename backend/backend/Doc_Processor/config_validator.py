from typing import Dict, Any
from pydantic import BaseModel, Field

class PDFConfig(BaseModel):
    ocr_enabled: bool = Field(default=True)
    language: str = Field(...)
    dpi: int = Field(default=300, ge=72, le=1200)

class ImageConfig(BaseModel):
    ocr_language: str = Field(...)
    preprocessing_steps: list[str] = Field(default_factory=list)

class StructuredConfig(BaseModel):
    schema_validation: bool = Field(default=True)

class ProcessorConfig(BaseModel):
    pdf: PDFConfig
    image: ImageConfig
    structured: StructuredConfig

def validate_config(config: Dict[str, Any]) -> ProcessorConfig:
    """Validate configuration using Pydantic models."""
    return ProcessorConfig(**config)