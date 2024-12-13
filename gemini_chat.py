import os
import json
import google.generativeai as genai
from typing import Dict, List, Any
import zipfile
import tempfile
from datetime import datetime

def initialize_gemini():
    """Initialize the Gemini model with configuration."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    generation_config = {
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    
    return model

def create_chat_session(model, history: List = None):
    """Create a new chat session with optional history."""
    if history is None:
        history = []
    return model.start_chat(history=history)

def format_api_analysis(request_info: Dict, response_info: Dict) -> str:
    """Format API analysis for Gemini input."""
    return f"""
    You are an API optimization expert. Here's the detailed information about an API request and response to analyze:

    API Request Analysis:
    - Method: {request_info.get('method')}
    - Endpoint: {request_info.get('url_analysis', {}).get('path')}
    - Headers: {json.dumps(request_info.get('headers', {}), indent=2)}
    
    API Response Analysis:
    - Status Code: {response_info.get('status_code')}
    - Response Time: {response_info.get('metadata', {}).get('timing', {}).get('total_time')}
    - Size: {response_info.get('metadata', {}).get('size')}
    
    Security Analysis:
    {json.dumps(response_info.get('metadata', {}).get('security_analysis', {}), indent=2)}

    Please analyze this information and provide:
    1. Detailed performance optimization suggestions
    2. Security improvements
    3. Best practices recommendations
    4. Code samples for implementing the improvements

    You can also process any additional files the user provides to help with the optimization.
    """

def process_uploaded_file(file_content: bytes, file_name: str) -> str:
    """Process an uploaded file and extract relevant information."""
    try:
        # Handle bytes or string input
        if isinstance(file_content, bytes):
            content = file_content.decode('utf-8')
        else:
            content = str(file_content)
        
        # Format the content for the AI
        formatted_content = f"""
File: {file_name}

Content:
{content}

Please analyze this file in the context of the API implementation and provide suggestions for improvement.
"""
        return formatted_content
    except UnicodeDecodeError:
        return f"Binary file uploaded: {file_name} (content cannot be processed)"

def create_optimized_api_files(chat_response: str) -> str:
    """
    Parse chat response and create downloadable files with optimized API code.
    Returns path to zip file containing the generated files.
    """
    # Create a temporary directory for files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a timestamp for unique file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"optimized_api_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # Create a zip file containing the optimized code
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Extract code blocks from chat response
            code_blocks = extract_code_blocks(chat_response)
            
            # Add each code block as a separate file
            for i, (filename, code) in enumerate(code_blocks.items()):
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(code)
                zf.write(file_path, filename)
            
            # Add README with implementation instructions
            readme_content = generate_readme(chat_response)
            readme_path = os.path.join(temp_dir, "README.md")
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            zf.write(readme_path, "README.md")
        
        return zip_path

def extract_code_blocks(response: str) -> Dict[str, str]:
    """Extract code blocks from the chat response and organize them by filename."""
    code_blocks = {}
    lines = response.split('\n')
    current_file = None
    current_code = []
    
    for line in lines:
        if line.startswith('```') and len(line) > 3:
            # New code block starts
            if current_file:
                code_blocks[current_file] = '\n'.join(current_code)
                current_code = []
            current_file = line[3:].strip()
        elif line.startswith('```') and current_file:
            # Code block ends
            code_blocks[current_file] = '\n'.join(current_code)
            current_file = None
            current_code = []
        elif current_file:
            # Inside a code block
            current_code.append(line)
            
    return code_blocks

def generate_readme(response: str) -> str:
    """Generate README file with implementation instructions."""
    return f"""# API Optimization Implementation Guide

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview
This package contains optimized API code generated based on the analysis of your API implementation.

## Implementation Instructions
{response.split('Here are the implementation steps:', 1)[-1].split('```')[0] if 'Here are the implementation steps:' in response else ''}

## Files Included
{chr(10).join(['- ' + filename for filename in extract_code_blocks(response).keys()])}

## Support
For any questions or issues, please refer to the documentation or contact your development team.
"""

class GeminiChatManager:
    def __init__(self):
        self.model = initialize_gemini()
        self.chat_session = None
        
    def start_chat(self):
        """Start a new chat session."""
        self.chat_session = create_chat_session(self.model)
        
    def analyze_api(
        self,
        request_info: Dict,
        response_info: Dict,
        additional_context: str = None,
        user_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Analyze API request and response, provide optimization suggestions,
        and generate optimized code if needed.
        """
        if not self.chat_session:
            self.start_chat()
            
        # Format API analysis for the model
        analysis = format_api_analysis(request_info, response_info)
        
        # Prepare the prompt
        base_prompt = f"""
        As an API optimization expert, analyze this API implementation and provide detailed recommendations.
        
        Here's the API analysis to review:
        {analysis}
        """
        
        if additional_context:
            base_prompt += f"\n\nAdditional files for analysis:\n{additional_context}"
            
        if user_prompt:
            base_prompt += f"\n\nUser question: {user_prompt}"
        else:
            base_prompt += """
            Please provide your response in the following format:
            1. Analysis summary
            2. Specific recommendations
            3. If code changes are needed, include them in code blocks with filenames
            4. Implementation steps
            """
        
        # Get model response
        response = self.chat_session.send_message(base_prompt)
        
        # Generate files if the response contains code blocks
        zip_path = None
        if "```" in response.text:
            zip_path = create_optimized_api_files(response.text)
        
        return {
            "analysis": response.text,
            "files_path": zip_path
        }
