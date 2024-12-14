import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class Collection:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.requests = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "requests": self.requests,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class CollectionManager:
    def __init__(self):
        self.collections_dir = Path("collections")
        self.collections_dir.mkdir(exist_ok=True)
        self.env_file = self.collections_dir / "environments.json"
        self.load_environments()

    def load_environments(self):
        """Load environment variables from file."""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                self.environments = json.load(f)
        else:
            self.environments = {
                "default": {},
                "development": {},
                "production": {}
            }
            self.save_environments()

    def save_environments(self):
        """Save environment variables to file."""
        with open(self.env_file, 'w') as f:
            json.dump(self.environments, f, indent=2)

    def create_collection(self, name: str, description: str = "") -> Collection:
        """Create a new collection."""
        collection = Collection(name, description)
        file_path = self.collections_dir / f"{name.lower().replace(' ', '_')}.json"
        self.save_collection(collection, file_path)
        return collection

    def save_collection(self, collection: Collection, file_path: Optional[Path] = None):
        """Save a collection to file."""
        if file_path is None:
            file_path = self.collections_dir / f"{collection.name.lower().replace(' ', '_')}.json"
        with open(file_path, 'w') as f:
            json.dump(collection.to_dict(), f, indent=2)

    def list_collections(self) -> List[str]:
        """List all available collections."""
        return [f.stem for f in self.collections_dir.glob("*.json") if f.name != "environments.json"]

    def get_collection(self, name: str) -> Optional[Collection]:
        """Get a collection by name."""
        file_path = self.collections_dir / f"{name.lower().replace(' ', '_')}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                collection = Collection(data["name"], data["description"])
                collection.requests = data["requests"]
                collection.created_at = data["created_at"]
                collection.updated_at = data["updated_at"]
                return collection
        return None

    def add_request_to_collection(self, collection_name: str, request_data: dict, name: str = "", description: str = ""):
        """Add a request to a collection with optional name and description."""
        collection = self.get_collection(collection_name)
        if collection:
            request_entry = {
                "name": name or f"Request {len(collection.requests) + 1}",
                "description": description,
                "request_data": request_data,
                "added_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "tags": []
            }
            collection.requests.append(request_entry)
            collection.updated_at = datetime.now().isoformat()
            self.save_collection(collection)
            
    def get_request_template(self, collection_name: str, request_name: str) -> Optional[dict]:
        """Get a request template by name from a collection."""
        collection = self.get_collection(collection_name)
        if collection:
            for request in collection.requests:
                if request["name"] == request_name:
                    return request["request_data"]
        return None

    def get_environment(self, name: str) -> Dict:
        """Get environment variables for a specific environment."""
        return self.environments.get(name, {})

    def set_environment_variable(self, env_name: str, key: str, value: str):
        """Set an environment variable."""
        if env_name not in self.environments:
            self.environments[env_name] = {}
        self.environments[env_name][key] = value
        self.save_environments()

    def delete_environment_variable(self, env_name: str, key: str):
        """Delete an environment variable."""
        if env_name in self.environments and key in self.environments[env_name]:
            del self.environments[env_name][key]
            self.save_environments()

    def interpolate_variables(self, text: str, environment: str) -> str:
        """Replace environment variables in text with their values."""
        env_vars = self.environments.get(environment, {})
        for key, value in env_vars.items():
            text = text.replace(f"{{${key}}}", value)
        return text

