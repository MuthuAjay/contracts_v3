#!/usr/bin/env python3
import sys
import json
import argparse
from typing import Optional, Dict, Any
from contract_analyzer.database import VectorDB
from contract_analyzer.agents.agent_manager import AgentManager
from contract_analyzer.config import Config
from contract_analyzer.agents.template.contract_analyst import (
    ContractAnalystTemplate,
    AnalysisScope,
)
from contract_analyzer.agents.template.legal_researcher import (
    LegalResearcherTemplate,
    ResearchScope,
    ResearchDomain,
)
from contract_analyzer.agents.template.risk_assessment import (
    RiskAssessmentTemplate,
    RiskLevel,
    RiskCategory,
)
from contract_analyzer.agents.template.contract_summarizer import (
    ContractSummaryTemplate,
)
from contract_analyzer.agents.template.extract_information import (
    ExtractionProcessor, 
)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_db = VectorDB()


def perform_contract_review(
    content: str, agent_manager: AgentManager, collection_name: str
) -> Optional[Dict[str, Any]]:
    try:
        agent = agent_manager.create_agent(
            "contract_analyst", model_type=Config._current_model_type
        )
        initial_content = ''
        analysis_prompt = ContractAnalystTemplate.create_analysis_prompt(
            initial_content, AnalysisScope.COMPREHENSIVE
        )
        
        # logger.info(f"Contract Review Prompt: {analysis_prompt}")

        if vector_db.set_active_collection(collection_name):
            logger.info(f"Collection set to: {collection_name}")
        else:
            raise ValueError(f"Failed to set collection: {collection_name[:200]}")
        
        content = vector_db.get_context(analysis_prompt, num_results=5)

        analysis_prompt = ContractAnalystTemplate.create_analysis_prompt(
            content, AnalysisScope.COMPREHENSIVE
        )
        
        result = agent.run(analysis_prompt)
        
        print("Completed Comprehensive Analysis")
        
        # logger.info(f"Contract Review Result: {result.content}")

        extarct_key_prompt = ContractAnalystTemplate.extract_key_terms(initial_content)

        content = vector_db.get_context(extarct_key_prompt, num_results=5)

        extarct_key_prompt = ContractAnalystTemplate.extract_key_terms(content)

        key_terms = agent.run(extarct_key_prompt)
        
        print("Completed Key Term Extraction")

        analyze_obg_prompt = ContractAnalystTemplate.analyze_obligations(initial_content)

        content = vector_db.get_context(analyze_obg_prompt, num_results=5)

        analyze_obg_prompt = ContractAnalystTemplate.analyze_obligations(content)

        obligations = agent.run(analyze_obg_prompt)

        print("Completed Obligations Analysis")
        
        party_extract_prompt = ContractAnalystTemplate.create_party_extraction_prompt(
            initial_content
        )

        content = vector_db.get_context(party_extract_prompt, num_results=5)

        party_extract_prompt = ContractAnalystTemplate.create_party_extraction_prompt(
            content
        )

        parties = agent.run(party_extract_prompt)
        
        print("Completed Parties Extraction")
        
        # logger.info(f"Key Terms: {key_terms.content}")
        
        # logging.INFO(f"Contract Review completed successfully")

        return {
            "Contract Review": result.content,
            "Key Terms": key_terms.content,
            "Obligations": obligations.content,
            "Parties": parties.content,
        }
    except Exception as e:
        logger.error(f"Contract review failed: {str(e)}")
        return None
    
# def perform_contract_review(
#     content: str, agent_manager: AgentManager, collection_name: str
# ) -> Optional[Dict[str, Any]]:
#     agent = agent_manager.create_agent(
#         "contract_analyst", model_type=Config._current_model_type
#     )

#     if vector_db.set_active_collection(collection_name):
#         logger.info(f"Collection set to: {collection_name}")
#     else:
#         raise ValueError(f"Failed to set collection: {collection_name[:200]}")
    

#     context_prompt = ContractAnalystTemplate.get_context_prompt()

#     content = vector_db.get_context(context_prompt, num_results=7)

#     context_prompt = ContractAnalystTemplate.create_analysis_prompt(
#         content, AnalysisScope.COMPREHENSIVE
#     )

#     result = agent.run(context_prompt)

#     return {
#         "Contract Review": result.content,
#     }


def perform_legal_research(
    content: str, agent_manager: AgentManager
) -> Optional[Dict[str, Any]]:
    agent = agent_manager.create_agent(
        "legal_researcher", model_type=Config._current_model_type
    )

    prompt = LegalResearcherTemplate.create_research_prompt(
        context=content,
        scope=ResearchScope.COMPREHENSIVE,
        domain=ResearchDomain.CONTRACT_LAW,
    )

    result = agent.run(prompt)
    return {"Legal Research": result.content} if result else None


def perform_risk_assessment(
    content: str, agent_manager: AgentManager
) -> Optional[Dict[str, Any]]:

    agent = agent_manager.create_agent(
        "risk_assessor", model_type=Config._current_model_type
    )

    prompt = RiskAssessmentTemplate.create_assessment_prompt(
        context=content, risk_level=RiskLevel.HIGH
    )

    # Get detailed risk analysis by categories
    results = {}
    for category in [
        RiskCategory.LEGAL,
        RiskCategory.FINANCIAL,
        RiskCategory.OPERATIONAL,
        RiskCategory.COMPLIANCE,
    ]:
        category_prompt = RiskAssessmentTemplate.get_risk_prompt(content, category)
        category_result = agent.run(category_prompt)
        if category_result:
            results[category.value] = category_result.content
            
    

#     # Format the combined results
#     combined_analysis = f"""# Risk Assessment Analysis

# ## Overview
# {results.get('legal', '')}

# ## Financial Risks
# {results.get('financial', '')}

