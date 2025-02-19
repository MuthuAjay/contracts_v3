# agents/templates/contract_analyst.py
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class AnalysisScope(Enum):
    """Analysis scope for contract analyst"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

@dataclass
class AnalysisRequirement:
    """Requirements for contract analysis"""
    min_context_length: int
    min_confidence: float
    required_sections: List[str]
    optional_sections: List[str]

class ContractAnalystTemplate:
    """Template for Contract Analyst agent"""

    # Base configuration
    NAME = "Contract Analyst"
    ROLE = "contract_analysis"
    VERSION = "2.0"

    # Core capabilities
    CAPABILITIES = [
        "contract_review",
        "term_analysis",
        "risk_identification",
        "obligation_assessment",
        "compliance_check"
    ]

    # Analysis requirements by scope
    REQUIREMENTS = {
        AnalysisScope.BASIC: AnalysisRequirement(
            min_context_length=1000,
            min_confidence=0.7,
            required_sections=[
                "parties",
                "terms",
                "signatures"
            ],
            optional_sections=[
                "definitions",
                "exhibits"
            ]
        ),
        AnalysisScope.DETAILED: AnalysisRequirement(
            min_context_length=2000,
            min_confidence=0.8,
            required_sections=[
                "parties",
                "definitions",
                "terms",
                "conditions",
                "obligations",
                "termination",
                "signatures"
            ],
            optional_sections=[
                "recitals",
                "exhibits",
                "schedules"
            ]
        ),
        AnalysisScope.COMPREHENSIVE: AnalysisRequirement(
            min_context_length=3000,
            min_confidence=0.9,
            required_sections=[
                "parties",
                "recitals",
                "definitions",
                "terms",
                "conditions",
                "obligations",
                "representations",
                "warranties",
                "indemnification",
                "termination",
                "governing_law",
                "signatures"
            ],
            optional_sections=[
                "exhibits",
                "schedules",
                "amendments"
            ]
        )
    }

    @classmethod
    def get_context_prompt(cls) -> str:
        """Get prompt for context extraction"""
        return f"""Extract the context of the following contract:
        Intellectual Property and Confidentiality
        - IP ownership and rights
        - License grants and restrictions
        - Confidentiality obligations
        - Rights, Obligations, and Deliverables
        - Core obligations of each party
        - Specific deliverables and requirements
        - Termination clauses
        - Governing law and Arbitration        
        """

    @classmethod
    def create_analysis_prompt(cls, context: str, scope: AnalysisScope) -> str:
        """Create comprehensive analysis prompt based on scope"""
        requirements = cls.REQUIREMENTS[scope]
        
        prompt = f"""Analyze the following contract comprehensively and extract all critical information:

    {context}

   
    Please provide:
    - Detailed analysis of each section with specific clause references
    - Exact quotes of critical language
    - Clear explanations of implications and concerns
    - Specific recommendations for improvements or clarifications
    - Risk ratings for significant issues (High/Medium/Low)
    - Cross-references between related provisions
    - Practical impact assessment for key terms
    - Strategic recommendations for negotiation or implementation

    Format the analysis with clear headers, bullet points, and systematic organization.
    Include specific section references and page numbers where applicable.
    Flag any missing or inadequate provisions that should be addressed.
    Highlight unusual or particularly favorable/unfavorable terms.
    Provide context for industry standards or typical market terms where relevant.
    And also explain two or three lines if necessary 
    
    """
        return prompt

    @classmethod
    def extract_key_terms(cls, context: str) -> str:
        """Create prompt for extracting key defined terms"""
        return f"""Review the following contract and extract all key defined terms:

    {context}

    For each defined term:
    1. Extract the exact definition
    2. Identify where it's used in the contract
    3. Analyze the scope and implications
    4. Flag any ambiguities or issues
    5. Compare to standard industry definitions
    6. Note any unusual or concerning aspects
    7. Suggest improvements if needed

    Focus on terms that:
    - Are critical to contract interpretation
    - Have financial implications
    - Affect rights and obligations
    - Impact risk allocation
    - Influence performance requirements
    - Relate to compliance obligations

    Provide analysis in a structured format with clear references and recommendations."""

    @classmethod
    def analyze_obligations(cls, context: str) -> str:
        """Create prompt for analyzing obligations"""
        return f"""Analyze all obligations in the following contract:

    {context}

    For each party, identify:
    1. Core Obligations
    - Primary performance requirements
    - Delivery obligations
    - Payment obligations
    - Service requirements
    - Quality standards
    - Timeline commitments

    2. Conditional Obligations
    - Prerequisites and conditions
    - Dependencies on other parties
    - External conditions or triggers
    - Optional obligations
    - Alternative obligations

    3. Compliance Obligations
    - Regulatory requirements
    - Reporting obligations
    - Record-keeping requirements
    - Audit obligations
    - Certification requirements

    4. Support Obligations
    - Cooperation requirements
    - Resource commitments
    - Personnel requirements
    - Access and availability
    - Training or support obligations

    Flag any obligations that are:
    - Unclear or ambiguous
    - Potentially unreasonable
    - Missing key details
    - Difficult to measure or enforce
    - Potentially conflicting
    - High risk or critical path"""
        
    @classmethod
    def create_party_extraction_prompt(cls, context: str) -> str:
        """Create prompt for extracting party and agreement information"""
        return f"""Extract key agreement and party information from the following contract text:

    {context}

    Please identify and extract:

    1. Agreement Metadata
    - Agreement date
    - Agreement type/title
    - Document reference numbers (if any)
    - Governing jurisdiction/law (if mentioned)

    2. Party Information (for each party)
    - Full legal name
    - Type of entity (e.g., corporation, LLC, etc.)
    - Registration/incorporation details
    - Principal address/location, or where it established
    - Role in agreement (if specified)
    - Any defined terms/aliases used

    3. Party Relationships
    - How parties are collectively referred to
    - Individual party references/definitions
    - Any specified hierarchies or relationships
    - Group definitions or collective terms used

    4. Additional Identifiers
    - Any registration numbers
    - Tax IDs or business numbers
    - Branch/subsidiary relationships
    - Trading names or aliases

    Format the output as:
    Agreement Details
    - Date: [date]
    - Type: [type]
    - Reference: [reference numbers if any]
    Party 1
    - Name: [full legal name]
    - Entity Type: [type]
    - Location: [address]
    - Role: [role]
    - Defined As: [defined term]
    Party 2
    [Same structure as Party 1]
    Collective References
    - Parties collectively known as: [collective term]
    - Individual references: [individual terms]

    Just Give the Output in the above format Do not write anything else
    Make sure the output is clear and structured for easy reference and analysis
    List all information exactly as stated in the document.
    Include any specific language or defined terms used.
    Note any missing or unclear information.
    """