import graphene
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass
from urllib.parse import urlencode

@dataclass
class GraphQLRequest:
    query: str
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None

class GraphQLAnalyzer:
    def __init__(self):
        self.schema = None
        self.query_builder = QueryBuilder()

    def format_request(self, request: GraphQLRequest) -> Dict[str, Any]:
        """Format a GraphQL request into a structure compatible with our request analyzer."""
        request_data = {
            "query": request.query,
            "variables": request.variables or {},
        }
        if request.operation_name:
            request_data["operationName"] = request.operation_name

        return {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            "data": json.dumps(request_data)
        }

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and analyze a GraphQL response."""
        return {
            "data": response_data.get("data"),
            "errors": response_data.get("errors"),
            "extensions": response_data.get("extensions"),
            "analysis": {
                "has_errors": bool(response_data.get("errors")),
                "data_fields": self._analyze_data_fields(response_data.get("data", {})),
                "performance_info": response_data.get("extensions", {}).get("performance", {})
            }
        }

    def _analyze_data_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure and content of returned data fields."""
        if not data:
            return {"fields": [], "depth": 0}

        def calculate_depth(obj: Any, current_depth: int = 0) -> int:
            if not isinstance(obj, dict):
                return current_depth
            if not obj:
                return current_depth
            depths = [calculate_depth(value, current_depth + 1) 
                     for value in obj.values() 
                     if isinstance(value, (dict, list))]
            return max(depths) if depths else current_depth

        fields = list(data.keys())
        return {
            "fields": fields,
            "depth": calculate_depth(data),
            "field_count": len(fields)
        }

class QueryBuilder:
    def __init__(self):
        self._query = []
        self._variables = {}
        self._operation_name = None

    def start_operation(self, operation_type: str = "query", name: Optional[str] = None):
        """Start a new GraphQL operation (query/mutation)."""
        self._operation_name = name
        self._query = [f"{operation_type}" + (f" {name}" if name else "") + " {"]
        return self

    def add_field(self, field: str, sub_fields: Optional[list] = None, args: Optional[Dict[str, Any]] = None):
        """Add a field to the query."""
        field_str = field
        if args:
            args_str = ", ".join(f"{k}: ${k}" if k in self._variables else f"{k}: {json.dumps(v)}"
                               for k, v in args.items())
            field_str = f"{field}({args_str})"

        self._query.append("  " + field_str + (" {" if sub_fields else ""))
        
        if sub_fields:
            for sub_field in sub_fields:
                self._query.append("    " + sub_field)
            self._query.append("  }")
        
        return self

    def add_variable(self, name: str, var_type: str, default_value: Any = None):
        """Add a variable to the query."""
        self._variables[name] = {
            "type": var_type,
            "default": default_value
        }
        return self

    def build(self) -> GraphQLRequest:
        """Build and return the complete GraphQL request."""
        # Add variables declaration if any
        if self._variables and self._query[0].startswith(("query", "mutation")):
            variables_decl = ", ".join(
                f"${k}: {v['type']}" + (f" = {json.dumps(v['default'])}" if v['default'] is not None else "")
                for k, v in self._variables.items()
            )
            self._query[0] = self._query[0].replace(" {", f"({variables_decl}) {{")

        # Close the operation
        self._query.append("}")
        
        return GraphQLRequest(
            query="\n".join(self._query),
            variables={k: v['default'] for k, v in self._variables.items() if v['default'] is not None},
            operation_name=self._operation_name
        )

# Example schema for API documentation
class APISchema:
    def __init__(self):
        self.types = {}
        self.queries = {}
        self.mutations = {}

    def add_type(self, name: str, fields: Dict[str, str]):
        """Add a GraphQL type definition."""
        self.types[name] = fields

    def add_query(self, name: str, return_type: str, args: Optional[Dict[str, str]] = None):
        """Add a query definition."""
        self.queries[name] = {
            "return_type": return_type,
            "args": args or {}
        }

    def add_mutation(self, name: str, return_type: str, args: Optional[Dict[str, str]] = None):
        """Add a mutation definition."""
        self.mutations[name] = {
            "return_type": return_type,
            "args": args or {}
        }

    def generate_documentation(self) -> str:
        """Generate markdown documentation for the API schema."""
        docs = ["# GraphQL API Documentation\n"]
        
        if self.types:
            docs.append("## Types\n")
            for type_name, fields in self.types.items():
                docs.append(f"### {type_name}\n")
                for field_name, field_type in fields.items():
                    docs.append(f"- {field_name}: {field_type}")
                docs.append("")

        if self.queries:
            docs.append("## Queries\n")
            for query_name, details in self.queries.items():
                docs.append(f"### {query_name}\n")
                if details["args"]:
                    docs.append("Arguments:")
                    for arg_name, arg_type in details["args"].items():
                        docs.append(f"- {arg_name}: {arg_type}")
                docs.append(f"\nReturns: {details['return_type']}\n")

        if self.mutations:
            docs.append("## Mutations\n")
            for mutation_name, details in self.mutations.items():
                docs.append(f"### {mutation_name}\n")
                if details["args"]:
                    docs.append("Arguments:")
                    for arg_name, arg_type in details["args"].items():
                        docs.append(f"- {arg_name}: {arg_type}")
                docs.append(f"\nReturns: {details['return_type']}\n")

        return "\n".join(docs)
