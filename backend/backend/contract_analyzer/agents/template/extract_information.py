import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from tqdm.auto import tqdm
import pandas as pd
import json


class ExtractionProcessor:
    """Enhanced processor for contract information extraction with section tracking"""

    def __init__(self):
        self.results = []
        self.error_strs = []
        self.contract_sections = {
            "Contract Metadata": [
                "Contract Name",
                "Agreement Type",
                "Country of agreement",
                "Contract Details",
                "Entity Name",
                "Counterparty Name",
                "Summary",
                "Department of Contract Owner",
                "SPOC",
                "Agreement Group",
                "Family Agreement",
                "Family Documents Present",
                "Family Hierarchy",
                "Scanned",
            ],
            "Key Dates and Duration": [
                "Signature by:",
                "Effective Date",
                "Contract Start Date",
                "Contract Duration",
                "Contract End Date",
                "Contingent Contract",
                "Perpetual Contract",
                "SLA",
                "Stamping Date",
                "Franking Date",
                "Franking Date_Availablity",
            ],
            "Legal Framework": [
                "Governing Law",
                "Dispute Resolution",
                "Place of Courts",
                "Court Jurisdiction",
                "Place of Arbitration",
                "Arbitration Institution",
                "Number of Arbitrators",
                "Seat of Arbitration",
                "Venue of Arbitration",
            ],
            "Liability and Indemnification": [
                "Legal Action Rights with counterparty",
                "Counterparty - liability cap",
                "Counterparty - liability limitation summary",
                "Indemnification",
                "Indemnification Summary",
                "Counterparty - liquidated damages",
                "Counterparty - damages summary",
                "Penalties",
                "Penal interest rate and other late payment charges",
            ],
            "Assignment and Termination": [
                "assignment rights",
                "Counterparty assignment rights",
                "Counterparty - assignment summary",
                "Can  terminate for Convenience?",
                "If yes, number of notice days?",
                "Can Counterparty terminate for Convenience?",
                "Counterparty - If yes, number of notice days?",
                "Counterparty - termination summary",
            ],
            "Contract Renewal and Lock-in": [
                "Provision for lock-in period",
                "Period of lock in.",
                "Lock-in summary",
                "Counterparty  - Change of Control Provision",
                "Auto-renewal provision",
                "Notice period (in days) to stop auto renewal",
                "Renewal Option Notice Start Date",
                "Renewal Option Notice End Date",
                "Auto-renewal provision summary",
            ],
            "Special Clauses": [
                "Acceleration clause applicable to ",
                "Acceleration clause applicable to Counterparty",
                "Acceleration clause - summary",
                "Exclusivity provision",
                "Scope",
                "Territory",
                "Carve-outs",
                "Exclusivity Period (Start Date)",
                "Exclusivity Period (End Date)",
                "Available to ",
                "Available to Counterparty",
                "Audit Rights - Summary",
            ],
            "Intellectual Property and Compliance": [
                "Copyright",
                "Patent",
                "Trademark",
                "Other",
                "ABAC/FCPA provision",
                "ABAC/FCPA provision - summary",
            ],
            "Financial Terms": [
                "Receive or Pay", 
                "Currency",
                "Total Contract Value",
                "Fixed Fee",
                "Security Deposit / Bank Guarantee",
                "Fuel surcharges",
                "Advance payment period",
                "Advance payment Amount",
                "Term for Refund of Security Deposit",
                "Incentive",
                "Revenue Share",
                "Commission Percentage",
                "Minimum Guarantee",
                "Variable Fee",
                "Fee-Other",
                "Payment Type",
                "Payment Schedule (in days)",
                "Payment Terms / Details",
                "Milestones",
                "Payment to Affiliates / Agency",
                "Fee Escalation",
                "Stamp Duty Share",
            ],
            "Confidentiality and Data Protection": [
                "Confidentiality",
                "Residual Confidentiality",
                "Exceptions to confidentiality",
                "Term (In months)",
                "Data Privacy Provision",
                "Data Privacy Summary",
            ],
            "Additional Terms and Conditions": [
                "Insurance coverage for ",
                "Insurance coverage for Counterparty",
                "Subcontracting rights for the  Counterpart",
                "Defect liability period",
                "Performance Guarantee",
                "Conflicts of Interests",
                "Force Majeure",
                "Insurance coverage",
                "Representation and Warranties",
                "Non-Compete",
                "Non-Solicitation",
                "Waiver",
                "Severability",
                "Survival",
            ],
            "Document Quality": [
                "Handwritten Comments",
                "Missing Pages",
                "Missing Signatures",
                "Review Comments (if any)",
            ],
        }

    def create_df(self) -> pd.DataFrame:
        """Create DataFrame from extraction types"""
        return pd.DataFrame(
            list(self.extraction_types.items()), columns=["Term", "Terms"]
        )

    def extract_sections(self, content, agent, section):
        extract_sections_prompt = f"""
        Analyze the following text:
        ---
        {content}
        ---
        
        The value "{section}" has been extracted from this text.
        
        Task:
        1. Identify specifically which section/part of the document contains this value "{section}"
        2. Determine how confident you are that this value belongs to the identified section
        
        Return ONLY a JSON with exactly these two fields:
        - "section": The name of the section where "{section}" appears (e.g., "Header", "Personal Information", "Employment History", etc.)
        - "confidence_score": A decimal between 0.0 and 1.0 representing your confidence
        
        Rules:
        - Section name must be 5 words or less
        - If you cannot determine the section, use "Unknown" with appropriate confidence score
        - Do not add any explanations, notes, or other text in your response
        - Return only valid JSON format
        
        Example valid response:
        {{"section": "Contact Information", "confidence_score": 0.95}}
        """
        
        response = agent.run(extract_sections_prompt)
        
        return response.content
        

    def process_extractions(self, content, vec, agent) -> None:
        
        self.agent = agent
        
        """Process all extractions"""
        for key, value in self.contract_sections.items():
            if key == "Contract Metadata":
                context = content[:3000]
            else:
                context = content

            response = self.agent.run(self._build_extraction_prompt(context, value))
            self._store_result([response.content], context)

            # break
            self.check_results(value)
            
        if len(self.error_strs) > 0:
            for error_str in self.error_strs:
                response = self.agent.run(error_str)
                self._store_result([response.content], context)
                
                self.check_results(value)
    
    
    def generate_response_format(self, values):
        """Generate expected response format with placeholders."""
        return '\n'.join([f'"{value}": "<extracted_value>"' for value in values])
            
    def _build_extraction_prompt(self, context: str, values: List, section_name: str = None) -> str:
        """
        Build an optimized extraction prompt with section-specific instructions for contract analysis.
        
        Args:
            context: The contract text to analyze
            values: List of fields to extract
            section_name: The name of the contract section being processed
        
        Returns:
            A structured prompt for the LLM to extract information
        """
        # Create a formatted list of fields
        field_list = ', '.join([f'"{v}"' for v in values])
        
        # Create a formatted JSON example
        fields_json = "{\n" + ",\n".join([f'  "{value}": ""' for value in values]) + "\n}"
        
        # Base prompt that will be used if no section is specified
        base_prompt = f"""
        TASK: Extract specific fields from a contract document.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        """
        
        # Section-specific prompts
        section_prompts = {
            "Contract Metadata": f"""
        TASK: Extract specific fields from a contract document - Contract Metadata section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a contract metadata specialist. Follow these steps:
        
        First, identify basic contract information (Contract Name, Agreement Type, Country).
        Second, extract entity information (Entity Name, Counterparty Name).
        Third, determine ownership and classification details (Department, SPOC, Agreement Group).
        Fourth, extract family relationship information (Family Agreement, Hierarchy).
        Finally, identify any document management details (Scanned status, Summary).
        """,
            
            "Key Dates and Duration": f"""
        TASK: Extract specific fields from a contract document - Key Dates and Duration section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a contract timeline analyst. Follow these steps:
        
        First, identify start dates (Signature Date, Effective Date, Contract Start Date).
        Second, determine duration information (Contract Duration, End Date).
        Third, extract special timing provisions (Contingent Contract, Perpetual Contract).
        Fourth, identify service level timelines (SLA details).
        Finally, extract administrative dates (Stamping Date, Franking Date).
        """,
            
            "Legal Framework": f"""
        TASK: Extract specific fields from a contract document - Legal Framework section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a legal framework analyst. Follow these steps:
        
        First, identify the governing law information.
        Second, extract dispute resolution mechanisms.
        Third, determine court jurisdiction details (Place of Courts, Court Jurisdiction).
        Fourth, identify all arbitration specifics (Place, Institution, Number of Arbitrators, Seat, Venue).
        """,
            
            "Liability and Indemnification": f"""
        TASK: Extract specific fields from a contract document - Liability and Indemnification section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a liability and indemnification specialist. Follow these steps:
        
        First, identify liability rights and limitations (Legal Action Rights, Liability Cap).
        Second, extract indemnification provisions and summaries.
        Third, determine damages details (Liquidated Damages, Damages Summary).
        Fourth, identify penalties and interest provisions.
        """,
            
            "Assignment and Termination": f"""
        TASK: Extract specific fields from a contract document - Assignment and Termination section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are an assignment and termination specialist. Follow these steps:
        
        First, identify assignment rights for both parties.
        Second, extract termination for convenience provisions (including notice periods).
        Third, determine counterparty termination rights.
        Finally, identify any termination summaries or special provisions.
        """,
            
            "Contract Renewal and Lock-in": f"""
        TASK: Extract specific fields from a contract document - Contract Renewal and Lock-in section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a contract renewal analyst. Follow these steps:
        
        First, identify any lock-in provisions and their duration.
        Second, extract change of control provisions.
        Third, determine auto-renewal details (provisions, notice periods).
        Fourth, identify renewal option notice dates.
        """,
            
            "Special Clauses": f"""
        TASK: Extract specific fields from a contract document - Special Clauses section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a special clauses analyst. Follow these steps:
        
        First, identify acceleration clauses and their applicability.
        Second, extract exclusivity provisions (scope, territory, carve-outs).
        Third, determine exclusivity period dates.
        Fourth, identify audit rights for both parties.
        """,
            
            "Intellectual Property and Compliance": f"""
        TASK: Extract specific fields from a contract document - Intellectual Property and Compliance section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are an IP and compliance specialist. Follow these steps:
        
        First, identify all IP provisions (Copyright, Patent, Trademark, Other).
        Second, extract ABAC/FCPA provisions and summaries.
        """,
            
            "Financial Terms": f"""
        TASK: Extract specific fields from a contract document - Financial Terms section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a financial contract analyzer. Follow these steps:
        
        First, identify any information about fees (Fixed Fee, Variable Fee, Total Contract Value, etc.).
        Second, find payment details (Payment Schedule, Payment Type, Payment Terms).
        Third, extract information about deposits and guarantees (Security Deposit, Bank Guarantee).
        Fourth, look for incentives, commissions, and revenue sharing terms.
        Finally, identify any other financial terms like Fee Escalation or Stamp Duty Share.
        """,
            
            "Confidentiality and Data Protection": f"""
        TASK: Extract specific fields from a contract document - Confidentiality and Data Protection section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a confidentiality and data protection specialist. Follow these steps:
        
        First, identify basic confidentiality provisions.
        Second, extract information about residual confidentiality and exceptions.
        Third, determine confidentiality term duration (in months).
        Fourth, identify data privacy provisions and summaries.
        """,
            
            "Additional Terms and Conditions": f"""
        TASK: Extract specific fields from a contract document - Additional Terms and Conditions section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are an additional terms analyst. Follow these steps:
        
        First, identify insurance coverage requirements for both parties.
        Second, extract subcontracting rights and liability periods.
        Third, determine performance guarantees and conflict provisions.
        Fourth, identify restrictive covenants (Non-Compete, Non-Solicitation).
        Finally, extract boilerplate clauses (Force Majeure, Warranties, Waiver, Severability, Survival).
        """,
            
            "Document Quality": f"""
        TASK: Extract specific fields from a contract document - Document Quality section.
        
        DOCUMENT CONTENT:
        ```
        {context}
        ```
        
        FIELDS TO EXTRACT (in this order):
        {field_list}
        
        EXTRACTION STRATEGY:
        You are a document quality analyst. Follow these steps:
        
        First, identify if there are any handwritten comments in the document.
        Second, determine if there are any missing pages or sections.
        Third, extract information about missing signatures.
        Finally, identify any review comments present in the document.
        """
        }
        
        # JSON formatting and validation instructions
        json_instructions = """
        RESPONSE FORMAT:
        You MUST return ONLY a valid JSON object with double quotes around ALL keys and values.
        
        Example of CORRECT format:
        {
        "field1": "extracted value 1",
        "field2": "extracted value 2"
        }
        
        Examples of INCORRECT formats:
        { field1: "extracted value 1", field2: "extracted value 2" }  // Missing quotes around keys
        { 'field1': 'extracted value 1', 'field2': 'extracted value 2' }  // Single quotes instead of double
        
        EXTRACTION RULES:
        - If a field is not found, use empty string: ""
        - All JSON keys and string values MUST have double quotes
        - No trailing commas allowed in the JSON
        - Ensure all special characters in values are properly escaped
        - Extract the EXACT text as it appears in the document
        - All monetary values should include currency and amount
        - All dates should maintain their original format
        - Include full context for provisions (e.g., full clause or detailed summary)
        
        IMPORTANT:
        - Return ONLY the JSON object with no explanations or additional text
        - The response MUST be valid, parseable JSON
        - Do not include backticks (```) or json tags around the response
        """
        
        # Select the appropriate prompt based on section_name
        if section_name and section_name in section_prompts:
            return section_prompts[section_name] + json_instructions
        else:
            return base_prompt + json_instructions

    def clean_json_string(self, json_str):
        """Clean the JSON string by removing markdown code markers and any extra whitespace"""
        # Remove markdown code markers
        
        cleaned = json_str.replace("```json", "").replace("```", "")
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        print(json_str)
        return cleaned

    def check_results(self, value: List) -> None:
        """Check if the extracted value is present in the OCR content"""
        for v in value:
            if v not in [result["term"] for result in self.results]:
                self.results.append(
                    {
                        "term": v,
                        "extracted_value": "Not Found",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    def _parse_response(self, json_strings: Any) -> Dict[str, str]:
        """Parse the response to extract value and section"""
        merged_data = {}

        self.error_strs = []
        
        # Process each JSON string in the list
        for json_str in json_strings:
            try:
                # Clean the JSON string
                cleaned_json = self.clean_json_string(json_str)
                if not cleaned_json:  # Skip empty strings
                    continue

                # Parse the JSON string
                json_obj = json.loads(cleaned_json)

                # Update the merged data with the current JSON object
                merged_data.update(json_obj)

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Problematic JSON string: {json_str[:100]}...")
                
                # Create Error Prompt
                
                error_prompt = f"""Error parsing JSON: {e} for JSON string: {json_str}... \n Fix the JSON string 
                
                Note Just return the JSON String in the correct format. Do not print any other information or analysis
                """
                self.error_strs.append(error_prompt)
                continue

        return merged_data

    def _store_result(self, response: Any, context: str) -> None:
        """Store extraction result with section information"""
        parsed_response = self._parse_response(response)

        for key, value in parsed_response.items():
            if value == None or value == "":
                value = "Not Found"
                section = "Not Found"
                confidence_score = "Not Found"
                
            elif value == "Not Found":
                section = "Not Found"
                confidence_score = "Not Found"
                
            elif value == "Not mentioned":
                section = "Not mentioned"
                confidence_score = "Not mentioned"
                
            elif value == "Not applicable":
                section = "Not applicable"
                confidence_score = "Not applicable"
                
            elif value == "Not Explicitly Mentioned":
                section = "Not Explicitly Mentioned"
                confidence_score = "Not Explicitly Mentioned"

            else:
                section = self.extract_sections(context, self.agent, value)
                parsed_section = self._parse_response([section])
                section = parsed_section["section"]
                confidence_score = parsed_section["confidence_score"]

            self.results.append(
                {
                    "term": key,
                    "extracted_value": value,
                    "section": section,
                    "confidence_score": confidence_score,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def export_results(self, format: str = "json") -> Any:
        """Export results in specified format"""
        if format == "json":
            return json.dumps(self.results, indent=2)
        elif format in ["csv", "dataframe"]:
            df = pd.DataFrame(self.results)
            return df.to_csv(index=False) if format == "csv" else df
        raise ValueError(f"Unsupported format: {format}")
