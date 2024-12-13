import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class HistoryEntry:
    timestamp: str
    curl_command: str
    request_info: Dict
    response_info: Dict
    success: bool
    execution_time: float

class HistoryManager:
    def __init__(self):
        self.history: List[HistoryEntry] = []
        self.max_entries = 50  # Keep last 50 requests
    
    def add_entry(self, curl_command: str, request_info: Dict, 
                 response_info: Dict, success: bool, execution_time: float) -> None:
        """Add a new entry to the history."""
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            curl_command=curl_command,
            request_info=request_info,
            response_info=response_info,
            success=success,
            execution_time=execution_time
        )
        self.history.append(entry)
        if len(self.history) > self.max_entries:
            self.history.pop(0)  # Remove oldest entry
    
    def get_history(self) -> List[HistoryEntry]:
        """Get all history entries."""
        return self.history
    
    def get_last_entry(self) -> Optional[HistoryEntry]:
        """Get the most recent entry."""
        return self.history[-1] if self.history else None
    
    def compare_responses(self, entry1: HistoryEntry, entry2: HistoryEntry) -> Dict:
        """Compare two responses and highlight differences."""
        comparison = {
            'status_code_match': entry1.response_info['status_code'] == entry2.response_info['status_code'],
            'timing_difference': abs(entry1.execution_time - entry2.execution_time),
            'header_differences': {},
            'content_size_difference': None
        }
        
        # Compare headers
        headers1 = set(entry1.response_info['headers'].keys())
        headers2 = set(entry2.response_info['headers'].keys())
        comparison['header_differences'] = {
            'only_in_first': list(headers1 - headers2),
            'only_in_second': list(headers2 - headers1),
            'different_values': []
        }
        
        # Compare common headers
        for header in headers1 & headers2:
            if entry1.response_info['headers'][header] != entry2.response_info['headers'][header]:
                comparison['header_differences']['different_values'].append(header)
        
        return comparison
