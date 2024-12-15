import requests
import json
import time
from typing import Dict, Any, List
import xml.dom.minidom
from utils import calculate_size, analyze_security_headers

def analyze_response(request_data: dict) -> dict:
    """
    Execute the request and analyze the response with detailed timing and security analysis.
    """
    try:
        timing = {}
        metrics = {}
        start_time = time.time()

        # DNS lookup and connection establishment
        session = requests.Session()
        
        # Create an adapter to capture connection metrics
        adapter = requests.adapters.HTTPAdapter()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        timing['session_setup'] = (time.time() - start_time) * 1000

        # Prepare and send the request with detailed timing
        start_request = time.time()
        try:
            # Record DNS lookup start
            dns_start = time.time()
            # Force DNS lookup
            from urllib.parse import urlparse
            import socket
            parsed_url = urlparse(request_data["url"])
            socket.gethostbyname(parsed_url.hostname)
            timing['dns_lookup'] = (time.time() - dns_start) * 1000
            
            # Send the request and measure connect time
            connect_start = time.time()
            response = session.request(
                method=request_data["method"],
                url=request_data["url"],
                headers=request_data["headers"],
                data=request_data["data"],
                timeout=30
            )
            timing['connect_time'] = (time.time() - connect_start) * 1000
            timing['request_time'] = (time.time() - start_request) * 1000
            
            # Calculate TLS handshake time for HTTPS
            if request_data["url"].startswith("https"):
                timing['tls_handshake'] = timing['connect_time'] * 0.6  # Approximate TLS portion
            
            # Record response metrics
            metrics.update({
                'response_size': len(response.content),
                'is_compressed': 'gzip' in response.headers.get('content-encoding', '').lower(),
                'connection_reused': 'keep-alive' in response.headers.get('connection', '').lower(),
            })
            
        except socket.gaierror:
            timing['dns_lookup'] = -1  # DNS lookup failed
            raise

        # Analyze content type and prepare response
        content_type = response.headers.get('content-type', '').lower()
        start_processing = time.time()
        
        try:
            if 'application/json' in content_type:
                content = json.loads(response.text)
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                content = xml.dom.minidom.parseString(response.text).toprettyxml()
            else:
                content = response.text
        except:
            content = response.text

        timing['processing_time'] = (time.time() - start_processing) * 1000
        total_time = (time.time() - start_time) * 1000

        # Security analysis
        security_analysis = analyze_security_headers(dict(response.headers))

        # Analyze response
        analysis = {
            'status_code': response.status_code,
            'reason': response.reason,
            'headers': dict(response.headers),
            'content_type': content_type,
            'content': content,
            'raw': response.text,
            'metadata': {
                'encoding': response.encoding,
                'size': calculate_size(response.content),
                'timing': {
                    'total_time': f"{total_time:.2f}ms",
                    'dns_lookup': f"{timing.get('dns_lookup', 0):.2f}ms",
                    'connect_time': f"{timing.get('connect_time', 0):.2f}ms",
                    'tls_handshake': f"{timing.get('tls_handshake', 0):.2f}ms" if 'tls_handshake' in timing else None,
                    'request_time': f"{timing['request_time']:.2f}ms",
                    'processing_time': f"{timing['processing_time']:.2f}ms",
                    'server_time': str(response.elapsed)
                },
                'performance_metrics': {
                    'total_score': _calculate_performance_score(timing, metrics),
                    'compression_enabled': metrics.get('is_compressed', False),
                    'connection_reused': metrics.get('connection_reused', False),
                    'response_size': calculate_size(response.content),
                    'recommendations': _generate_performance_recommendations(timing, metrics)
                },
                'redirect_count': len(response.history),
                'final_url': response.url,
                'cookies': dict(response.cookies),
                'security_analysis': security_analysis
            }
        }

        return analysis

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

def _calculate_performance_score(timing: Dict[str, Any], metrics: Dict[str, Any]) -> int:
    """
    Calculate a performance score based on timing metrics and response characteristics.
    Returns a score from 0-100.
    """
    score = 100
    total_time = float(timing.get('total_time', 0))
    
    # Time-based scoring
    if total_time > 3000:  # More than 3 seconds
        score -= 30
    elif total_time > 1000:  # More than 1 second
        score -= 15
    elif total_time > 500:  # More than 500ms
        score -= 5
    
    # DNS lookup scoring
    dns_time = float(timing.get('dns_lookup', 0))
    if dns_time > 500:
        score -= 10
    elif dns_time > 200:
        score -= 5
    
    # Connection and TLS scoring
    if 'tls_handshake' in timing:
        tls_time = float(timing['tls_handshake'])
        if tls_time > 300:
            score -= 10
        elif tls_time > 100:
            score -= 5
    
    # Response optimization scoring
    if not metrics.get('is_compressed', False):
        score -= 10
    if not metrics.get('connection_reused', False):
        score -= 5
    
    # Response size scoring
    response_size = metrics.get('response_size', 0)
    if response_size > 5_000_000:  # 5MB
        score -= 15
    elif response_size > 1_000_000:  # 1MB
        score -= 5
    
    return max(0, score)  # Ensure score doesn't go below 0

def _generate_performance_recommendations(timing: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
    """
    Generate performance improvement recommendations based on timing and metrics.
    """
    recommendations = []
    total_time = float(timing.get('total_time', 0))
    
    # Time-based recommendations
    if total_time > 1000:
        recommendations.append("Consider implementing caching to improve response times")
    
    # DNS recommendations
    dns_time = float(timing.get('dns_lookup', 0))
    if dns_time > 200:
        recommendations.append("Consider using a DNS pre-fetch or a CDN to reduce DNS lookup time")
    
    # Connection optimization
    if not metrics.get('connection_reused', False):
        recommendations.append("Enable keep-alive connections to reduce connection overhead")
    
    # Compression recommendations
    if not metrics.get('is_compressed', False):
        recommendations.append("Enable response compression (gzip/br) to reduce transfer size")
    
    # Size optimization
    response_size = metrics.get('response_size', 0)
    if response_size > 1_000_000:
        recommendations.append("Consider implementing pagination or response size limits")
    
    # TLS optimization
    if 'tls_handshake' in timing:
        tls_time = float(timing['tls_handshake'])
        if tls_time > 100:
            recommendations.append("Consider implementing TLS session resumption")
    
    return recommendations
from typing import List