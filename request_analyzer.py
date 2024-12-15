import requests
from urllib.parse import urlparse

def analyze_request(request_data: dict) -> dict:
    """
    Analyze the request data and return detailed information with security insights.
    """
    parsed_url = urlparse(request_data["url"])
    
    analysis = {
        "method": request_data["method"],
        "url_analysis": {
            "scheme": parsed_url.scheme,
            "host": parsed_url.netloc,
            "path": parsed_url.path,
            "query_params": parsed_url.query,
            "fragment": parsed_url.fragment,
            "security": {
                "uses_https": parsed_url.scheme == "https",
                "has_sensitive_params": _check_sensitive_params(parsed_url.query),
                "recommendations": []
            }
        },
        "headers": {
            "count": len(request_data["headers"]),
            "details": request_data["headers"],
            "security_analysis": _analyze_request_headers(request_data["headers"]),
            "recommendations": []
        },
        "authentication": {
            "present": False,
            "type": None,
            "security_level": "none"
        }
    }

    # Analyze authentication with enhanced security checks
    auth_headers = [
        ("Authorization", "Bearer", "Bearer Token", "high"),
        ("Authorization", "Basic", "Basic Auth", "medium"),
        ("X-API-Key", None, "API Key", "medium"),
    ]

    for header, prefix, auth_type, security_level in auth_headers:
        if header in request_data["headers"]:
            analysis["authentication"]["present"] = True
            analysis["authentication"]["security_level"] = security_level
            if prefix and request_data["headers"][header].startswith(prefix):
                analysis["authentication"]["type"] = auth_type
            elif not prefix:
                analysis["authentication"]["type"] = auth_type

    # Analyze body with enhanced security and format detection
    if request_data["data"]:
        analysis["body"] = _analyze_request_body(request_data["data"])
    else:
        analysis["body"] = {
            "present": False
        }

    # Add security recommendations
    if not analysis["url_analysis"]["security"]["uses_https"]:
        analysis["url_analysis"]["security"]["recommendations"].append(
            "Consider using HTTPS for secure data transmission"
        )

    # Add overall security score
    analysis["security_score"] = _calculate_security_score(analysis)
    
    return analysis

def _check_sensitive_params(query_string: str) -> bool:
    """Check if query parameters contain potentially sensitive information."""
    sensitive_keywords = {
        'password', 'token', 'key', 'secret', 'auth',
        'pwd', 'pass', 'credential', 'private'
    }
    params = query_string.lower().split('&')
    return any(any(keyword in param for keyword in sensitive_keywords) 
              for param in params)

def _analyze_request_headers(headers: dict) -> dict:
    """Analyze request headers for security and best practices."""
    security_analysis = {
        "content_type_secure": "content-type" in headers,
        "accepts_secure": "accept" in headers,
        "cors_present": "origin" in headers,
        "cache_control": "cache-control" in headers,
        "security_headers": {
            "x-csrf-token": "x-csrf-token" in headers,
            "x-xss-protection": "x-xss-protection" in headers,
            "x-content-type-options": "x-content-type-options" in headers,
        }
    }
    return security_analysis

def _analyze_request_body(data: str) -> dict:
    """Analyze request body with enhanced security checks and format detection."""
    try:
        # Attempt to parse as JSON
        json.loads(data)
        content_type = "json"
    except json.JSONDecodeError:
        try:
            # Attempt to parse as XML
            xml.dom.minidom.parseString(data)
            content_type = "xml"
        except:
            content_type = "raw"

    return {
        "present": True,
        "size_bytes": len(data),
        "content_type": content_type,
        "content_preview": data[:200] + "..." if len(data) > 200 else data,
        "security_analysis": {
            "contains_sensitive_data": _check_sensitive_content(data),
            "size_warning": len(data) > 1000000,  # Warning for payloads > 1MB
            "recommendations": []
        }
    }

def _check_sensitive_content(content: str) -> bool:
    """Check if content contains potentially sensitive information patterns."""
    sensitive_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
        r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN-like patterns
        r'(?i)\b(password|secret|key|token|auth)\b'  # Sensitive keywords
    ]
    return any(re.search(pattern, content) for pattern in re.compile(pattern) 
              for pattern in sensitive_patterns)

def _calculate_security_score(analysis: dict) -> dict:
    """Calculate overall security score and provide recommendations."""
    score = 100
    recommendations = []

    # URL Security (-20 points for HTTP)
    if not analysis["url_analysis"]["security"]["uses_https"]:
        score -= 20
        recommendations.append("Switch to HTTPS for secure communication")

    # Authentication (-30 points for no auth, -15 for basic auth)
    if not analysis["authentication"]["present"]:
        score -= 30
        recommendations.append("Implement authentication for secure access")
    elif analysis["authentication"]["security_level"] == "medium":
        score -= 15
        recommendations.append("Consider using stronger authentication method")

    # Headers Security (-5 points for each missing security header)
    headers_analysis = analysis["headers"]["security_analysis"]["security_headers"]
    for header, present in headers_analysis.items():
        if not present:
            score -= 5
            recommendations.append(f"Add {header} security header")

    # Sensitive Data (-10 points for sensitive data in URL or body)
    if analysis["url_analysis"]["security"]["has_sensitive_params"]:
        score -= 10
        recommendations.append("Remove sensitive data from URL parameters")

    return {
        "score": max(0, score),  # Ensure score doesn't go below 0
        "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F",
        "recommendations": recommendations
    }
