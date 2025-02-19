# agents/templates/custom.py
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalysisCategory(Enum):
    """Categories for custom analysis"""

    LEGAL = "legal"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    CUSTOM = "custom"


@dataclass
class CustomRequirement:
    """Dynamic requirements for custom agent"""

    min_confidence: float
    required_skills: Set[str]
    analysis_categories: List[AnalysisCategory]
    context_requirements: Dict[str, Any]
    specialized_knowledge: List[str]
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


class CustomAgentTemplate:
    def __init__(self):
        self.query_patterns = self._init_query_patterns()
        self.question_patterns = {
            r"\bwhat\b|\bhow\b|\bwhen\b|\bwhere\b|\bwhy\b|\bwho\b|\bwhich\b": "question",
            r"\?$": "question",
            r"^(can|could|would|should|is|are|do|does|did|has|have)": "question",
        }
        self.skill_mappings = self._init_skill_mappings()
        self.logger = logging.getLogger(__name__)

    def _init_query_patterns(self) -> Dict[str, List[str]]:
        """Initialize query pattern recognition"""
        return {
            "legal_analysis": [
                r"legal\s+analysis",
                r"law\s+review",
                r"regulatory",
                r"compliance",
                r"jurisdiction",
            ],
            "technical_review": [
                r"technical\s+review",
                r"specification",
                r"technology",
                r"implementation",
                r"system",
            ],
            "financial_assessment": [
                r"financial",
                r"cost",
                r"budget",
                r"pricing",
                r"payment",
            ],
            "risk_analysis": [
                r"risk",
                r"liability",
                r"exposure",
                r"mitigation",
                r"protection",
            ],
            "contract_review": [
                r"contract",
                r"agreement",
                r"terms",
                r"clause",
                r"provision",
            ],
        }

    def _init_skill_mappings(self) -> Dict[str, Set[str]]:
        """Initialize skill requirement mappings"""
        return {
            "legal_analysis": {
                "legal_research",
                "regulatory_analysis",
                "compliance_review",
                "case_law_analysis",
            },
            "technical_review": {
                "technical_assessment",
                "specification_review",
                "implementation_analysis",
                "system_evaluation",
            },
            "financial_assessment": {
                "financial_analysis",
                "cost_evaluation",
                "pricing_review",
                "budget_assessment",
            },
            "risk_analysis": {
                "risk_assessment",
                "liability_analysis",
                "mitigation_planning",
                "protection_review",
            },
            "contract_review": {
                "contract_analysis",
                "term_review",
                "provision_assessment",
                "agreement_evaluation",
            },
        }

    def analyze_query(self, query: str) -> Dict[str, float]:
        """
        Analyze query to determine required capabilities

        Args:
            query: User query string

        Returns:
            Dictionary of capability scores
        """
        scores = defaultdict(float)

        for category, patterns in self.query_patterns.items():
            category_score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query.lower()))
                if matches > 0:
                    category_score += matches * 0.2  # 20% per match
            scores[category] = min(category_score, 1.0)  # Cap at 1.0

        return dict(scores)

    def _is_direct_question(self, query: str) -> bool:
        query = query.lower().strip()
        return any(re.search(pattern, query) for pattern in self.question_patterns)

    def determine_requirements(
        self, query: str, additional_context: Optional[Dict[str, Any]] = None
    ) -> CustomRequirement:
        # Check if query is a direct question
        is_question = self._is_direct_question(query)

        if is_question:
            return CustomRequirement(
                min_confidence=0.7,
                required_skills={"question_answering"},
                analysis_categories=[AnalysisCategory.CUSTOM],
                context_requirements={"min_context_length": 100},
                specialized_knowledge=["direct_response"],
                custom_parameters={"response_type": "direct_answer"},
            )

        # Original analysis logic for non-questions
        capability_scores = self.analyze_query(query)
        required_skills = set()
        analysis_categories = []

        for category, score in capability_scores.items():
            if score > 0.2:
                if category in self.skill_mappings:
                    required_skills.update(self.skill_mappings[category])
                try:
                    analysis_categories.append(
                        AnalysisCategory[category.split("_")[0].upper()]
                    )
                except KeyError:
                    analysis_categories.append(AnalysisCategory.CUSTOM)

        min_confidence = 0.7
        if len(required_skills) > 5:
            min_confidence = 0.8
        if len(required_skills) > 8:
            min_confidence = 0.9

        return CustomRequirement(
            min_confidence=min_confidence,
            required_skills=required_skills,
            analysis_categories=analysis_categories,
            context_requirements=self._determine_context_requirements(
                capability_scores
            ),
            specialized_knowledge=self._determine_specialized_knowledge(query),
            custom_parameters=additional_context or {},
        )

    def create_custom_prompt(
        self, query: str, requirements: CustomRequirement, context: str
    ) -> str:
        # Check if this is a direct question
        if "question_answering" in requirements.required_skills:
            return f"""Answer this question directly and concisely based on the provided context:

Question: {query}

Context:
{context}

Please provide a clear, direct answer without analysis or additional explanations unless necessary for clarity."""

        # Original analysis prompt for non-questions
        return f"""Analyze the following based on specific requirements:

Context:
{context}

Query:
{query}

Required Analysis Categories:
{chr(10).join(f'- {cat.value}' for cat in requirements.analysis_categories)}

Required Skills:
{chr(10).join(f'- {skill}' for skill in requirements.required_skills)}

Analysis Instructions:
1. Focused Analysis
   - Address the specific query
   - Cover all required categories
   - Apply specified skills
   - Maintain minimum confidence of {requirements.min_confidence}

2. Required Elements
   - Specific analysis for each category
   - Evidence-based conclusions
   - Clear recommendations
   - Actionable insights

3. Special Considerations
   {chr(10).join(f'   - {item}' for item in requirements.specialized_knowledge)}

Please provide:
- Detailed analysis for each category
- Specific evidence and justification
- Clear conclusions
- Actionable recommendations
"""

    def _determine_context_requirements(
        self, capability_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Determine context requirements based on capabilities"""
        requirements = {
            "min_context_length": 1000,  # Base requirement
            "required_elements": set(),
            "optional_elements": set(),
        }

        # Adjust based on capabilities
        for category, score in capability_scores.items():
            if score > 0.5:
                requirements["min_context_length"] += 500
                if category in self.skill_mappings:
                    requirements["required_elements"].update(
                        [skill.split("_")[0] for skill in self.skill_mappings[category]]
                    )

        return requirements

    def _determine_specialized_knowledge(self, query: str) -> List[str]:
        """Determine specialized knowledge requirements"""
        specialized = []

        # Add specialized knowledge based on query content
        knowledge_patterns = {
            r"technical": "Technical domain expertise required",
            r"legal": "Legal domain knowledge required",
            r"financial": "Financial analysis expertise required",
            r"regulation|compliance": "Regulatory compliance knowledge required",
            r"industry|sector": "Industry-specific knowledge required",
        }

        for pattern, requirement in knowledge_patterns.items():
            if re.search(pattern, query.lower()):
                specialized.append(requirement)

        return specialized

    def validate_capabilities(
        self, requirements: CustomRequirement, available_capabilities: Set[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if available capabilities meet requirements

        Args:
            requirements: Determined requirements
            available_capabilities: Available capabilities

        Returns:
            Tuple of (is_valid, missing_capabilities)
        """
        missing = []

        # Check required skills
        missing_skills = requirements.required_skills - available_capabilities
        if missing_skills:
            missing.append(f"Missing required skills: {', '.join(missing_skills)}")

        # Check specialized knowledge
        for knowledge in requirements.specialized_knowledge:
            knowledge_capability = f"knowledge_{knowledge.split()[0].lower()}"
            if knowledge_capability not in available_capabilities:
                missing.append(f"Missing specialized knowledge: {knowledge}")

        return len(missing) == 0, missing

    def get_metadata(self, requirements: CustomRequirement) -> Dict[str, Any]:
        """Get template metadata"""
        return {
            "type": "custom_agent",
            "created_at": datetime.now().isoformat(),
            "requirements": {
                "min_confidence": requirements.min_confidence,
                "required_skills": list(requirements.required_skills),
                "analysis_categories": [
                    cat.value for cat in requirements.analysis_categories
                ],
                "specialized_knowledge": requirements.specialized_knowledge,
            },
        }
