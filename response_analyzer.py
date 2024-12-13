import requests
import json
import time
from typing import Dict, Any
import xml.dom.minidom
from utils import calculate_size, analyze_security_headers

def analyze_response(request_data: dict) -> dict:
    """
    Execute the request and analyze the response with detailed timing and security analysis.
    """
    try:
        timing = {}
        start_time = time.time()

        # DNS lookup and connection establishment
        session = requests.Session()
        timing['session_setup'] = (time.time() - start_time) * 1000

        # Prepare the request
        start_request = time.time()
        response = session.request(
            method=request_data["method"],
            url=request_data["url"],
            headers=request_data["headers"],
            data=request_data["data"],
            timeout=30
        )
        timing['request_time'] = (time.time() - start_request) * 1000

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
        security_analysis = analyze_security_headers(response.headers)

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
                    'session_setup': f"{timing['session_setup']:.2f}ms",
                    'request_time': f"{timing['request_time']:.2f}ms",
                    'processing_time': f"{timing['processing_time']:.2f}ms",
                    'server_time': str(response.elapsed)
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
