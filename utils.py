import json
import xml.dom.minidom
from typing import Union, Any

def format_data(data: Any, content_type: str) -> str:
    """
    Format data based on content type.
    """
    if isinstance(data, str):
        if 'application/json' in content_type:
            try:
                return json.dumps(json.loads(data), indent=2)
            except:
                return data
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            try:
                return xml.dom.minidom.parseString(data).toprettyxml()
            except:
                return data
        return data
    elif isinstance(data, (dict, list)):
        return json.dumps(data, indent=2)
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
