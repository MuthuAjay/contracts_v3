# agent_manager.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime
from enum import Enum
from phi.agent import Agent
from ..config import Config, ModelType
from ..error_handler import handle_errors, ErrorCategory

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Predefined agent roles"""
    CONTRACT_ANALYST = "contract_analyst"
    LEGAL_RESEARCHER = "legal_researcher"
    LEGAL_STRATEGIST = "legal_strategist"
    NEGOTIATION_SPECIALIST = "negotiation_specialist"
    RISK_ASSESSOR = "risk_assessor"
    COMPLIANCE_EXPERT = "compliance_expert"
    CUSTOM = "custom_analyst"
    CONTRACT_SUMMARIZER = "contract_summarizer"
    EXTRACT_INFORMATION = "extract_information"

@dataclass
class AgentTemplate:
    """Template for creating agents"""
    name: str
    role: AgentRole
    instructions: List[str]
    capabilities: List[str]
    requirements: Dict[str, Any]
    metadata: Dict[str, Any]

class AgentManager:
    """Manages agent creation and lifecycle"""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._templates: Dict[str, AgentTemplate] = {}
        self.logger = logging.getLogger(__name__)
        self._load_default_templates()

    def create_agent(
        self,
        template_name: str,
        custom_instructions: Optional[List[str]] = None,
        model_type: Optional[ModelType] = None
    ) -> Optional[Agent]:
        """
        Create a new agent from template
        
        Args:
            template_name: Name of template to use
            custom_instructions: Optional additional instructions
            model_type: Optional specific model to use
        """
        try:
            template = self._templates.get(template_name)
            # print("+++++++",template_name)
            # print("+++++++",template)
            # print("+++++++",self._templates)
            if not template:
                raise ValueError(f"Template {template_name} not found")

            # Get instructions
            instructions = template.instructions
            if custom_instructions:
                instructions.extend(custom_instructions)

            # Get model
            model_type = model_type or Config._current_model_type
            model = Config.get_model_instance(model_type)

            # Create agent
            agent = Agent(
                name=template.name,
                role=template.role.value,
                instructions=instructions,
                model=model
            )

            # Store agent
            agent_id = f"{template.name}_{datetime.now().timestamp()}"
            self._agents[agent_id] = agent

            self.logger.info(f"Created agent: {template.name} with ID: {agent_id}")
            return agent

        except Exception as e:
            self.logger.error(f"Agent creation failed: {str(e)}")
            return None

    def register_template(self, template: AgentTemplate) -> bool:
        """Register new agent template"""
        try:
            template_id = f"{template.role.value}_{template.name}"
            self._templates[template.role.value] = template
            # print("+++++++",self._templates)
            self.logger.info(f"Registered template: {template_id}")
            return True
        except Exception as e:
            self.logger.error(f"Template registration failed: {str(e)}")
            return False

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all active agents with metadata"""
        return {
            agent_id: {
                'name': agent.name,
                'role': agent.role,
                'model': agent.model.id
            }
            for agent_id, agent in self._agents.items()
        }

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent"""
        try:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self.logger.info(f"Removed agent: {agent_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Agent removal failed: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup agents"""
        self._agents = {}
            
    def _load_default_templates(self) -> None:
        default_templates = {
            AgentRole.CONTRACT_ANALYST: AgentTemplate(
                name="Contract Analyst",
                role=AgentRole.CONTRACT_ANALYST,
                instructions=[
                    "Review contracts thoroughly",
                    "Identify key terms and potential issues",
                    "Focus on obligations and liabilities", 
                    "Highlight important clauses and conditions"
                ],
                capabilities=[
                    "Contract review",
                    "Term analysis",
                    "Risk identification", 
                    "Obligation assessment"
                ],
                requirements={"min_context": 3, "min_confidence": 0.8},
                metadata={"type": "core"}
            ),
            AgentRole.LEGAL_RESEARCHER: AgentTemplate(
                name="Legal Researcher",
                role=AgentRole.LEGAL_RESEARCHER, 
                instructions=[
                    "Research legal precedents",
                    "Analyze regulatory requirements",
                    "Identify compliance issues",
                    "Provide legal context"
                ],
                capabilities=[
                    "Legal research",
                    "Precedent analysis",
                    "Regulatory review",
                    "Compliance assessment"
                ],
                requirements={"min_context": 5, "min_confidence": 0.85},
                metadata={"type": "core"}
            ),
            AgentRole.CONTRACT_SUMMARIZER: AgentTemplate(
                name="Contract Summarizer",
                role=AgentRole.CONTRACT_SUMMARIZER,
                instructions=[
                    "Extract key contract information",
                    "Identify parties, dates, and values",
                    "Summarize obligations and deadlines",
                    "Highlight penalties and key clauses"
                ],
                capabilities=[
                    "Information extraction",
                    "Entity recognition",
                    "Timeline analysis",
                    "Structured summarization"
                ],
                requirements={"min_context": 3, "min_confidence": 0.8},
                metadata={"type": "core"}
            ),
            AgentRole.CUSTOM: AgentTemplate(
                name="Custom Analyst",
                role=AgentRole.CUSTOM,
                instructions=[
                    "Analyze documents based on custom requirements",
                    "Extract key insights and patterns",
                    "Generate targeted recommendations",
                    "Provide contextual analysis"
                ],
                capabilities=[
                    "Custom analysis",
                    "Pattern recognition", 
                    "Insight generation",
                    "Context analysis"
                ],
                requirements={"min_context": 3, "min_confidence": 0.75},
                metadata={"type": "custom"}
            ),
            AgentRole.RISK_ASSESSOR : AgentTemplate(
                name="Risk Assessor",
                role=AgentRole.RISK_ASSESSOR,
                instructions=[
                    "Identify potential risks and liabilities",
                    "Assess impact and probability",
                    "Provide risk mitigation strategies",
                    "Highlight key risk factors"
                ],
                capabilities=[
                    "Risk identification",
                    "Impact assessment",
                    "Probability analysis",
                    "Mitigation strategies"
                ],
                requirements={"min_context": 3, "min_confidence": 0.8},
                metadata={"type": "core"}
            ),
            AgentRole.EXTRACT_INFORMATION: AgentTemplate(
                name="Extract Information",
                role=AgentRole.EXTRACT_INFORMATION,
                instructions=[
                    "Extract key information from documents",
                    "Identify entities, dates, and values",
                    "Summarize key details",
                    "Provide structured data output"
                ],
                capabilities=[
                    "Information extraction",
                    "Entity recognition",
                    "Value extraction",
                    "Structured output"
                ],
                requirements={"min_context": 3, "min_confidence": 0.8},
                metadata={"type": "core"}
            )
        }
        
        for template in default_templates.values():
            self.register_template(template)
            
