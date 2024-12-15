"""API Documentation Generator

This module automatically generates documentation for API endpoints by analyzing
the codebase and extracting endpoint information, request/response schemas,
and security requirements.
"""

import inspect
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EndpointDoc:
    """Represents documentation for an API endpoint."""
    path: str
    method: str
    description: str
    parameters: Dict
    response_schema: Dict
    security_requirements: List[str]
    examples: Dict

class APIDocumentationGenerator:
    def __init__(self):
        self.endpoints = []
        
    def analyze_view_function(self, func) -> EndpointDoc:
        """Extract documentation from a view function."""
        source = inspect.getsource(func)
        docstring = inspect.getdoc(func) or ""
        
        # Extract path from function name and docstring
        path = f"/{func.__name__.replace('_view', '')}"
        
        # Extract method from the function implementation
        method = "GET"  # Default
        if "post" in source.lower():
            method = "POST"
        elif "put" in source.lower():
            method = "PUT"
        elif "delete" in source.lower():
            method = "DELETE"
        
        # Extract parameters from the function signature
        parameters = {}
        for param in inspect.signature(func).parameters.values():
            parameters[param.name] = {
                "type": str(param.annotation),
                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }
        
        # Extract security requirements
        security_reqs = []
        if "authentication" in source.lower():
            security_reqs.append("Authentication required")
        if "authorization" in source.lower():
            security_reqs.append("Authorization required")
            
        return EndpointDoc(
            path=path,
            method=method,
            description=docstring,
            parameters=parameters,
            response_schema=self._extract_response_schema(source),
            security_requirements=security_reqs,
            examples=self._generate_examples(path, method, parameters)
        )
    
    def _extract_response_schema(self, source: str) -> Dict:
        """Extract response schema from function source."""
        schema = {
            "type": "object",
            "properties": {}
        }
        
        # Look for return statements and json responses
        if "return" in source:
            if "json" in source.lower():
                schema["format"] = "json"
            elif "html" in source.lower():
                schema["format"] = "html"
                
        return schema
    
    def _generate_examples(self, path: str, method: str, parameters: Dict) -> Dict:
        """Generate example requests and responses."""
        examples = {
            "request": {
                "curl": f"curl -X {method} http://localhost:5000{path}",
                "python": f"""
import requests

response = requests.{method.lower()}('http://localhost:5000{path}')
print(response.json())
"""
            },
            "response": {
                "success": {
                    "status": 200,
                    "body": {"message": "Success"}
                },
                "error": {
                    "status": 400,
                    "body": {"error": "Bad Request"}
                }
            }
        }
        return examples
    
    def generate_docs(self, module) -> Dict:
        """Generate documentation for all endpoints in a module."""
        doc_data = {
            "info": {
                "title": "API Testing Studio API Documentation",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "description": "Automatically generated API documentation"
            },
            "endpoints": []
        }
        
        # Find all view functions in the module
        for name, func in inspect.getmembers(module):
            if name.endswith('_view') and inspect.isfunction(func):
                endpoint_doc = self.analyze_view_function(func)
                doc_data["endpoints"].append(vars(endpoint_doc))
        
        return doc_data
    
    def save_documentation(self, doc_data: Dict, output_file: str = "docs/api_documentation.json"):
        """Save generated documentation to a file."""
        with open(output_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
            
    def generate_markdown(self, doc_data: Dict, output_file: str = "docs/API.md"):
        """Generate markdown documentation from the API data."""
        markdown = f"""# {doc_data['info']['title']}

Version: {doc_data['info']['version']}
Generated: {doc_data['info']['generated_at']}

{doc_data['info']['description']}

## Endpoints

"""
        for endpoint in doc_data['endpoints']:
            markdown += f"""### {endpoint['path']}
**Method:** {endpoint['method']}

{endpoint['description']}

#### Parameters
"""
            if endpoint['parameters']:
                markdown += "| Name | Type | Required | Default |\n"
                markdown += "|------|------|----------|----------|\n"
                for name, param in endpoint['parameters'].items():
                    markdown += f"| {name} | {param['type']} | {param['required']} | {param['default']} |\n"
            else:
                markdown += "No parameters required.\n"
                
            markdown += "\n#### Security Requirements\n"
            for req in endpoint['security_requirements']:
                markdown += f"- {req}\n"
                
            markdown += "\n#### Examples\n"
            markdown += "**curl:**\n```bash\n"
            markdown += endpoint['examples']['request']['curl']
            markdown += "\n```\n\n**Python:**\n```python\n"
            markdown += endpoint['examples']['request']['python']
            markdown += "\n```\n\n"
            
            markdown += "**Example Response:**\n```json\n"
            markdown += json.dumps(endpoint['examples']['response']['success'], indent=2)
            markdown += "\n```\n\n"
            
        with open(output_file, 'w') as f:
            f.write(markdown)

def generate_documentation():
    """Generate API documentation for the project."""
    import main
    
    generator = APIDocumentationGenerator()
    doc_data = generator.generate_docs(main)
    
    # Save as JSON
    generator.save_documentation(doc_data)
    
    # Generate markdown documentation
    generator.generate_markdown(doc_data)

if __name__ == "__main__":
    generate_documentation()
