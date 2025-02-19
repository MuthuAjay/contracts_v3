from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum
from .database import VectorDB
from .config import Config
from .error_handler import handle_errors, ErrorCategory, ErrorHandler

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of contract analysis"""
    CONTRACT_REVIEW = "contract_review"
    LEGAL_RESEARCH = "legal_research"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECK = "compliance_check"
    NEGOTIATION_ANALYSIS = "negotiation_analysis"
    CUSTOM = "custom"

@dataclass
class AnalysisConfig:
    """Configuration for analysis types"""
    query: str
    agents: List[str]
    required_context: int = 3
    min_confidence: float = 0.7
    max_results: int = 5

class AnalysisResult:
    """Contract analysis result"""
    def __init__(
        self,
        analysis_type: AnalysisType,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
        timestamp: datetime
    ):
        self.analysis_type = analysis_type
        self.content = content
        self.metadata = metadata
        self.timestamp = timestamp
        self.processed = False
        self.summary: Optional[str] = None
        self.recommendations: List[str] = []

    def add_summary(self, summary: str) -> None:
        """Add analysis summary"""
        self.summary = summary
        self.processed = True

    def add_recommendation(self, recommendation: str) -> None:
        """Add analysis recommendation"""
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.analysis_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'summary': self.summary,
            'recommendations': self.recommendations
        }


class PromptTemplates:
    """Detailed templates for contract analysis prompts"""
    
    CONTRACT_REVIEW = """
    Conduct a comprehensive review of the following contract:

    {context}

    Please analyze the following aspects in detail:
    1. Key Terms and Definitions
       - Identify and explain critical defined terms
       - Highlight any ambiguous or concerning definitions
       - Assess the scope of key terms

    2. Rights and Obligations
       - List main obligations for each party
       - Identify conditional obligations
       - Analyze performance requirements

    3. Risk Assessment
       - Identify potential legal risks
       - Evaluate liability exposure
       - Analyze indemnification provisions
       - Assess warranty and guarantee terms

    4. Timeline and Deadlines
       - List critical dates and deadlines
       - Identify timing-related obligations
       - Note any automatic renewal provisions

    5. Termination and Remedies
       - Analyze termination conditions
       - Evaluate remedy provisions
       - Identify cure periods

    Please provide:
    - Specific references to relevant sections
    - Direct quotes of critical language
    - Clear explanations of potential issues
    - Recommendations for improvements

    Your analysis:
    """

    LEGAL_RESEARCH = """
    Conduct legal research relevant to the following contract:

    {context}

    Please research and analyze:
    1. Relevant Legal Framework
       - Applicable laws and regulations
       - Relevant jurisdictional requirements
       - Recent legal developments

    2. Case Law Analysis
       - Similar cases and precedents
       - Relevant court interpretations
       - Notable legal principles

    3. Regulatory Compliance
       - Industry-specific regulations
       - Mandatory legal requirements
       - Compliance obligations

    4. Legal Trends
       - Emerging legal issues
       - Recent court decisions
       - Regulatory changes

    5. Best Practices
       - Industry standards
       - Common legal approaches
       - Risk mitigation strategies

    Please provide:
    - Citations to relevant cases
    - References to applicable laws
    - Analysis of legal implications
    - Practical recommendations

    Your research findings:
    """

    RISK_ASSESSMENT = """
    Conduct a detailed risk assessment of the following contract:

    {context}

    Please analyze the following risk areas:
    1. Legal Risks
       - Regulatory compliance issues
       - Jurisdictional challenges
       - Enforceability concerns

    2. Operational Risks
       - Performance obligations
       - Resource requirements
       - Operational constraints

    3. Financial Risks
       - Payment terms and conditions
       - Financial obligations
       - Currency and tax implications
       - Insurance requirements

    4. Reputational Risks
       - Public relations implications
       - Brand impact considerations
       - Stakeholder concerns

    5. Strategic Risks
       - Long-term implications
       - Market position impact
       - Competitive considerations

    For each identified risk:
    - Rate severity (Low/Medium/High)
    - Assess probability
    - Suggest mitigation strategies
    - Provide specific recommendations

    Your risk assessment:
    """

    COMPLIANCE_CHECK = """
    Perform a comprehensive compliance check of the following contract:

    {context}

    Please evaluate compliance in these areas:
    1. Regulatory Requirements
       - Industry-specific regulations
       - General legal requirements
       - Local and international laws

    2. Data Protection and Privacy
       - Data handling provisions
       - Privacy protection measures
       - Security requirements

    3. Employment and Labor Laws
       - Labor law compliance
       - Employment terms
       - Worker protection measures

    4. Environmental Compliance
       - Environmental regulations
       - Sustainability requirements
       - Environmental protection measures

    5. Industry-Specific Standards
       - Industry regulations
       - Professional standards
       - Best practices compliance

    For each area:
    - Identify compliance requirements
    - Assess current compliance status
    - Note any gaps or violations
    - Suggest required changes

    Your compliance analysis:
    """

    NEGOTIATION_ANALYSIS = """
    Analyze negotiation positions for the following contract:

    {context}

    Please assess:
    1. Key Negotiation Points
       - Critical terms and conditions
       - Price and payment terms
       - Service levels and deliverables
       - Risk allocation provisions

    2. Party Positions
       - Identify each party's interests
       - Analyze bargaining power
       - Assess flexibility points
       - Note deal-breakers

    3. Market Context
       - Industry standards
       - Market conditions
       - Competitive factors
       - Economic considerations

    4. Negotiation Strategy
       - Recommended positions
       - Alternative proposals
       - Fallback options
       - BATNA analysis

    5. Risk-Benefit Analysis
       - Cost-benefit assessment
       - Risk trade-offs
       - Value propositions
       - Long-term implications

    Provide:
    - Specific negotiation recommendations
    - Alternative language suggestions
    - Strategic approach options
    - Priority rankings for terms

    Your negotiation analysis:
    """

class AnalysisQueries:
    """Detailed queries for different analysis types"""
    
    CONTRACT_REVIEW = """
    Review this contract with focus on:
    - Key terms and definitions accuracy
    - Rights and obligations clarity
    - Risk allocation and liability provisions
    - Timeline and performance requirements
    - Termination and remedy provisions
    Provide specific references, quotes, and detailed analysis.
    """

    LEGAL_RESEARCH = """
    Research and analyze:
    - Applicable laws and regulations
    - Relevant case law and precedents
    - Industry-specific regulatory requirements
    - Recent legal developments
    - Compliance obligations
    Provide citations and practical implications.
    """

    RISK_ASSESSMENT = """
    Assess risks in these categories:
    - Legal and regulatory risks
    - Operational and performance risks
    - Financial and commercial risks
    - Reputational and strategic risks
    - Compliance and governance risks
    Rate severity, likelihood, and provide mitigation strategies.
    """

    COMPLIANCE_CHECK = """
    Evaluate compliance with:
    - Industry-specific regulations
    - Data protection and privacy laws
    - Employment and labor requirements
    - Environmental regulations
    - Professional standards
    Identify gaps and recommend necessary changes.
    """

    NEGOTIATION_ANALYSIS = """
    Analyze negotiation aspects:
    - Key terms and conditions
    - Party positions and interests
    - Market context and standards
    - Strategic options and alternatives
    - Risk-benefit trade-offs
    Provide specific recommendations and alternative proposals.
    """

class ContractAnalyzer:
    """Enhanced contract analysis utility"""
    
    # Updated analysis configurations with detailed queries
    ANALYSIS_CONFIGS = {
        AnalysisType.CONTRACT_REVIEW: AnalysisConfig(
            query=AnalysisQueries.CONTRACT_REVIEW,
            agents=["Contract Analyst"],
            required_context=3,
            min_confidence=0.8
        ),
        AnalysisType.LEGAL_RESEARCH: AnalysisConfig(
            query=AnalysisQueries.LEGAL_RESEARCH,
            agents=["Legal Researcher"],
            required_context=5,
            min_confidence=0.85
        ),
        AnalysisType.RISK_ASSESSMENT: AnalysisConfig(
            query=AnalysisQueries.RISK_ASSESSMENT,
            agents=["Contract Analyst", "Legal Strategist"],
            required_context=4,
            min_confidence=0.8
        ),
        AnalysisType.COMPLIANCE_CHECK: AnalysisConfig(
            query=AnalysisQueries.COMPLIANCE_CHECK,
            agents=["Legal Researcher", "Contract Analyst", "Legal Strategist"],
            required_context=4,
            min_confidence=0.9
        ),
        AnalysisType.NEGOTIATION_ANALYSIS: AnalysisConfig(
            query=AnalysisQueries.NEGOTIATION_ANALYSIS,
            agents=["Contract Analyst", "Legal Strategist"],
            required_context=3,
            min_confidence=0.8
        )
    }

    def _create_analysis_prompt(self, context: str, analysis_type: AnalysisType) -> str:
        """Create detailed analysis prompt based on type"""
        template = getattr(PromptTemplates, analysis_type.name, PromptTemplates.CONTRACT_REVIEW)
        return template.format(context=context)


class ContractAnalyzer:
    """Enhanced contract analysis utility"""
    
    # Predefined analysis configurations
    ANALYSIS_CONFIGS = {
        AnalysisType.CONTRACT_REVIEW: AnalysisConfig(
            query="Review this contract and identify key terms, obligations, and potential issues.",
            agents=["Contract Analyst"],
            required_context=3
        ),
        AnalysisType.LEGAL_RESEARCH: AnalysisConfig(
            query="Research relevant cases and precedents related to this document.",
            agents=["Legal Researcher"],
            required_context=5
        ),
        AnalysisType.RISK_ASSESSMENT: AnalysisConfig(
            query="Analyze potential legal risks and liabilities in this document.",
            agents=["Contract Analyst", "Legal Strategist"],
            required_context=4
        ),
        AnalysisType.COMPLIANCE_CHECK: AnalysisConfig(
            query="Check this document for regulatory compliance issues.",
            agents=["Legal Researcher", "Contract Analyst", "Legal Strategist"],
            required_context=4
        ),
        AnalysisType.NEGOTIATION_ANALYSIS: AnalysisConfig(
            query="Analyze negotiation points and suggest strategies.",
            agents=["Contract Analyst", "Legal Strategist"],
            required_context=3
        ),
        AnalysisType.CUSTOM: AnalysisConfig(
            query="",
            agents=["Contract Analyst", "Legal Researcher", "Legal Strategist"],
            required_context=3
        )
    }

    def __init__(self, vector_db: VectorDB):
        """Initialize analyzer"""
        self.vector_db = vector_db
        self.agents = {}
        self.logger = logging.getLogger(__name__)

    def update_agents(self, agents: Dict[str, Any]) -> None:
        """Update available agents"""
        self.agents = agents

    @handle_errors(error_category=ErrorCategory.CONTRACT)
    def analyze_contract(
        self,
        analysis_type: AnalysisType,
        contract_id: str,
        custom_query: Optional[str] = None
    ) -> Optional[AnalysisResult]:
        """
        Perform detailed contract analysis
        
        Args:
            analysis_type: Type of analysis to perform
            contract_id: Contract identifier
            custom_query: Optional custom query
            
        Returns:
            Detailed analysis result if successful
        """
        try:
            # Get configuration and validate
            config = self._get_analysis_config(analysis_type, custom_query)
            if not self._validate_config(config):
                raise ValueError("Invalid analysis configuration")

            # Validate required agents
            if not self._validate_agents(config.agents):
                raise ValueError("Required agents not available")

            # Get context from vector database
            context = self.vector_db.get_context(
                config.query,
                num_results=config.required_context
            )
            if not context:
                raise ValueError("Failed to retrieve context")

            # Create detailed analysis prompt
            prompt = self._create_analysis_prompt(context, analysis_type)
            
            # Get responses from agents with specific focus areas
            results = {}
            for agent_name in config.agents:
                agent = self.agents.get(agent_name)
                if agent:
                    # Customize prompt based on agent role
                    agent_prompt = self._customize_prompt_for_agent(
                        prompt, agent_name, analysis_type
                    )
                    response = agent.run(agent_prompt)
                    if response and response.content:
                        results[agent.name] = response.content
            
            # Create and process result
            result = AnalysisResult(
                analysis_type=analysis_type,
                content=results,
                metadata=self._create_metadata(contract_id),
                timestamp=datetime.now()
            )
            
            # Add comprehensive summary and recommendations
            self._process_detailed_results(result, results)
            
            return result

        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return None

    def _customize_prompt_for_agent(
        self,
        base_prompt: str,
        agent_name: str,
        analysis_type: AnalysisType
    ) -> str:
        """Customize prompt based on agent role"""
        if "Contract Analyst" in agent_name:
            return base_prompt + "\nFocus on contract terms, obligations, and practical implications."
        elif "Legal Researcher" in agent_name:
            return base_prompt + "\nFocus on legal precedents, regulations, and compliance requirements."
        elif "Legal Strategist" in agent_name:
            return base_prompt + "\nFocus on strategic implications, risks, and recommendations."
        return base_prompt

    def _process_detailed_results(
        self,
        result: AnalysisResult,
        agent_results: Dict[str, str]
    ) -> None:
        """Process results with detailed analysis"""
        try:
            # Generate comprehensive summary
            summary_agent = self.agents.get("Legal Strategist") or next(iter(self.agents.values()))
            
            # Create detailed summary prompt
            summary_prompt = f"""
            Create a comprehensive summary of the following analysis results:
            {agent_results}
            
            Please include:
            1. Key findings and insights
            2. Critical issues identified
            3. Risk assessment overview
            4. Compliance considerations
            5. Strategic implications
            
            Format as a detailed executive summary.
            """
            
            summary_response = summary_agent.run(summary_prompt)
            if summary_response:
                result.add_summary(summary_response.content)
            
            # Generate actionable recommendations
            rec_prompt = f"""
            Based on the following analysis:
            {agent_results}
            
            Provide specific, actionable recommendations for:
            1. Immediate actions required
            2. Risk mitigation steps
            3. Compliance improvements
            4. Strategic considerations
            5. Long-term planning
            
            Format as clear, prioritized action items.
            """
            
            rec_response = summary_agent.run(rec_prompt)
            if rec_response:
                recommendations = [
                    rec.strip()
                    for rec in rec_response.content.split('\n')
                    if rec.strip()
                ]
                for rec in recommendations:
                    result.add_recommendation(rec)
                    
        except Exception as e:
            self.logger.error(f"Result processing failed: {str(e)}")
        
        
    def batch_analyze(
        self,
        contracts: List[str],
        analysis_type: AnalysisType,
        custom_query: Optional[str] = None
    ) -> List[Optional[AnalysisResult]]:
        """
        Analyze multiple contracts
        
        Args:
            contracts: List of contract IDs
            analysis_type: Type of analysis
            custom_query: Optional custom query
            
        Returns:
            List of analysis results
        """
        results = []
        for contract_id in contracts:
            try:
                result = self.analyze_contract(
                    analysis_type,
                    contract_id,
                    custom_query
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch analysis failed for {contract_id}: {str(e)}")
                results.append(None)
        return results

    def get_analysis_summary(
        self,
        analysis_type: AnalysisType,
        results: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Generate analysis summary
        
        Args:
            analysis_type: Type of analysis
            results: Analysis results
            
        Returns:
            Summary and recommendations
        """
        try:
            combined_text = ""
            for agent_name, content in results.items():
                combined_text += f"\n{agent_name}:\n{content}"

            summary_agent = self.agents.get("Legal Strategist") or next(iter(self.agents.values()))
            
            # Generate summary
            summary_response = summary_agent.run(
                f"Provide a concise summary of this analysis:\n{combined_text}"
            )
            summary = summary_response.content if summary_response else ""

            # Generate recommendations
            rec_response = summary_agent.run(
                f"Provide specific recommendations based on this analysis:\n{combined_text}"
            )
            recommendations = (
                rec_response.content.split('\n')
                if rec_response and rec_response.content
                else []
            )

            return summary, recommendations

        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return "", []

    def _get_analysis_config(
        self,
        analysis_type: AnalysisType,
        custom_query: Optional[str] = None
    ) -> AnalysisConfig:
        """Get analysis configuration"""
        config = self.ANALYSIS_CONFIGS[analysis_type]
        if analysis_type == AnalysisType.CUSTOM and custom_query:
            config.query = custom_query
        return config

    def _validate_agents(self, required_agents: List[str]) -> bool:
        """Validate required agents are available"""
        return all(agent in self.agents for agent in required_agents)

    def _validate_config(self, config: AnalysisConfig) -> bool:
        """Validate analysis configuration"""
        return bool(
            config.query and
            config.agents and
            config.required_context > 0 and
            0 < config.min_confidence <= 1
        )

    @staticmethod
    def _create_analysis_prompt(context: str, query: str) -> str:
        """Create analysis prompt"""
        return f"""Analyze the following legal document:

Context:
{context}

Query:
{query}

Instructions:
1. Review the provided context thoroughly
2. Address the specific query/task
3. Include relevant quotes or references
4. Provide clear, actionable insights
5. Highlight important findings

Analysis:"""

    def _get_agent_responses(
        self,
        prompt: str,
        agent_names: List[str]
    ) -> Dict[str, str]:
        """Get responses from specified agents"""
        results = {}
        for agent_name in agent_names:
            if agent := self.agents.get(agent_name):
                try:
                    response = agent.run(prompt)
                    if response and response.content:
                        results[agent.name] = response.content
                    else:
                        self.logger.warning(f"Empty response from agent {agent_name}")
                except Exception as e:
                    self.logger.error(f"Agent {agent_name} failed: {str(e)}")
        return results

    def _create_metadata(self, contract_id: str) -> Dict[str, Any]:
        """Create analysis metadata"""
        return {
            'contract_id': contract_id,
            'timestamp': datetime.now().isoformat(),
            'agents': list(self.agents.keys()),
            'version': '2.0'
        }

    def _process_results(
        self,
        result: AnalysisResult,
        agent_results: Dict[str, str]
    ) -> None:
        """Process and enhance analysis results"""
        try:
            summary, recommendations = self.get_analysis_summary(
                result.analysis_type,
                agent_results
            )
            result.add_summary(summary)
            for rec in recommendations:
                result.add_recommendation(rec)
        except Exception as e:
            self.logger.error(f"Result processing failed: {str(e)}")

