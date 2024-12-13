from typing import Dict, Any, List
import time
from datetime import datetime

def analyze_api_health(response_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze API health based on response metrics and provide recommendations.
    """
    timing = response_info['metadata']['timing']
    total_time = float(timing['total_time'].replace('ms', ''))
    
    health_metrics = {
        'performance': {
            'status': 'good' if total_time < 1000 else 'warning' if total_time < 3000 else 'poor',
            'message': f"Response time is {total_time:.2f}ms",
            'recommendations': []
        },
        'reliability': {
            'status': 'good' if 200 <= response_info['status_code'] < 300 else 'warning' if response_info['status_code'] < 500 else 'poor',
            'message': f"Status code: {response_info['status_code']}",
            'recommendations': []
        },
        'security': {
            'status': 'checking',
            'message': '',
            'recommendations': []
        },
        'best_practices': {
            'status': 'checking',
            'message': '',
            'recommendations': []
        }
    }
    
    # Performance Analysis
    if total_time > 1000:
        health_metrics['performance']['recommendations'].extend([
            "Consider implementing caching mechanisms",
            "Optimize database queries if applicable",
            "Enable compression for large responses"
        ])
    
    # Reliability Analysis
    if response_info['status_code'] >= 400:
        health_metrics['reliability']['recommendations'].extend([
            "Implement proper error handling",
            "Add retry mechanisms for failed requests",
            "Include detailed error messages in responses"
        ])
    
    # Security Analysis
    security = response_info['metadata']['security_analysis']
    missing_headers = [header for header, info in security.items() if not info['present']]
    
    health_metrics['security']['status'] = 'good' if len(missing_headers) == 0 else 'warning' if len(missing_headers) <= 2 else 'poor'
    health_metrics['security']['message'] = f"Missing {len(missing_headers)} security headers"
    if missing_headers:
        health_metrics['security']['recommendations'].extend([
            f"Add {header} header for better security" for header in missing_headers
        ])
    
    # Best Practices Analysis
    best_practices_issues = []
    
    # Check content type
    if 'content-type' not in response_info['headers']:
        best_practices_issues.append("Specify Content-Type header")
    
    # Check cache control
    if 'cache-control' not in response_info['headers']:
        best_practices_issues.append("Add Cache-Control header for better caching")
    
    # Check response size
    response_size = response_info['metadata']['size']
    if 'MB' in response_size and float(response_size.split()[0]) > 1:
        best_practices_issues.append("Large response size - consider pagination or data filtering")
    
    health_metrics['best_practices']['status'] = 'good' if len(best_practices_issues) == 0 else 'warning'
    health_metrics['best_practices']['message'] = f"Found {len(best_practices_issues)} best practice issues"
    health_metrics['best_practices']['recommendations'] = best_practices_issues
    
    return health_metrics

def get_optimization_suggestions(request_info: Dict[str, Any], response_info: Dict[str, Any]) -> List[str]:
    """
    Generate optimization suggestions based on request and response analysis.
    """
    suggestions = []
    
    # Analyze request headers
    if 'Accept-Encoding' not in request_info['headers']:
        suggestions.append("Add 'Accept-Encoding' header to enable compression")
    
    if 'If-None-Match' not in request_info['headers'] and 'etag' in response_info['headers']:
        suggestions.append("Implement ETag-based caching to reduce bandwidth")
    
    # Analyze response
    if response_info['metadata']['redirect_count'] > 0:
        suggestions.append("Multiple redirects detected - consider using direct URLs")
    
    # Analyze timing
    timing = response_info['metadata']['timing']
    request_time = float(timing['request_time'].replace('ms', ''))
    if request_time > 500:
        suggestions.append("High request time - consider implementing request caching or CDN")
    
    return suggestions
