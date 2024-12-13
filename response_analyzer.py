import requests
import json
from typing import Dict, Any
import xml.dom.minidom
from utils import calculate_size

def analyze_response(request_data: dict) -> dict:
    """
    Execute the request and analyze the response.
    """
    try:
        # Prepare the request
        response = requests.request(
            method=request_data["method"],
            url=request_data["url"],
            headers=request_data["headers"],
            data=request_data["data"],
            timeout=30
        )

        # Analyze content type
        content_type = response.headers.get('content-type', '').lower()
        
        # Prepare response content
        try:
            if 'application/json' in content_type:
                content = json.loads(response.text)
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                content = xml.dom.minidom.parseString(response.text).toprettyxml()
            else:
                content = response.text
        except:
            content = response.text

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
                'elapsed_time': str(response.elapsed),
                'redirect_count': len(response.history),
                'final_url': response.url,
                'cookies': dict(response.cookies)
            }
        }

        return analysis

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
