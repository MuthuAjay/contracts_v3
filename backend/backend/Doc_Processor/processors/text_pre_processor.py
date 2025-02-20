from ollama import chat
import json
import re
from collections import defaultdict


def process_text_chunks(text, chunk_size=3000):
    """Process text in chunks and get JSON responses from Ollama API"""
    all_responses = []

    # Process text in chunks
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]

        response = chat(
            model="llama3.1",
            messages=[
                {
                    "role": "user",
                    "content": f"""From the following agreement, please extract the content and give a json format" + f{chunk} + "Do not add any additional information. \n Don not do any Analysis.
                    
                    Format:
                    {{
                        "section1": "content1",
                        "section2": "content2",
                        ...
                    }}
                    """,
                }
            ],
        )
        print("--------------------------------------------")
        print(response["message"]["content"])
        all_responses.append(response["message"]["content"])

    return "\n".join(all_responses)


def clean_json_output(text):
    """Clean and process JSON output from the API responses"""
    # Find all JSON content between triple backticks
    json_pattern = r"```\s*\{.*?\}\s*```"
    json_matches = re.finditer(json_pattern, text, re.DOTALL)

    # Use defaultdict to handle repeated sections
    section_counter = defaultdict(int)
    final_json = {}

    for match in json_matches:
        try:
            # Extract and parse JSON
            json_str = match.group().strip("`").strip()
            json_content = json.loads(json_str)

            # Process each key-value pair
            for key, value in json_content.items():
                # Handle different types of values
                if isinstance(value, dict):
                    # For nested dictionaries
                    if key not in final_json:
                        final_json[key] = {}
                    for sub_key, sub_value in value.items():
                        section_counter[f"{key}_{sub_key}"] += 1
                        count = section_counter[f"{key}_{sub_key}"]
                        new_sub_key = f"{sub_key}_{count}" if count > 1 else sub_key
                        final_json[key][new_sub_key] = sub_value

                elif isinstance(value, list):
                    # For lists, extend existing list or create new one
                    if key not in final_json:
                        final_json[key] = []
                    # Remove duplicates while preserving order
                    new_items = [item for item in value if item not in final_json[key]]
                    final_json[key].extend(new_items)

                else:
                    # For simple values
                    section_counter[key] += 1
                    count = section_counter[key]
                    new_key = f"{key}_{count}" if count > 1 else key
                    final_json[new_key] = value

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            continue

    return final_json


def reorganize_sections(json_data):
    """Reorganize sections to maintain proper order and structure"""
    organized = {}

    # Sort sections that should be grouped together
    section_groups = defaultdict(list)

    for key, value in json_data.items():
        # Extract base section name (remove _1, _2, etc.)
        base_name = re.sub(r"_\d+$", "", key)
        section_groups[base_name].append((key, value))

    # Process each group
    for base_name, sections in section_groups.items():
        if len(sections) == 1:
            # If only one section, use original name
            organized[sections[0][0]] = sections[0][1]
        else:
            # If multiple sections, create a numbered list
            if isinstance(sections[0][1], dict):
                # For nested dictionaries
                organized[base_name] = {}
                for key, value in sections:
                    organized[base_name].update(value)
            else:
                # For regular sections
                organized[base_name] = [value for _, value in sorted(sections)]

    return organized


def split_text_into_chunks(text: str, chunk_size: int = 5000) -> list:
    """
    Split text into chunks while respecting paragraph boundaries.
    
    Args:
        text (str): The input text to be split
        chunk_size (int): Maximum size of each chunk in characters
        
    Returns:
        list: List of text chunks
    """
    chunks = []
    current_chunk = ""
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size and we have existing content
        if len(current_chunk) + len(paragraph) > chunk_size:
            if current_chunk:  # Add current chunk if not empty
                chunks.append(current_chunk.strip())
            # If single paragraph is larger than chunk_size, split at last sentence
            if len(paragraph) > chunk_size:
                sentences = paragraph.split('. ')
                current_chunk = ""
                temp_chunk = ""
                
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > chunk_size:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = sentence + '. '
                    else:
                        temp_chunk += sentence + '. '
                
                current_chunk = temp_chunk
            else:
                current_chunk = paragraph
        else:
            # Add paragraph with a newline if current_chunk is not empty
            separator = '\n\n' if current_chunk else ''
            current_chunk += separator + paragraph
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_agreement(text, use_llm: bool = False, chunk_size: int = 5000):
    """Main function to process agreement text and return final JSON"""
    
    if use_llm:
        # Use LLM to process text
        # Step 1: Process text in chunks and get API responses
        api_responses = process_text_chunks(text)
        
        # Step 2: Clean and combine JSON from responses
        merged_json = clean_json_output(api_responses)
        
        # Step 3: Reorganize sections
        final_json = reorganize_sections(merged_json)
        
        return final_json
    else:
        # Split the text into chunks using the new function
        return split_text_into_chunks(text, chunk_size)