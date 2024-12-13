import re
import shlex
from urllib.parse import urlparse

def parse_curl_command(curl_command: str) -> dict:
    """
    Parse a curl command into its components.
    """
    # Remove newlines and extra spaces
    curl_command = " ".join(curl_command.strip().split())
    
    try:
        # Split the command respecting quoted strings
        parts = shlex.split(curl_command)
        
        if not parts[0].lower() == "curl":
            raise ValueError("Command must start with 'curl'")

        request_data = {
            "method": "GET",  # Default method
            "url": "",
            "headers": {},
            "data": None,
            "params": {},
        }

        i = 1
        while i < len(parts):
            part = parts[i]
            
            # Handle URL (if not a flag)
            if not part.startswith("-"):
                request_data["url"] = part
                i += 1
                continue

            # Handle flags
            if part in ["-H", "--header"]:
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for {part}")
                header_line = parts[i + 1]
                key, value = header_line.split(":", 1)
                request_data["headers"][key.strip()] = value.strip()
                i += 2

            elif part in ["-X", "--request"]:
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for {part}")
                request_data["method"] = parts[i + 1].upper()
                i += 2

            elif part in ["-d", "--data", "--data-raw"]:
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for {part}")
                request_data["data"] = parts[i + 1]
                if request_data["method"] == "GET":
                    request_data["method"] = "POST"
                i += 2

            else:
                i += 1

        # Validate URL
        if not request_data["url"]:
            raise ValueError("No URL specified in curl command")
        
        parsed_url = urlparse(request_data["url"])
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

        return request_data

    except Exception as e:
        raise ValueError(f"Error parsing curl command: {str(e)}")
