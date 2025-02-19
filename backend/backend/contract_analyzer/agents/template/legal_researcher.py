# agents/templates/legal_researcher.py
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class ResearchScope(Enum):
    """Research scope levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXPERT = "expert"

class ResearchDomain(Enum):
    """Legal research domains"""
    CONTRACT_LAW = "contract_law"
    CORPORATE_LAW = "corporate_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    EMPLOYMENT_LAW = "employment_law"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    INTERNATIONAL_LAW = "international_law"

@dataclass
class ResearchRequirement:
    """Requirements for legal research"""
    min_source_count: int
    min_confidence: float
    required_analysis: List[str]
    required_jurisdictions: List[str]
    time_scope_years: int

class LegalResearcherTemplate:
    """Template for Legal Researcher agent"""
    
    # Base configuration
    NAME = "Legal Researcher"
    ROLE = "legal_research"
    VERSION = "2.0"
    
    # Core capabilities
    CAPABILITIES = [
        "legal_research",
        "precedent_analysis",
        "regulatory_review",
        "compliance_assessment",
        "jurisdictional_analysis",
        "case_law_research"
    ]
    
    # Research requirements by scope
    REQUIREMENTS = {
        ResearchScope.BASIC: ResearchRequirement(
            min_source_count=3,
            min_confidence=0.7,
            required_analysis=[
                "relevant_laws",
                "key_regulations",
                "basic_precedents"
            ],
            required_jurisdictions=["primary_jurisdiction"],
            time_scope_years=5
        ),
        ResearchScope.STANDARD: ResearchRequirement(
            min_source_count=5,
            min_confidence=0.8,
            required_analysis=[
                "relevant_laws",
                "key_regulations",
                "precedents",
                "regulatory_guidance",
                "compliance_requirements"
            ],
            required_jurisdictions=["primary_jurisdiction", "related_jurisdictions"],
            time_scope_years=7
        ),
        ResearchScope.COMPREHENSIVE: ResearchRequirement(
            min_source_count=10,
            min_confidence=0.9,
            required_analysis=[
                "relevant_laws",
                "key_regulations",
                "precedents",
                "regulatory_guidance",
                "compliance_requirements",
                "legal_trends",
                "industry_standards",
                "enforcement_actions"
            ],
            required_jurisdictions=["primary_jurisdiction", "related_jurisdictions", "international"],
            time_scope_years=10
        ),
        ResearchScope.EXPERT: ResearchRequirement(
            min_source_count=15,
            min_confidence=0.95,
            required_analysis=[
                "relevant_laws",
                "key_regulations",
                "precedents",
                "regulatory_guidance",
                "compliance_requirements",
                "legal_trends",
                "industry_standards",
                "enforcement_actions",
                "academic_analysis",
                "policy_implications",
                "future_developments"
            ],
            required_jurisdictions=["primary_jurisdiction", "related_jurisdictions", "international", "emerging_markets"],
            time_scope_years=15
        )
    }
    
    @classmethod
    def get_base_instructions(cls) -> List[str]:
        """Get base instructions for the researcher"""
        return [
            "Conduct thorough legal research on relevant topics",
            "Analyze applicable laws and regulations",
            "Review relevant case law and precedents",
            "Assess compliance requirements and standards",
            "Provide clear legal analysis and recommendations"
        ]
    
    @classmethod
    def get_domain_instructions(cls, domain: ResearchDomain) -> List[str]:
        """Get domain-specific research instructions"""
        domain_instructions = {
            ResearchDomain.CONTRACT_LAW: [
                "Research contract formation and enforcement",
                "Analyze breach and remedies precedents",
                "Review contract interpretation principles",
                "Assess standard contractual provisions",
                "Research recent contract law developments"
            ],
            ResearchDomain.INTELLECTUAL_PROPERTY: [
                "Research IP protection and enforcement",
                "Analyze patent and trademark precedents",
                "Review licensing and transfer requirements",
                "Assess IP rights and restrictions",
                "Research technology law developments"
            ],
            ResearchDomain.EMPLOYMENT_LAW: [
                "Research employment rights and obligations",
                "Analyze workplace law compliance",
                "Review labor law requirements",
                "Assess employment contract standards",
                "Research worker protection regulations"
            ]
        }
        return domain_instructions.get(domain, cls.get_base_instructions())

    @classmethod
    def create_research_prompt(cls, context: str, scope: ResearchScope, domain: ResearchDomain) -> str:
        """Create research prompt based on scope and domain"""
        requirements = cls.REQUIREMENTS[scope]
        
        prompt = f"""Conduct {scope.value} legal research for the following in {domain.value}:

