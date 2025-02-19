from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RiskCategory(Enum):
    """Categories of contract risks"""
    LEGAL = "legal"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    STRATEGIC = "strategic"

@dataclass
class RiskRequirement:
    """Requirements for risk assessment"""
    min_context_length: int
    min_confidence: float
    required_categories: List[str]
    min_risks_per_category: int
    include_mitigation: bool
    include_probability: bool

class RiskAssessmentTemplate:
    """Template for Risk Assessment agent"""

    NAME = "Risk Assessor"
    ROLE = "risk_assessment"
    VERSION = "2.0"

    CAPABILITIES = [
        "risk_identification",
        "impact_analysis",
        "probability_assessment",
        "mitigation_planning",
        "compliance_evaluation",
        "financial_risk_analysis"
    ]

    REQUIREMENTS = {
        RiskLevel.LOW: RiskRequirement(
            min_context_length=1000,
            min_confidence=0.7,
            required_categories=["legal", "financial"],
            min_risks_per_category=2,
            include_mitigation=False,
            include_probability=False
        ),
        RiskLevel.MEDIUM: RiskRequirement(
            min_context_length=2000,
            min_confidence=0.8,
            required_categories=["legal", "financial", "operational", "compliance"],
            min_risks_per_category=3,
            include_mitigation=True,
            include_probability=True
        ),
        RiskLevel.HIGH: RiskRequirement(
            min_context_length=3000,
            min_confidence=0.9,
            required_categories=["legal", "financial", "operational", "compliance", "reputational"],
            min_risks_per_category=4,
            include_mitigation=True,
            include_probability=True
        ),
        RiskLevel.CRITICAL: RiskRequirement(
            min_context_length=4000,
            min_confidence=0.95,
            required_categories=["legal", "financial", "operational", "compliance", "reputational", "strategic"],
            min_risks_per_category=5,
            include_mitigation=True,
            include_probability=True
        )
    }

    @classmethod
    def create_assessment_prompt(cls, context: str, risk_level: RiskLevel) -> str:
        """Create risk assessment prompt based on level"""
        requirements = cls.REQUIREMENTS[risk_level]
        
        prompt = f"""Conduct a {risk_level.value} risk assessment of the following contract:

{context}

Required Analysis Categories:
{chr(10).join(f'- {cat.upper()} RISKS' for cat in requirements.required_categories)}

For each category, identify minimum {requirements.min_risks_per_category} risks and analyze:
1. Risk Description and Impact
   - Clear description of the risk
   - Potential impact on organization
   - Severity assessment
   
2. Risk Evaluation
   - Likelihood of occurrence
   - Impact magnitude
   - Overall risk rating

3. Contributing Factors
   - Key triggers and warning signs
   - Environmental factors
   - Dependencies and relationships

4. Financial Implications
   - Potential monetary impact
   - Associated costs
   - Financial exposure"""

        if requirements.include_mitigation:
            prompt += """

5. Mitigation Strategies
   - Preventive measures
   - Detective controls
   - Corrective actions
   - Implementation timeline
   - Resource requirements"""

        if requirements.include_probability:
            prompt += """

6. Probability Assessment
   - Quantitative analysis
   - Historical precedents
   - Industry benchmarks
   - Confidence intervals"""

        prompt += """

Provide:
- Detailed analysis for each risk
- Clear severity ratings
- Specific examples and references
- Actionable recommendations"""

        return prompt

    @classmethod
    def get_risk_prompt(cls, context: str, category: RiskCategory) -> str:
        """Get category-specific risk prompt"""
        prompts = {
            RiskCategory.LEGAL: """
Analyze legal risks including:
- Contractual obligations and liabilities
- Regulatory compliance issues
- Intellectual property risks
- Dispute resolution exposure
- Jurisdiction and venue concerns""",

            RiskCategory.FINANCIAL: """
Analyze financial risks including:
- Payment and credit risks
- Currency and market risks
- Revenue and profitability impact
- Cost overrun potential
- Financial reporting implications""",

            RiskCategory.OPERATIONAL: """
Analyze operational risks including:
- Performance and delivery risks
- Resource and capacity issues
- Quality control concerns
- Process efficiency impacts
- Operational disruptions""",

            RiskCategory.COMPLIANCE: """
Analyze compliance risks including:
- Regulatory requirements
- Industry standards
- Data protection obligations
- Reporting requirements
- Audit considerations""",

            RiskCategory.REPUTATIONAL: """
Analyze reputational risks including:
- Brand impact potential
- Stakeholder perception
- Media exposure
- Public relations implications
- Market position effects""",

            RiskCategory.STRATEGIC: """
Analyze strategic risks including:
- Market position impact
- Competitive advantage effects
- Growth opportunity costs
- Strategic alignment issues
- Long-term viability concerns"""
        }
        
        return f"""Analyze the following contract for {category.value} risks:

{context}

{prompts[category]}

Provide:
- Specific risk identification
- Impact assessment
- Mitigation recommendations
- Priority rating
"""

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get template metadata"""
        return {
            "name": cls.NAME,
            "role": cls.ROLE,
            "version": cls.VERSION,
            "capabilities": cls.CAPABILITIES,
            "created_at": datetime.now().isoformat(),
            "requirements": {
                level.value: {
                    "min_context_length": req.min_context_length,
                    "min_confidence": req.min_confidence,
                    "required_categories": req.required_categories
                }
                for level, req in cls.REQUIREMENTS.items()
            }
        }

    @classmethod
    def validate_assessment(
        cls,
        risk_level: RiskLevel,
        context_length: int,
        confidence: float,
        categories_covered: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate if assessment meets requirements"""
        requirements = cls.REQUIREMENTS[risk_level]
        missing = []

        if context_length < requirements.min_context_length:
            missing.append(f"Context length below minimum: {requirements.min_context_length}")

        if confidence < requirements.min_confidence:
            missing.append(f"Confidence below minimum: {requirements.min_confidence}")

        missing_categories = set(requirements.required_categories) - set(categories_covered)
        if missing_categories:
            missing.append(f"Missing required categories: {', '.join(missing_categories)}")

        return len(missing) == 0, missing

    @classmethod
    def get_specialized_instructions(cls, specialization: str) -> List[str]:
        """Get specialized risk assessment instructions"""
        specialized = {
            "technology": [
                "Focus on technology implementation risks",
                "Assess cybersecurity exposures",
                "Evaluate system integration risks",
                "Analyze data protection concerns",
                "Review technical compliance requirements"
            ],
            "financial": [
                "Focus on financial exposure analysis",
                "Assess market and currency risks",
                "Evaluate credit and payment risks",
                "Analyze revenue impact potential",
                "Review financial compliance obligations"
            ],
            "regulatory": [
                "Focus on regulatory compliance risks",
                "Assess reporting requirements",
                "Evaluate audit implications",
                "Analyze regulatory change impact",
                "Review compliance monitoring needs"
            ]
        }
        return specialized.get(specialization, [])