class AgentBuilder:
    """Builder for creating custom agents"""

    def __init__(self, manager: AgentManager):
        self.manager = manager
        self._template = None
        self._instructions = []
        self._capabilities = []
        self._requirements = {}
        self._metadata = {}

    def with_role(self, role: AgentRole) -> 'AgentBuilder':
        """Set agent role"""
        if role == AgentRole.CUSTOM:
            self._template = AgentTemplate(
                name="Custom Agent",
                role=role,
                instructions=[],
                capabilities=[],
                requirements={},
                metadata={"type": "custom"}
            )
        return self

    def with_name(self, name: str) -> 'AgentBuilder':
        """Set agent name"""
        if self._template:
            self._template.name = name
        return self

    def add_instruction(self, instruction: str) -> 'AgentBuilder':
        """Add an instruction"""
        self._instructions.append(instruction)
        return self

    def add_capability(self, capability: str) -> 'AgentBuilder':
        """Add a capability"""
        self._capabilities.append(capability)
        return self

    def set_requirement(self, key: str, value: Any) -> 'AgentBuilder':
        """Set a requirement"""
        self._requirements[key] = value
        return self

    def add_metadata(self, key: str, value: Any) -> 'AgentBuilder':
        """Add metadata"""
        self._metadata[key] = value
        return self

    def build(self) -> Optional[Agent]:
        """Build the agent"""
        if not self._template:
            return None

        self._template.instructions = self._instructions
        self._template.capabilities = self._capabilities
        self._template.requirements = self._requirements
        self._template.metadata.update(self._metadata)

        # Register template
        template_id = f"custom_{self._template.name}"
        if self.manager.register_template(self._template):
            print("inside build")
            return self.manager.create_agent(template_id)

        return None