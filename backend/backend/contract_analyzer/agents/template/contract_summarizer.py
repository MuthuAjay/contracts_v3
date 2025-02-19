# agents/templates/contract_summary.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class SummarySection(Enum):
   OVERVIEW = "overview"
   OBLIGATIONS = "obligations"  
   DEADLINES = "deadlines"
   PENALTIES = "penalties"
   ADDITIONAL = "additional"

@dataclass
class SummaryRequirement:
   extract_parties: bool = True
   extract_dates: bool = True 
   extract_values: bool = True
   extract_obligations: bool = True
   extract_penalties: bool = True
   min_content_length: int = 100
   include_references: bool = True

class ContractSummaryTemplate:
   NAME = "Contract Summary"
   ROLE = "summary_generation"
   VERSION = "1.0"
   
   CAPABILITIES = [
       "entity_extraction",
       "date_extraction", 
       "obligation_analysis",
       "value_extraction",
       "penalty_identification",
       "timeline_analysis"
   ]

   @classmethod
   def create_summary_prompt(cls, context: str) -> str:
       return f"""Analyze and extract key information from the contract below:

{context}

Please identify and extract:

1. Overview Information
- Contracting parties or entities or individuals or groups or companies or Industries
- Effective date and duration  
- Subject matter/purpose
- Contract value
- Governing law

2. Key Obligations
- Core obligations for each party
- Deliverables and requirements
- Conditions and dependencies
- Specific quantities/specifications

3. Important Dates & Deadlines
- Delivery schedules
- Payment timelines 
- Milestones
- Notice periods

4. Penalties & Consequences
- Late delivery penalties
- Payment penalties
- Breach consequences
- Termination penalties

5. Additional Important Terms
- Termination conditions
- Confidentiality requirements
- Other significant clauses

6. Transaction Values
- Payment amounts
- Transaction values
- Currency details
- Payment terms
- Amount paid or received
- Payment methods
- Dollar amounts

Format the output in clear Markdown:
- Use headers and bullet points
- Bold key terms and values
- Include specific numbers and dates
- Group related items logically

Only include key terms and significant details.
Summarize in a structured, easy-to-scan format.
"""

   @classmethod
   def extract_details_prompt(cls, context: str, section: str) -> str:
       prompts = {
           "parties": f"""Identify the contracting parties in this contract.
           
           {context}
           
For each party, extract:
- Name of the entity or individual or Company or Group
- Type of entity (corporation, LLC etc)
- Role in contract
Return in a clear list format.""",

           "obligations": f"""Extract the key obligations for each party.
           
           {context}
           
Include:
- Transcanctions and services or Payment obligations
- Currency details
- Delivery schedules
- Money amounts transferred or received or paid
- Core responsibilities
- Specific deliverables
- Required actions
- Conditions and requirements
Group by party and list in order of importance.""",

           "deadlines": f"""Identify all important dates and deadlines.
           
           {context}
           
Include:
- Effective/start date
- Delivery dates
- Payment deadlines
- Review/approval periods
- Termination dates
List chronologically with context.""",

           "penalties": f"""Extract all penalties and consequences.
           
           {context}
           
Include:
- Late delivery penalties
- Payment penalties
- Breach consequences
- Termination penalties
Group by type and list amounts/terms."""
       }
       return prompts.get(section, "Extract and summarize key information from this section.")

   @classmethod
   def format_summary(cls, extracted_data: Dict[str, Any]) -> str:
       summary = ["# Contract Summary\n"]
    
       if "overview" in extracted_data:
           summary.extend([
               "## Overview",
               extracted_data["overview"],
               ""
           ])

       for section in ["obligations", "deadlines", "penalties", "additional"]:
           if section in extracted_data:
               summary.extend([
                   f"## {section.title()}", 
                   extracted_data[section],
                   ""
               ])

       return "\n".join(summary)

   @classmethod
   def create_metadata(cls) -> Dict[str, Any]:
       return {
           "name": cls.NAME,
           "role": cls.ROLE,
           "version": cls.VERSION,
           "capabilities": cls.CAPABILITIES,
           "created_at": datetime.now().isoformat(),
           "requirements": {
               "extract_parties": True,
               "extract_dates": True,
               "extract_values": True,
               "extract_obligations": True,
               "min_content_length": 100
           }
       }