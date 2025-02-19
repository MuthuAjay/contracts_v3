# config.py
from ast import Mod
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import datetime
from typing import Dict, List, Optional, Any, Set
import gc
import logging


@dataclass
class AgentConfig:
    """Configuration for agents"""

    name: str
    role: str
    instructions: List[str]
    capabilities: Set[str] = field(default_factory=set)
    requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Configuration for models"""

    name: str
    model_id: str
    size: str
    description: str


class ModelType(Enum):
    """Available model types"""

    LLAMA_3_2_VISION = "llama3.2-vision"
    LLAVA = "llava"
    QWEN_2_5 = "qwen2.5"
    DEEPSEEK_1_5B = "deepseek-r1:1.5b"
    DEEPSEEK_8B = "deepseek-r1:8b"
    LLAMA_3_1 = "llama3.1"
    DEEPSEEK_14B = "deepseek-r1:14b"
    PHI_4 = "phi4"
    LLAMA_3_3 = "llama3.3"


@dataclass
class ProcessorConfig:
    """Configuration for document processing"""

    ocr_enabled: bool = True
    language: str = "en"
    dpi: int = 300
    extract_images: bool = True
    max_workers: int = 4
    batch_size: int = 100
    chunk_size: int = 2048
    chunk_overlap: int = 50
    save_processed_files: bool = True
    save_processed_files_dir: Path = Path(
        r"/home/ajay/LLM-Agents/server/python/processed_files"
    )


@dataclass
class AgentBuildConfig:
    """Configuration for agent building"""

    min_confidence: float = 0.7
    required_capabilities: Set[str] = field(default_factory=set)
    min_instructions: int = 3
    max_instructions: int = 10
    allow_custom: bool = True
    validation_required: bool = True


@dataclass
class DatabaseConfig:
    """Configuration for database operations"""

    collection_prefix: str = "contract"
    similarity_threshold: float = 0.85
    max_results: int = 5
    cache_ttl_minutes: int = 30


class Config:
    """Central configuration management"""

    # Database configuration
    CHROMA_DB_PATH = Path("./chroma_db")
    COLLECTION_NAME = f"legal_docs_{datetime.datetime.now().timestamp()}"

    # Embedding configuration
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    # EMBEDDING_MODEL = r"billatsectorflow/stella_en_400M_v5"
    ENCODING_NAME = "cl100k_base"

    # Model management
    _current_model: Optional[ModelConfig] = None
    _current_model_type: ModelType = ModelType.LLAMA_3_1
    _model_instances: Dict[ModelType, Any] = {}

    # Processing configuration
    PROCESSOR_CONFIG = ProcessorConfig()

    # Agent building configuration
    AGENT_BUILD_CONFIG = AgentBuildConfig(
        required_capabilities={
            "basic_analysis",
            "text_comprehension",
            "logical_reasoning",
        }
    )

    SAVE_PROCESSED_TEXT = True
    SAVE_PROCESSED_TEXT_DIR = Path(
        "/home/ajay/LLM-Agents/server/python/processed_files"
    )

    # Database configuration
    DATABASE_CONFIG = DatabaseConfig()

    # Available models configuration
    AVAILABLE_MODELS = {
        ModelType.LLAMA_3_2_VISION: ModelConfig(
            name="llama3.2-vision",
            model_id="085a1fdae525",
            size="7.9 GB",
            description="Latest Llama model with vision capabilities",
        ),
        ModelType.LLAVA: ModelConfig(
            name="llava",
            model_id="8dd30f6b0cb1",
            size="4.7 GB",
            description="Vision-language model based on Llama architecture",
        ),
        ModelType.QWEN_2_5: ModelConfig(
            name="qwen2.5",
            model_id="845dbda0ea48",
            size="4.7 GB",
            description="Qwen language model version 2.5",
        ),
        ModelType.DEEPSEEK_1_5B: ModelConfig(
            name="deepseek-r1:1.5b",
            model_id="a42b25d8c10a",
            size="1.1 GB",
            description="Lightweight DeepSeek model (1.5B parameters)",
        ),
        ModelType.DEEPSEEK_8B: ModelConfig(
            name="deepseek-r1:8b",
            model_id="28f8fd6cdc67",
            size="4.9 GB",
            description="Larger DeepSeek model (8B parameters)",
        ),
        ModelType.LLAMA_3_1: ModelConfig(
            name="llama3.1",
            model_id="46e0c10c039e",
            size="4.9 GB",
            description="Llama 3.1 base model",
        ),
        ModelType.DEEPSEEK_14B: ModelConfig(
            name="deepseek-r1:14b",
            model_id="ea35dfe18182",
            size="9.0 GB",
            description="DeepSeek model with 14B parameters",
        ),
        ModelType.PHI_4: ModelConfig(
            name="phi4",
            model_id="ac896e5b8b34",
            size="9.1 GB",
            description="Phi 4 language model",
        ),
        ModelType.LLAMA_3_3: ModelConfig(
            name="llama3.3",
            model_id="a6eb4748fd29",
            size="42 GB",
            description="Llama 3.3 language model",
        ),
    }

    @classmethod
    def get_current_model(cls) -> ModelConfig:
        """Get current model configuration"""
        if cls._current_model is None:
            cls._current_model = cls.AVAILABLE_MODELS[cls._current_model_type]
        return cls._current_model

    @classmethod
    def set_model_type(cls, model_type: ModelType) -> None:
        """Change model type and clean up old model instances"""
        if model_type not in cls.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model type: {model_type}")

        try:
            # Clean up old model instance
            if cls._current_model_type in cls._model_instances:
                del cls._model_instances[cls._current_model_type]
                gc.collect()
                logging.info(f"Cleaned up model: {cls._current_model_type.value}")

            # Update model type and reset current model
            cls._current_model_type = model_type
            cls._current_model = None

            logging.info(f"Model switched to: {model_type.value}")

        except Exception as e:
            logging.error(f"Error switching model: {str(e)}")
            raise

    @classmethod
    def get_model_instance(cls, model_type: ModelType) -> Any:
        """Get or create model instance with caching"""
        if model_type not in cls._model_instances:
            config = cls.AVAILABLE_MODELS[model_type]
            cls._model_instances[model_type] = cls._create_model_instance(config)
        return cls._model_instances[model_type]

    @staticmethod
    def _create_model_instance(config: ModelConfig) -> Any:
        """Create new model instance using Ollama"""
        from phi.model.ollama import Ollama

        print(f"Creating model instance: {config.name}")
        
        return Ollama(
            id=config.name.lower(),
            config={
                "temperature": 0.9,
                "num_ctx": 4096,
            },
        )

    @staticmethod
    def get_agent_configs() -> Dict[str, AgentConfig]:
        """Get configurations for available agents"""
        return {
            "contract_analyst": AgentConfig(
                name="Contract Analyst",
                role="Contract analysis specialist",
                instructions=[
                    "Review contracts thoroughly",
                    "Identify key terms and potential issues",
                    "Focus on obligations and liabilities",
                    "Highlight important clauses and conditions",
                ],
                capabilities={
                    "contract_review",
                    "term_analysis",
                    "risk_identification",
                    "clause_evaluation",
                },
            ),
            "legal_researcher": AgentConfig(
                name="Legal Researcher",
                role="Legal research specialist",
                instructions=[
                    "Research relevant cases and precedents",
                    "Provide detailed research summaries",
                    "Focus on legal principles and applications",
                    "Identify relevant regulations and standards",
                ],
                capabilities={
                    "legal_research",
                    "case_analysis",
                    "regulatory_review",
                    "precedent_identification",
                },
            ),
            "legal_strategist": AgentConfig(
                name="Legal Strategist",
                role="Legal strategy specialist",
                instructions=[
                    "Develop comprehensive legal strategies",
                    "Assess risks and opportunities",
                    "Provide actionable recommendations",
                    "Consider long-term implications",
                ],
                capabilities={
                    "strategy_development",
                    "risk_assessment",
                    "recommendation_formulation",
                    "impact_analysis",
                },
            ),
            "negotiation_analyst": AgentConfig(
                name="Negotiation Analyst",
                role="Contract negotiation specialist",
                instructions=[
                    "Analyze contract terms for negotiation",
                    "Identify key negotiation points",
                    "Suggest negotiation strategies",
                    "Track negotiation progress",
                    "Provide comparative analysis",
                ],
                capabilities={
                    "negotiation_analysis",
                    "strategy_planning",
                    "term_comparison",
                    "progress_tracking",
                },
            ),
            "risk_assessor": AgentConfig(
                name="Risk Assessor",
                role="Risk analysis specialist",
                instructions=[
                    "Evaluate contract risks comprehensively",
                    "Identify potential compliance issues",
                    "Assess financial implications",
                    "Rate risk levels with justification",
                    "Suggest risk mitigation strategies",
                ],
                capabilities={
                    "risk_evaluation",
                    "compliance_assessment",
                    "financial_analysis",
                    "mitigation_planning",
                },
            ),
        }

    @classmethod
    def cleanup_resources(cls) -> None:
        """Clean up all model instances and resources"""
        cls._model_instances.clear()
        cls._current_model = None
        gc.collect()
        logging.info("Cleaned up all model resources")
