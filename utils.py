import json
import xml.dom.minidom
from typing import Union, Any, Dict

def format_data(data: Any, content_type: str) -> str:
    """
    Format data based on content type with enhanced formatting.
    """
    if isinstance(data, str):
        if 'application/json' in content_type:
            try:
                # Strip any leading/trailing whitespace
                cleaned_data = data.strip()
                parsed = json.loads(cleaned_data)
                return json.dumps(parsed, indent=2, sort_keys=True)
            except json.JSONDecodeError as e:
                return f"Invalid JSON: {str(e)}\nRaw data: {data}"
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            try:
                return xml.dom.minidom.parseString(data).toprettyxml(indent="  ")
            except:
                return data
        elif 'text/html' in content_type:
            try:
                from bs4 import BeautifulSoup
                return BeautifulSoup(data, 'html.parser').prettify()
            except:
                return data
        return data
    elif isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, sort_keys=True)
    return str(data)

def calculate_size(content: bytes) -> str:
    """
    Calculate human-readable size of content.
    """
    size_bytes = len(content)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def analyze_security_headers(headers: Dict[str, str]) -> Dict[str, Dict[str, Union[bool, str]]]:
    """
    Analyze security-related headers in the response.
    """
    security_headers = {
        'Content-Security-Policy': {
            'present': False,
            'description': 'Helps prevent XSS attacks'
        },
        'X-Content-Type-Options': {
            'present': False,
            'description': 'Prevents MIME-type sniffing'
        },
        'X-Frame-Options': {
            'present': False,
            'description': 'Prevents clickjacking attacks'
        },
        'Strict-Transport-Security': {
            'present': False,
            'description': 'Enforces HTTPS connections'
        },
        'X-XSS-Protection': {
            'present': False,
            'description': 'Provides XSS filtering'
        }
    }
    
    for header in security_headers:
        if header in headers:
            security_headers[header]['present'] = True
            security_headers[header]['value'] = headers[header]
            
    return security_headers
