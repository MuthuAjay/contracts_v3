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
        self.extraction_types = {
            "Agreement Category": "master agreement, service agreement, license agreement, framework agreement, statement of work, purchase order, SOW, MSA, SaaS agreement",
            "Template used": "template, standard form, form agreement, standard terms, company template, approved template, template version",
            "Nature of Agreement": "scope, purpose, whereas, background, recitals, nature, type of agreement, agreement purpose",
            "Document Type": "agreement, contract, deed, amendment, addendum, memorandum, MOU, letter of intent, LOI",
            "Document Type Comment": "agreement type, contract classification, document category, contract type, supporting document",
            "Contracting Entity": "party, first party, company, corporation, entity, contracting party, service provider",
            "Contracting Entity Location": "registered office, principal place of business, address, location, headquarters, incorporation place",
            "Counterparty Entity Name": "second party, counterparty, client, customer, vendor, supplier, contractor",
            "Counterparty Entity Location": "counterparty address, client location, vendor location, supplier address",
            "Contract Summary": "purpose, whereas clause, recitals, scope of services, scope of work, agreement overview",
            "Country Where Work will be performed": "location of services, place of performance, service location, delivery location, work site",
            "Effective Date": "term, effective, term clause, commencement date, start date",
            "Effective Date Comments": "effectiveness condition, condition precedent, starting conditions",
            "Initial Term End Date": "term clause, end, expiration date, initial period end",
            "Initial Term End Date Comments": "initial term conditions, first period end, primary term completion",
            "Term Type": "fixed term, indefinite term, perpetual, duration, term period, contract duration",
            "Term Type Comments": "term conditions, duration specifications, period details",
            "Contract Terminated on": "termination date, end date, cessation date, contract end",
            "Contract Terminated on Comments": "early termination, termination notice, termination trigger, termination conditions",
            "Renewal Type": "renew, renewal, extend, extension, automatic renewal, renewal terms",
            "Renewal Type Comments": "renewal conditions, extension provisions, continuation terms",
            "Renewal Term End Date": "renewal expiration, extension end date, renewed term end",
            "Renewal Term End Date Comments": "renewal period end conditions, extension completion terms",
            "Milestone of Agreements or Contract": "deliverables, milestones, phases, timeline, schedule, key dates",
            "Milestone of Agreements or Contract Comments": "milestone conditions, delivery schedule, phase completion",
            "Agreement Termination Type": "terminate, termination, termination clause, termination rights",
            "Agreement Termination Type Comment": "termination conditions, termination process, termination procedure",
            "Agreement Termination notice Period": "notice period, termination notice, advance notice, written notice",
            "Agreement Termination notice Period Comments": "notice requirements, notification terms, notice conditions",
            "Payment Currency": "currency, dollars, EUR, USD, payment in, denomination, monetary unit",
            "Payment Term": "payment schedule, payment terms, net 30, net 60, payment within, payment deadline",
            "Late Payment Onus": "interest, late payment interest, default interest, interest rate",
            "Late Payment Onus Comments": "interest calculation, late payment consequences, default terms",
            "Late Payment Penalty": "penalty, late fee, additional charges, penalty rate, liquidated damages",
            "Price": "fees, charges, cost, price, rate, compensation, payment amount",
            "Price Comments": "pricing terms, fee structure, cost breakdown, rate card",
            "Value Of Contract": "contract value, total value, consideration, total fees, contract worth",
            "Invoice Cycle": "invoice, billing cycle, billing period, invoice frequency, payment schedule",
            "Invoice Cycle Comments": "billing terms, invoice schedule, payment frequency",
            "Liability Cap": "liability clause, liable, limitation of liability, liability limit, maximum liability",
            "Liability Cap Comments": "liability conditions, liability exceptions, liability terms",
            "Indemnity": "indemnification clause, indemnify, indem*, indemnification, hold harmless",
            "Indemnity Comments": "indemnification scope, indemnity conditions, indemnification terms",
            "Confidential Obligation": "confidentiality clause, confidential information, non-disclosure, secrecy",
            "Confidentiality Obligation Comments": "confidentiality terms, confidentiality scope, disclosure restrictions",
            "Duration of Confidentiality Obligation": "confidentiality period, confidentiality term, survival period",
            "Limitation of Data Processing": "data protection, GDPR, data processing, personal data, data handling",
            "Exclusivity": "intellectual property clause, exclusive, exclusive rights, sole rights",
            "Exclusivity Comments": "exclusivity terms, exclusive arrangements, exclusivity scope",
            "Sub-Contractor Permitted": "contractor, contracting, sub-contracting clause, subcontractor",
            "Sub-Contractor Permitted Comments": "subcontracting terms, delegation rights, assignment rights",
            "Non-Compete": "compete, non-compete clause, competition restriction, competitive activities",
            "Non-Compete Comments": "competition terms, non-compete scope, competitive restrictions",
            "Non-Solicitation": "solicit, non-solicitation clause, hire, employ, poaching",
            "Non-Solicitation Comments": "solicitation restrictions, hiring restrictions, employee restrictions",
            "Types of IP": "copyright, patents, database rights, trade marks, designs, know-how, intellectual property types",
            "Ownership of IP": "intellectual property clause, intellectual, owns, ownership, owner, IP rights",
            "Ownership of IP comments": "IP ownership terms, intellectual property rights, ownership conditions",
            "Transfer of IP": "intellectual property clause, transfer, transferable, IP assignment",
            "Transfer of IP Comments": "IP transfer terms, assignment conditions, transfer restrictions",
            "Insurance if Any": "insurance clause, insurance, coverage, policy, insured amount",
            "Any ESG Or CSR Obligation": "environmental, social, governance, sustainability, corporate social responsibility, ESG",
            "Change of Control Provision": "change in control, merger, acquisition, ownership change, control transfer",
            "Governing Law": "law, laws, governing law provision, jurisdiction, applicable law, arbitration",
            "Dispute resolution": "court, arbitration, dispute, mediation, conflict resolution",
            "Notes": "additional terms, special conditions, additional provisions, remarks",
        }

        self.extraction_prompts = {
            "Agreement Category": (
                "Please extract the 'Agreement Category' from the provided document. "
                "Look for mentions of: master agreement, service agreement, license agreement, framework agreement, "
                "statement of work, purchase order, SOW, MSA, SaaS agreement."
            ),
            "Template used": (
                "Please extract the 'Template used' from the provided document. "
                "Search for terms such as: template, standard form, form agreement, standard terms, company template, "
                "approved template, template version."
            ),
            "Nature of Agreement": (
                "Please extract the 'Nature of Agreement' from the document. "
                "Identify sections discussing: scope, purpose, whereas, background, recitals, nature, type of agreement, "
                "agreement purpose."
            ),
            "Document Type": (
                "Please extract the 'Document Type' from the document. "
                "Look for references such as: agreement, contract, deed, amendment, addendum, memorandum, MOU, letter of intent, LOI."
            ),
            "Document Type Comment": (
                "Please extract the 'Document Type Comment' from the document. "
                "Look for contextual cues like: agreement type, contract classification, document category, contract type, supporting document."
            ),
            "Contracting Entity": (
                "Please extract the 'Contracting Entity' from the document. "
                "Search for terms including: party, first party, company, corporation, entity, contracting party, service provider."
            ),
            "Contracting Entity Location": (
                "Please extract the 'Contracting Entity Location' from the document. "
                "Look for indicators such as: registered office, principal place of business, address, location, headquarters, incorporation place."
            ),
            "Counterparty Entity Name": (
                "Please extract the 'Counterparty Entity Name' from the document. "
                "Look for keywords such as: second party, counterparty, client, customer, vendor, supplier, contractor."
            ),
            "Counterparty Entity Location": (
                "Please extract the 'Counterparty Entity Location' from the document. "
                "Search for terms like: counterparty address, client location, vendor location, supplier address."
            ),
            "Contract Summary": (
                "Please extract the 'Contract Summary' from the document. "
                "Look for summaries mentioning: purpose, whereas clause, recitals, scope of services, scope of work, agreement overview."
            ),
            "Country Where Work will be performed": (
                "Please extract the 'Country Where Work will be performed' from the document. "
                "Identify phrases such as: location of services, place of performance, service location, delivery location, work site."
            ),
            "Effective Date": (
                "Please extract the 'Effective Date' from the document. "
                "Look for dates or phrases like: term, effective, term clause, commencement date, start date."
            ),
            "Effective Date Comments": (
                "Please extract any 'Effective Date Comments' from the document. "
                "Look for conditions or clarifications such as: effectiveness condition, condition precedent, starting conditions."
            ),
            "Initial Term End Date": (
                "Please extract the 'Initial Term End Date' from the document. "
                "Search for references such as: term clause, end, expiration date, initial period end."
            ),
            "Initial Term End Date Comments": (
                "Please extract any 'Initial Term End Date Comments' from the document. "
                "Look for clarifications like: initial term conditions, first period end, primary term completion."
            ),
            "Term Type": (
                "Please extract the 'Term Type' from the document. "
                "Identify the term duration by looking for: fixed term, indefinite term, perpetual, duration, term period, contract duration."
            ),
            "Term Type Comments": (
                "Please extract any 'Term Type Comments' from the document. "
                "Look for details such as: term conditions, duration specifications, period details."
            ),
            "Contract Terminated on": (
                "Please extract the 'Contract Terminated on' date from the document. "
                "Look for terms such as: termination date, end date, cessation date, contract end."
            ),
            "Contract Terminated on Comments": (
                "Please extract any 'Contract Terminated on Comments' from the document. "
                "Look for information like: early termination, termination notice, termination trigger, termination conditions."
            ),
            "Renewal Type": (
                "Please extract the 'Renewal Type' from the document. "
                "Search for indications like: renew, renewal, extend, extension, automatic renewal, renewal terms."
            ),
            "Renewal Type Comments": (
                "Please extract any 'Renewal Type Comments' from the document. "
                "Look for details such as: renewal conditions, extension provisions, continuation terms."
            ),
            "Renewal Term End Date": (
                "Please extract the 'Renewal Term End Date' from the document. "
                "Look for phrases like: renewal expiration, extension end date, renewed term end."
            ),
            "Renewal Term End Date Comments": (
                "Please extract any 'Renewal Term End Date Comments' from the document. "
                "Look for clarifications such as: renewal period end conditions, extension completion terms."
            ),
            "Milestone of Agreements or Contract": (
                "Please extract the 'Milestone of Agreements or Contract' from the document. "
                "Look for key milestones such as: deliverables, milestones, phases, timeline, schedule, key dates."
            ),
            "Milestone of Agreements or Contract Comments": (
                "Please extract any 'Milestone of Agreements or Contract Comments' from the document. "
                "Look for additional details like: milestone conditions, delivery schedule, phase completion."
            ),
            "Agreement Termination Type": (
                "Please extract the 'Agreement Termination Type' from the document. "
                "Look for terms like: terminate, termination, termination clause, termination rights."
            ),
            "Agreement Termination Type Comment": (
                "Please extract any 'Agreement Termination Type Comment' from the document. "
                "Look for details such as: termination conditions, termination process, termination procedure."
            ),
            "Agreement Termination notice Period": (
                "Please extract the 'Agreement Termination notice Period' from the document. "
                "Search for references such as: notice period, termination notice, advance notice, written notice."
            ),
            "Agreement Termination notice Period Comments": (
                "Please extract any 'Agreement Termination notice Period Comments' from the document. "
                "Look for clarifications like: notice requirements, notification terms, notice conditions."
            ),
            "Payment Currency": (
                "Please extract the 'Payment Currency' from the document. "
                "Look for currency indicators such as: currency, dollars, EUR, USD, payment in, denomination, monetary unit."
            ),
            "Payment Term": (
                "Please extract the 'Payment Term' from the document. "
                "Identify payment terms by searching for: payment schedule, payment terms, net 30, net 60, payment within, payment deadline."
            ),
            "Late Payment Onus": (
                "Please extract the 'Late Payment Onus' from the document. "
                "Look for mentions of interest or fees such as: interest, late payment interest, default interest, interest rate."
            ),
            "Late Payment Onus Comments": (
                "Please extract any 'Late Payment Onus Comments' from the document. "
                "Look for explanations like: interest calculation, late payment consequences, default terms."
            ),
            "Late Payment Penalty": (
                "Please extract the 'Late Payment Penalty' from the document. "
                "Look for mentions of penalties such as: penalty, late fee, additional charges, penalty rate, liquidated damages."
            ),
            "Price": (
                "Please extract the 'Price' from the document. "
                "Look for numerical values or references to fees, charges, cost, price, rate, compensation, or payment amount."
            ),
            "Price Comments": (
                "Please extract any 'Price Comments' from the document. "
                "Look for additional details such as: pricing terms, fee structure, cost breakdown, rate card."
            ),
            "Value Of Contract": (
                "Please extract the 'Value Of Contract' from the document. "
                "Look for mentions of: contract value, total value, consideration, total fees, contract worth."
            ),
            "Invoice Cycle": (
                "Please extract the 'Invoice Cycle' from the document. "
                "Look for indications of billing frequency such as: invoice, billing cycle, billing period, invoice frequency, payment schedule."
            ),
            "Invoice Cycle Comments": (
                "Please extract any 'Invoice Cycle Comments' from the document. "
                "Look for clarifications such as: billing terms, invoice schedule, payment frequency."
            ),
            "Liability Cap": (
                "Please extract the 'Liability Cap' from the document. "
                "Look for references to limits such as: liability clause, liable, limitation of liability, liability limit, maximum liability."
            ),
            "Liability Cap Comments": (
                "Please extract any 'Liability Cap Comments' from the document. "
                "Look for additional details such as: liability conditions, liability exceptions, liability terms."
            ),
            "Indemnity": (
                "Please extract the 'Indemnity' information from the document. "
                "Look for mentions of indemnification such as: indemnification clause, indemnify, indem*, indemnification, hold harmless."
            ),
            "Indemnity Comments": (
                "Please extract any 'Indemnity Comments' from the document. "
                "Look for details such as: indemnification scope, indemnity conditions, indemnification terms."
            ),
            "Confidential Obligation": (
                "Please extract the 'Confidential Obligation' from the document. "
                "Look for references to confidentiality such as: confidentiality clause, confidential information, non-disclosure, secrecy."
            ),
            "Confidentiality Obligation Comments": (
                "Please extract any 'Confidentiality Obligation Comments' from the document. "
                "Look for clarifications like: confidentiality terms, confidentiality scope, disclosure restrictions."
            ),
            "Duration of Confidentiality Obligation": (
                "Please extract the 'Duration of Confidentiality Obligation' from the document. "
                "Look for time frames such as: confidentiality period, confidentiality term, survival period."
            ),
            "Limitation of Data Processing": (
                "Please extract the 'Limitation of Data Processing' details from the document. "
                "Look for mentions of: data protection, GDPR, data processing, personal data, data handling."
            ),
            "Exclusivity": (
                "Please extract the 'Exclusivity' information from the document. "
                "Look for indications of exclusive rights such as: intellectual property clause, exclusive, exclusive rights, sole rights."
            ),
            "Exclusivity Comments": (
                "Please extract any 'Exclusivity Comments' from the document. "
                "Look for additional details such as: exclusivity terms, exclusive arrangements, exclusivity scope."
            ),
            "Sub-Contractor Permitted": (
                "Please extract the 'Sub-Contractor Permitted' information from the document. "
                "Look for mentions of subcontracting such as: contractor, contracting, sub-contracting clause, subcontractor."
            ),
            "Sub-Contractor Permitted Comments": (
                "Please extract any 'Sub-Contractor Permitted Comments' from the document. "
                "Look for clarifications like: subcontracting terms, delegation rights, assignment rights."
            ),
            "Non-Compete": (
                "Please extract the 'Non-Compete' information from the document. "
                "Look for references to competition restrictions such as: compete, non-compete clause, competition restriction, competitive activities."
            ),
            "Non-Compete Comments": (
                "Please extract any 'Non-Compete Comments' from the document. "
                "Look for additional details such as: competition terms, non-compete scope, competitive restrictions."
            ),
            "Non-Solicitation": (
                "Please extract the 'Non-Solicitation' information from the document. "
                "Look for terms related to recruitment restrictions such as: solicit, non-solicitation clause, hire, employ, poaching."
            ),
            "Non-Solicitation Comments": (
                "Please extract any 'Non-Solicitation Comments' from the document. "
                "Look for details such as: solicitation restrictions, hiring restrictions, employee restrictions."
            ),
            "Types of IP": (
                "Please extract the 'Types of IP' from the document. "
                "Look for mentions of intellectual property types such as: copyright, patents, database rights, trade marks, designs, know-how, intellectual property types."
            ),
            "Ownership of IP": (
                "Please extract the 'Ownership of IP' from the document. "
                "Look for references to ownership of intellectual property such as: intellectual property clause, intellectual, owns, ownership, owner, IP rights."
            ),
            "Ownership of IP comments": (
                "Please extract any 'Ownership of IP comments' from the document. "
                "Look for further details such as: IP ownership terms, intellectual property rights, ownership conditions."
            ),
            "Transfer of IP": (
                "Please extract the 'Transfer of IP' information from the document. "
                "Look for terms related to intellectual property transfer such as: intellectual property clause, transfer, transferable, IP assignment."
            ),
            "Transfer of IP Comments": (
                "Please extract any 'Transfer of IP Comments' from the document. "
                "Look for details such as: IP transfer terms, assignment conditions, transfer restrictions."
            ),
            "Insurance if Any": (
                "Please extract the 'Insurance if Any' details from the document. "
                "Look for mentions of insurance such as: insurance clause, insurance, coverage, policy, insured amount."
            ),
            "Any ESG Or CSR Obligation": (
                "Please extract any 'ESG Or CSR Obligation' from the document. "
                "Look for references to: environmental, social, governance, sustainability, corporate social responsibility, ESG."
            ),
            "Change of Control Provision": (
                "Please extract the 'Change of Control Provision' from the document. "
                "Look for terms such as: change in control, merger, acquisition, ownership change, control transfer."
            ),
            "Governing Law": (
                "Please extract the 'Governing Law' from the document. "
                "Look for references such as: law, laws, governing law provision, jurisdiction, applicable law, arbitration."
            ),
            "Dispute resolution": (
                "Please extract the 'Dispute resolution' details from the document. "
                "Look for terms such as: court, arbitration, dispute, mediation, conflict resolution."
            ),
            "Notes": (
                "Please extract any 'Notes' from the document. "
                "Look for additional information such as: additional terms, special conditions, additional provisions, remarks."
            ),
        }

    def create_df(self) -> pd.DataFrame:
        """Create DataFrame from extraction types"""
        return pd.DataFrame(
            list(self.extraction_types.items()), columns=["Term", "Terms"]
        )

    def process_extractions(self, content, vec, agent) -> None:
        """Process all extractions"""

        meta_list = [
            "Agreement Category",
            "Template used",
            "Nature of Agreement",
            "Document Type",
            "Document Type Comment",
            "Contracting Entity",
            "Contracting Entity Location",
            "Counterparty Entity Name",
            "Counterparty Entity Location",
        ]

        df = self.create_df()
        for _, row in tqdm(df.iterrows(), desc="Extracting Information"):
            if len(content) > 20000:
                context = vec.get_context(self._build_search_prompt(row), num_results=2)
            else:
                context = content
            
            if row["Term"].isin(meta_list):
                context = content[:3000]
            
            response = agent.run(self._build_extraction_prompt(context, row))
            self._store_result(row["Term"], response, context)

    def _build_search_prompt(self, row: pd.Series) -> str:
        """Build vector search prompt"""
        return f"""
        Find sections containing information about {row['Term']}.
        Key phrases: {row['Terms']}
        Return relevant sections with context.
        """

    def _build_extraction_prompt(self, context: str, row: pd.Series) -> str:
        """Build extraction prompt"""
        return f"""
        {self.extraction_prompts[row['Term']]}
        Extract section/paragraph where the value was found from the following context. 
        Context:
        {context}

        Requirements:
        - Extract the specific value
        - Include the exact section/paragraph where the value was found (hint it will have numbers eg: 11.1, 12.1)
        - Return "Not specified" if not found
        - No explanations or analysis
        
        Format: 
        Value: <extracted_value>
        Section: <relevant_section>
        """

    def _parse_response(self, response: Any) -> Dict[str, str]:
        """Parse the response to extract value and section"""
        content = response.content.strip()

        # Initialize default values
        value = "Not specified"
        section = "Not found"

        # Split the response into lines
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("Value:"):
                value = line[6:].strip()
            elif line.startswith("Section:"):
                section = line[8:].strip()

        return {"value": value, "section": section}

    def _store_result(self, term: str, response: Any, context: str) -> None:
        """Store extraction result with section information"""
        parsed_response = self._parse_response(response)

        self.results.append(
            {
                "term": term,
                "extracted_value": parsed_response["value"],
                "section": parsed_response["section"],
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

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        df = pd.DataFrame(self.results)
        return {
            "total_terms": len(df),
            "terms_found": len(df[df["extracted_value"] != "Not specified"]),
            "sections_found": len(df[df["section"] != "Not found"]),
            "completion_rate": f"{(len(df[df['extracted_value'] != 'Not specified']) / len(df)) * 100:.1f}%",
        }
