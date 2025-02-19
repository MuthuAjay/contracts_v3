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

    def process_extractions(self, content, vec, agent) -> None:
        """Process all extractions"""
        for key, value in self.contract_sections.items():
            if key == "Contract Metadata":
                context = content[:3000]
            else:
                context = content

            response = agent.run(self._build_extraction_prompt(context, value))
            self._store_result([response.content])

            # break
            self.check_results(value)

    def _build_extraction_prompt(self, context: str, value: List) -> str:
        """Build extraction prompt"""
        return f"""From the following text {context}
        Extract the following fields from the OCR content of the contract document:
        maintain the sequence of the fields as per the contract

        {value}

        Response Format:
        Value: <extracted_value>

        Note return in a json format with the field name and the extracted value only if the value is present in the OCR content
        Do not return any other information or analysis
        Do not Hallucinate the data. If the data is not present in the OCR content, do not make any assumptions.
        Do not print any other information or analysis
        """

    def clean_json_string(self, json_str):
        """Clean the JSON string by removing markdown code markers and any extra whitespace"""
        # Remove markdown code markers
        print(json_str)
        cleaned = json_str.replace("```json", "").replace("```", "")
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
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
                continue

        return merged_data

    def _store_result(self, response: Any) -> None:
        """Store extraction result with section information"""
        parsed_response = self._parse_response(response)

        for key, value in parsed_response.items():
            if value == None or value == "":
                value = "Not Found"
            self.results.append(
                {
                    "term": key,
                    "extracted_value": value,
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