# ## Operational Risks
# {results.get('operational', '')}

# ## Compliance Risks
# {results.get('compliance', '')}
# """
#     return {"Risk Assessment": combined_analysis}

    return results


def perform_contract_summary(
    content: str, agent_manager: AgentManager
) -> Optional[Dict[str, Any]]:
    agent = agent_manager.create_agent(
        "contract_summarizer", model_type=Config._current_model_type
    )

    # Get initial context
    prompt = ContractSummaryTemplate.create_summary_prompt(context=content)
    result = agent.run(prompt)

    # Extract core details
    prompt_parties = ContractSummaryTemplate.extract_details_prompt(content, "parties")
    parties_result = agent.run(prompt_parties)

    prompt_obligations = ContractSummaryTemplate.extract_details_prompt(
        content, "obligations"
    )
    obligations_result = agent.run(prompt_obligations)

    prompt_dates = ContractSummaryTemplate.extract_details_prompt(content, "deadlines")
    dates_result = agent.run(prompt_dates)

    prompt_penalties = ContractSummaryTemplate.extract_details_prompt(
        content, "penalties"
    )
    penalties_result = agent.run(prompt_penalties)

    # Format extracted data
    extracted_data = {
        "summary": result.content if result else "",
        "overview": parties_result.content if parties_result else "",
        "obligations": obligations_result.content if obligations_result else "",
        "deadlines": dates_result.content if dates_result else "",
        "penalties": penalties_result.content if penalties_result else "",
    }

    summary = ContractSummaryTemplate.format_summary(extracted_data)
    return {"Contract Summary": summary}


def perform_custom_analysis(
    content: str, custom_query: str, agent_manager: AgentManager, collection_name: str
) -> Optional[Dict[str, Any]]:
    
    if vector_db.set_active_collection(collection_name):
        logger.info(f"Collection set to: {collection_name}")
    else:
        raise ValueError(f"Failed to set collection: {collection_name[:200]}")
    
    content = vector_db.get_context(custom_query)

    agent = agent_manager.create_agent(
        "custom_analyst",
        custom_instructions=["Perform specialized analysis based on query"],
        model_type=Config._current_model_type,
    )

    prompt = f"""Analyze the following document based on the custom query:

Document:
{content}

Query: {custom_query}

"""

    result = agent.run(prompt)
    return {"Custom Analysis": result.content} if result else None

def perform_information_extraction(content: str, agent_manager: AgentManager, collection_name: str) -> Optional[Dict[str, Any]]:
    """
    Perform information extraction on contract content
    
    Args:
        content: Contract content to analyze
        agent_manager: Agent manager instance
        collection_name: Name of the vector DB collection
        
    Returns:
        Dictionary containing extracted information
    """
    try:
        # Create agent
        agent = agent_manager.create_agent(
            "extract_information", 
            model_type=Config._current_model_type
        )
        
        # Set vector DB collection
        if vector_db.set_active_collection(collection_name):
            logger.info(f"Collection set to: {collection_name}")
        else:
            raise ValueError(f"Failed to set collection: {collection_name[:200]}")
            
        # Initialize extraction processor
        processor = ExtractionProcessor()
        
        vector_db.set_active_collection(collection_name)

        print("Collection set to: ", collection_name)
        
        # Process extractions
        processor.process_extractions(
            content=content,
            vec=vector_db,
            agent=agent,
        )
        
        # Get results in proper format
        results = processor.export_results(format='json')
        
        # Get summary statistics
        
        # Return formatted output
        return {
            "Information Extraction": {
                "results": json.loads(results),  # Parse JSON string to dict
                "status": "success"
            }
        }
        
    except Exception as e:
        logger.error(f"Information extraction failed: {str(e)}")
        return {
            "Information Extraction": {
                "error": str(e),
                "status": "failed"
            }
        }

def perform_analysis(
    content: str, 
    analysis_type: str, 
    custom_query: Optional[str] = None, 
    collection_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Perform analysis based on type
    """
    agent_manager = AgentManager()

    try:
        result = None
        
        if analysis_type == "Information Extraction":
            if not collection_name:
                raise ValueError("Collection name required for Information Extraction")
            result = perform_information_extraction(content, agent_manager, collection_name)
        elif analysis_type == "Contract Review":
            result = perform_contract_review(content, agent_manager, collection_name)
        elif analysis_type == "Legal Research":
            result = perform_legal_research(content, agent_manager, collection_name)
        elif analysis_type == "Risk Assessment":
            result = perform_risk_assessment(content, agent_manager, collection_name)
        elif analysis_type == "Contract Summary":
            result = perform_contract_summary(content, agent_manager, collection_name)
        elif analysis_type == "Custom Analysis":
            result = perform_custom_analysis(content, custom_query, agent_manager, collection_name)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        # Ensure result is JSON serializable
        if result:
            try:
                json.dumps(result)  # Test JSON serialization
                return result
            except (TypeError, json.JSONDecodeError) as e:
                logger.error(f"JSON serialization failed: {str(e)}")
                return {
                    "error": "Result could not be serialized to JSON",
                    "status": "failed"
                }
        return None

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }
    finally:
        agent_manager.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze contract documents")
    parser.add_argument("--content", required=True, help="Document content to analyze")
    parser.add_argument("--type", required=True, help="Type of analysis to perform")
    parser.add_argument("--query", help="Custom query for analysis")
    parser.add_argument("--collection_name", help="Collection name for querying the database")

    args = parser.parse_args()
    
    try:
        result = perform_analysis(args.content, args.type, args.query, args.collection_name)
        
        if result:
            # Ensure proper JSON formatting
            print(json.dumps(result, indent=2))
            sys.exit(0)
        else:
            logger.error("Analysis returned no result")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)