class DocumentValidator:
    """Validate document content and structure"""
    
    @staticmethod
    def validate_content(content: str) -> Tuple[bool, List[str]]:
        """
        Validate document content
        
        Args:
            content: Document content to validate
            
        Returns:
            Validation status and issues
        """
        issues = []
        
        # Basic content checks
        if not content.strip():
            issues.append("Empty document content")
            return False, issues
            
        # Length check
        if len(content.split()) < 50:
            issues.append("Document content too short")
            
        # Structure checks
        if not DocumentValidator._has_valid_structure(content):
            issues.append("Invalid document structure")
            
        # Section checks
        if not DocumentValidator._has_required_sections(content):
            issues.append("Missing required sections")
            
        return not bool(issues), issues

    @staticmethod
    def _has_valid_structure(content: str) -> bool:
        """Check document structure"""
        lines = content.splitlines()
        has_header = False
        has_body = False
        has_sections = False
        
        for line in lines:
            if line.isupper() and len(line.split()) <= 5:
                has_header = True
            elif len(line.strip()) > 0:
                has_body = True
            if line.strip().startswith(('Section', 'SECTION', 'Article', 'ARTICLE')):
                has_sections = True
                
        return has_header and has_body and has_sections

    @staticmethod
    def _has_required_sections(content: str) -> bool:
        """Check for required sections"""
        required_sections = {
            'parties',
            'terms',
            'conditions',
            'agreement',
            'signature'
        }
        
        content_lower = content.lower()
        return any(
            section in content_lower
            for section in required_sections
        )