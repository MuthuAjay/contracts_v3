# agents/builders/builder.py
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from ..template.custom import CustomAgentTemplate, AnalysisCategory, CustomRequirement
from ..template.contract_analyst import ContractAnalystTemplate
from ..template.legal_researcher import LegalResearcherTemplate, ResearchScope

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of agents that can be built"""
    CONTRACT_ANALYST = "contract_analyst"
    LEGAL_RESEARCHER = "legal_researcher"
    CUSTOM = "custom"

@dataclass
class AgentConfig:
    """Configuration for agent building"""
    name: str
    role: str
    type: AgentType
    capabilities: Set[str]
    requirements: Dict[str, Any]
    metadata: Dict[str, Any]

class AgentBuilder:
    """Builder for creating specialized agents"""
    
    def __init__(self):
        self._reset()
        self.custom_template = CustomAgentTemplate()
        self.logger = logging.getLogger(__name__)

    def _reset(self):
        """Reset builder to initial state"""
        self._agent_config = None
        self._instructions = []
        self._capabilities = set()
        self._requirements = {}
        self._metadata = {}

    def with_type(self, agent_type: AgentType) -> 'AgentBuilder':
        """Set agent type"""
        if not self._agent_config:
            self._agent_config = AgentConfig(
                name="",
                role="",
                type=agent_type,
                capabilities=set(),
                requirements={},
                metadata={}
            )
        return self

    def with_name(self, name: str) -> 'AgentBuilder':
        """Set agent name"""
        if self._agent_config:
            self._agent_config.name = name
        return self

    def with_role(self, role: str) -> 'AgentBuilder':
        """Set agent role"""
        if self._agent_config:
            self._agent_config.role = role
        return self

    def with_capabilities(self, capabilities: Set[str]) -> 'AgentBuilder':
        """Add capabilities"""
        if self._agent_config:
            self._agent_config.capabilities.update(capabilities)
        return self

    def with_requirements(self, requirements: Dict[str, Any]) -> 'AgentBuilder':
        """Set requirements"""
        if self._agent_config:
            self._agent_config.requirements.update(requirements)
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'AgentBuilder':
        """Add metadata"""
        if self._agent_config:
            self._agent_config.metadata.update(metadata)
        return self

    def from_template(self, template_type: AgentType) -> 'AgentBuilder':
        """Initialize from predefined template"""
        if template_type == AgentType.CONTRACT_ANALYST:
            self._init_contract_analyst()
        elif template_type == AgentType.LEGAL_RESEARCHER:
            self._init_legal_researcher()
        return self

    def customize_for_query(self, query: str) -> 'AgentBuilder':
        """Customize agent based on query"""
        try:
            # Determine requirements from query
            requirements = self.custom_template.determine_requirements(query)
            
            # Update agent configuration
            if self._agent_config:
                self._agent_config.capabilities.update(requirements.required_skills)
                self._agent_config.requirements.update({
                    "min_confidence": requirements.min_confidence,
                    "analysis_categories": [cat.value for cat in requirements.analysis_categories],
                    "specialized_knowledge": requirements.specialized_knowledge
                })
            
            return self
            
        except Exception as e:
            self.logger.error(f"Query customization failed: {str(e)}")
            return self

    def create_prompt(self, context: str) -> Optional[str]:
        """Create agent prompt based on configuration"""
        try:
            if not self._agent_config:
                return None

            if self._agent_config.type == AgentType.CUSTOM:
                # Create custom requirements
                requirements = CustomRequirement(
                    min_confidence=self._agent_config.requirements.get("min_confidence", 0.7),
                    required_skills=self._agent_config.capabilities,
                    analysis_categories=[
                        AnalysisCategory(cat) for cat in 
                        self._agent_config.requirements.get("analysis_categories", ["CUSTOM"])
                    ],
                    context_requirements=self._agent_config.requirements.get("context_requirements", {}),
                    specialized_knowledge=self._agent_config.requirements.get("specialized_knowledge", [])
                )
                
                return self.custom_template.create_custom_prompt(
                    query="Custom analysis",
                    requirements=requirements,
                    context=context
                )
            
            elif self._agent_config.type == AgentType.CONTRACT_ANALYST:
                return ContractAnalystTemplate.create_analysis_prompt(context, "COMPREHENSIVE")
            
            elif self._agent_config.type == AgentType.LEGAL_RESEARCHER:
                return LegalResearcherTemplate.create_research_prompt(
                    context,
                    ResearchScope.COMPREHENSIVE,
                    "CONTRACT_LAW"
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Prompt creation failed: {str(e)}")
            return None

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate agent configuration"""
        if not self._agent_config:
            return False, ["No agent configuration"]

        issues = []
        
        # Basic validation
        if not self._agent_config.name:
            issues.append("Agent name not set")
        if not self._agent_config.role:
            issues.append("Agent role not set")
        if not self._agent_config.capabilities:
            issues.append("No capabilities defined")

        # Type-specific validation
        if self._agent_config.type == AgentType.CUSTOM:
            if not self._agent_config.requirements:
                issues.append("No requirements defined for custom agent")
                
        elif self._agent_config.type == AgentType.CONTRACT_ANALYST:
            required_capabilities = {"contract_analysis", "term_review"}
            missing = required_capabilities - self._agent_config.capabilities
            if missing:
                issues.append(f"Missing required capabilities: {missing}")
                
        elif self._agent_config.type == AgentType.LEGAL_RESEARCHER:
            required_capabilities = {"legal_research", "case_law_analysis"}
            missing = required_capabilities - self._agent_config.capabilities
            if missing:
                issues.append(f"Missing required capabilities: {missing}")

        return len(issues) == 0, issues

    def build(self) -> Optional[Dict[str, Any]]:
        """Build the agent configuration"""
        try:
            is_valid, issues = self.validate()
            if not is_valid:
                self.logger.error(f"Validation failed: {issues}")
                return None

            return {
                "name": self._agent_config.name,
                "role": self._agent_config.role,
                "type": self._agent_config.type.value,
                "capabilities": list(self._agent_config.capabilities),
                "requirements": self._agent_config.requirements,
                "metadata": {
                    **self._agent_config.metadata,
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Build failed: {str(e)}")
            return None

    def _init_contract_analyst(self):
        """Initialize contract analyst configuration"""
        self._agent_config = AgentConfig(
            name="Contract Analyst",
            role="contract_analysis",
            type=AgentType.CONTRACT_ANALYST,
            capabilities=set(ContractAnalystTemplate.CAPABILITIES),
            requirements=ContractAnalystTemplate.REQUIREMENTS,
            metadata=ContractAnalystTemplate.get_metadata()
        )

    def _init_legal_researcher(self):
        """Initialize legal researcher configuration"""
        self._agent_config = AgentConfig(
            name="Legal Researcher",
            role="legal_research",
            type=AgentType.LEGAL_RESEARCHER,
            capabilities=set(LegalResearcherTemplate.CAPABILITIES),
            requirements=LegalResearcherTemplate.REQUIREMENTS,
            metadata=LegalResearcherTemplate.get_metadata()
        )