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

def _calculate_performance_score(timing: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate detailed performance metrics and scores based on timing and response characteristics.
    Returns a dictionary with scores and detailed analysis.
    """
    score = 100
    analysis = {
        'scores': {},
        'bottlenecks': [],
        'metrics': {},
        'optimization_opportunities': []
    }
    
    # Calculate TTFB (Time To First Byte)
    ttfb = float(timing.get('dns_lookup', 0)) + float(timing.get('connect_time', 0))
    if 'tls_handshake' in timing:
        ttfb += float(timing['tls_handshake'])
    
    analysis['metrics']['ttfb'] = f"{ttfb:.2f}ms"
    
    # Time-based scoring
    total_time = float(timing.get('total_time', 0))
    analysis['metrics']['total_time'] = f"{total_time:.2f}ms"
    
    if total_time > 3000:  # More than 3 seconds
        score -= 30
        analysis['bottlenecks'].append("High total response time")
    elif total_time > 1000:  # More than 1 second
        score -= 15
        analysis['optimization_opportunities'].append("Response time optimization needed")
    elif total_time > 500:  # More than 500ms
        score -= 5
        analysis['optimization_opportunities'].append("Minor response time improvements possible")
    
    # DNS lookup analysis
    dns_time = float(timing.get('dns_lookup', 0))
    analysis['metrics']['dns_time'] = f"{dns_time:.2f}ms"
    
    if dns_time > 500:
        score -= 10
        analysis['bottlenecks'].append("Slow DNS resolution")
    elif dns_time > 200:
        score -= 5
        analysis['optimization_opportunities'].append("DNS resolution optimization recommended")
    
    # Network latency analysis
    latency = float(timing.get('connect_time', 0)) - dns_time
    analysis['metrics']['network_latency'] = f"{latency:.2f}ms"
    
    if latency > 200:
        score -= 10
        analysis['bottlenecks'].append("High network latency")
        analysis['optimization_opportunities'].append("Consider using a CDN or closer server location")
    
    # TLS analysis
    if 'tls_handshake' in timing:
        tls_time = float(timing['tls_handshake'])
        analysis['metrics']['tls_time'] = f"{tls_time:.2f}ms"
        
        if tls_time > 300:
            score -= 10
            analysis['bottlenecks'].append("Slow TLS handshake")
            analysis['optimization_opportunities'].append("Enable TLS session resumption")
        elif tls_time > 100:
            score -= 5
            analysis['optimization_opportunities'].append("TLS optimization possible")
    
    # Response optimization analysis
    if not metrics.get('is_compressed', False):
        score -= 10
        analysis['optimization_opportunities'].append("Enable response compression")
    
    if not metrics.get('connection_reused', False):
        score -= 5
        analysis['optimization_opportunities'].append("Implement connection reuse")
    
    # Response size analysis
    response_size = metrics.get('response_size', 0)
    if response_size > 5_000_000:  # 5MB
        score -= 15
        analysis['bottlenecks'].append("Large response size")
        analysis['optimization_opportunities'].append("Implement pagination or response size limits")
    elif response_size > 1_000_000:  # 1MB
        score -= 5
        analysis['optimization_opportunities'].append("Consider response size optimization")
    
    # Calculate performance grade
    analysis['scores'] = {
        'total': max(0, score),
        'ttfb': 100 - (ttfb / 10 if ttfb < 1000 else 100),
        'network': 100 - (latency / 2 if latency < 200 else 100),
        'optimization': 100 if metrics.get('is_compressed', False) and metrics.get('connection_reused', False) else 50
    }
    
    return analysis

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