{context}

Research Requirements:
1. Legal Framework Analysis
   - Identify applicable laws and regulations
   - Review relevant jurisdictions: {', '.join(requirements.required_jurisdictions)}
   - Analyze regulatory framework
   - Assess compliance requirements

2. Case Law Research
   - Find relevant precedents (minimum {requirements.min_source_count} sources)
   - Analyze court interpretations
   - Review enforcement actions
   - Identify legal principles

3. Required Analysis Areas
   {chr(10).join(f'   - {item}' for item in requirements.required_analysis)}

4. Time Scope
   - Focus on developments within past {requirements.time_scope_years} years
   - Note any significant historical precedents
   - Identify emerging trends

5. Deliverables
   - Comprehensive legal analysis
   - Relevant citations and references
   - Practical implications
   - Specific recommendations

Please provide:
- Detailed analysis for each required area
- Specific legal citations and references
- Clear explanations of implications
- Actionable recommendations
"""
        return prompt

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
                scope.value: {
                    "min_sources": req.min_source_count,
                    "min_confidence": req.min_confidence,
                    "required_analysis": req.required_analysis
                }
                for scope, req in cls.REQUIREMENTS.items()
            }
        }

    @classmethod
    def validate_research_requirements(
        cls,
        scope: ResearchScope,
        source_count: int,
        confidence: float,
        covered_areas: List[str],
        jurisdictions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if research requirements are met
        
        Args:
            scope: Research scope
            source_count: Number of sources used
            confidence: Confidence score
            covered_areas: Areas covered in analysis
            jurisdictions: Jurisdictions covered
            
        Returns:
            Tuple of (is_valid, missing_requirements)
        """
        requirements = cls.REQUIREMENTS[scope]
        missing = []

        if source_count < requirements.min_source_count:
            missing.append(f"Insufficient sources: {source_count}/{requirements.min_source_count}")

        if confidence < requirements.min_confidence:
            missing.append(f"Confidence below minimum: {confidence}/{requirements.min_confidence}")

        missing_areas = set(requirements.required_analysis) - set(covered_areas)
        if missing_areas:
            missing.append(f"Missing analysis areas: {', '.join(missing_areas)}")

        missing_jurisdictions = set(requirements.required_jurisdictions) - set(jurisdictions)
        if missing_jurisdictions:
            missing.append(f"Missing jurisdictions: {', '.join(missing_jurisdictions)}")

        return len(missing) == 0, missing

    @classmethod
    def get_specialized_instructions(cls, specialization: str) -> List[str]:
        """Get specialized research instructions"""
        specialized_instructions = {
            "regulatory": [
                "Focus on regulatory compliance requirements",
                "Review recent regulatory changes",
                "Analyze enforcement patterns",
                "Assess reporting obligations",
                "Evaluate compliance frameworks"
            ],
            "litigation": [
                "Focus on litigation precedents",
                "Analyze court decisions",
                "Review procedural requirements",
                "Assess evidence standards",
                "Evaluate litigation strategies"
            ],
            "transactional": [
                "Focus on transaction structures",
                "Analyze deal precedents",
                "Review regulatory approvals",
                "Assess documentation requirements",
                "Evaluate market standards"
            ]
        }
        return specialized_instructions.get(specialization, cls.get_base_instructions())