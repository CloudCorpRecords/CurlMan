import requests
from urllib.parse import urlparse

def analyze_request(request_data: dict) -> dict:
    """
    Analyze the request data and return detailed information.
    """
    parsed_url = urlparse(request_data["url"])
    
    analysis = {
        "method": request_data["method"],
        "url_analysis": {
            "scheme": parsed_url.scheme,
            "host": parsed_url.netloc,
            "path": parsed_url.path,
            "query_params": parsed_url.query,
            "fragment": parsed_url.fragment
        },
        "headers": {
            "count": len(request_data["headers"]),
            "details": request_data["headers"]
        },
        "authentication": {
            "present": False,
            "type": None
        }
    }

    # Analyze authentication
    auth_headers = [
        ("Authorization", "Bearer", "Bearer Token"),
        ("Authorization", "Basic", "Basic Auth"),
        ("X-API-Key", None, "API Key"),
    ]

    for header, prefix, auth_type in auth_headers:
        if header in request_data["headers"]:
            analysis["authentication"]["present"] = True
            if prefix and request_data["headers"][header].startswith(prefix):
                analysis["authentication"]["type"] = auth_type
            elif not prefix:
                analysis["authentication"]["type"] = auth_type

    # Analyze body if present
    if request_data["data"]:
        analysis["body"] = {
            "present": True,
            "size_bytes": len(request_data["data"]),
            "content_preview": request_data["data"][:200] + "..." if len(request_data["data"]) > 200 else request_data["data"]
        }
    else:
        analysis["body"] = {
            "present": False
        }

    return analysis
