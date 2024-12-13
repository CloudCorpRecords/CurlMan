from typing import Dict, Optional
import json
import os
from datetime import datetime

class EnvironmentManager:
    def __init__(self):
        self.environments: Dict[str, Dict[str, str]] = {
            "Global": {},
            "Local": {}
        }
        self.active_environment = "Local"
        
    def set_variable(self, name: str, value: str, environment: Optional[str] = None) -> None:
        """Set an environment variable in the specified environment."""
        env = environment or self.active_environment
        if env not in self.environments:
            raise ValueError(f"Environment '{env}' does not exist")
        self.environments[env][name] = value
    
    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable's value, checking active environment first, then global."""
        # Check active environment first
        if name in self.environments[self.active_environment]:
            return self.environments[self.active_environment][name]
        # Fall back to global environment
        return self.environments["Global"].get(name)
    
    def substitute_variables(self, text: str) -> str:
        """Replace {{variable}} placeholders with their values."""
        import re
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self.get_variable(var_name)
            return value if value is not None else match.group(0)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, text)

class RequestTemplate:
    def __init__(self):
        self.templates: Dict[str, Dict] = {}
        
    def save_template(self, name: str, curl_command: str, description: str = "") -> None:
        """Save a curl command as a template."""
        self.templates[name] = {
            "curl_command": curl_command,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
    
    def get_template(self, name: str) -> Optional[Dict]:
        """Retrieve a template by name."""
        template = self.templates.get(name)
        if template:
            template["last_used"] = datetime.now().isoformat()
            return template
        return None
    
    def list_templates(self) -> Dict[str, Dict]:
        """List all available templates."""
        return self.templates
    
    def delete_template(self, name: str) -> bool:
        """Delete a template by name."""
        if name in self.templates:
            del self.templates[name]
            return True
        return False

# Create singleton instances
env_manager = EnvironmentManager()
template_manager = RequestTemplate()
