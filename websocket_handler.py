import websockets
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WebSocketMessage:
    content: str
    direction: str  # 'sent' or 'received'
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class WebSocketHandler:
    def __init__(self):
        self.connection = None
        self.messages: List[WebSocketMessage] = []
        self.is_connected = False
        self.connection_info = {}
        
    async def connect(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Establish WebSocket connection."""
        try:
            extra_headers = [(k, v) for k, v in (headers or {}).items()]
            self.connection = await websockets.connect(
                url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=20,
                max_size=10_485_760  # 10MB max message size
            )
            
            # Start background task for receiving messages
            asyncio.create_task(self._background_receive())
            
            self.is_connected = True
            self.connection_info = {
                'url': url,
                'headers': headers,
                'connected_at': datetime.now().isoformat(),
                'status': 'Connected'
            }
            return True
        except Exception as e:
            self.connection_info = {
                'url': url,
                'headers': headers,
                'error': str(e),
                'status': 'Connection Failed'
            }
            return False
            
    async def _background_receive(self):
        """Background task to receive messages."""
        try:
            while True:
                if self.connection and self.is_connected:
                    try:
                        message = await self.connection.recv()
                        self.messages.append(WebSocketMessage(
                            content=message,
                            direction='received'
                        ))
                    except websockets.exceptions.ConnectionClosed:
                        self.is_connected = False
                        break
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        break
                else:
                    break
        except Exception as e:
            print(f"Background receive error: {e}")
            self.is_connected = False

    async def disconnect(self):
        """Close WebSocket connection."""
        if self.connection and self.is_connected:
            await self.connection.close()
            self.is_connected = False
            self.connection_info['status'] = 'Disconnected'
            self.connection_info['disconnected_at'] = datetime.now().isoformat()

    async def send_message(self, message: str) -> bool:
        """Send a message through WebSocket connection."""
        if not self.is_connected:
            return False
        try:
            await self.connection.send(message)
            self.messages.append(WebSocketMessage(
                content=message,
                direction='sent'
            ))
            return True
        except Exception as e:
            self.connection_info['last_error'] = str(e)
            return False

    async def receive_message(self) -> Optional[str]:
        """Receive a message from WebSocket connection."""
        if not self.is_connected:
            return None
        try:
            message = await self.connection.recv()
            self.messages.append(WebSocketMessage(
                content=message,
                direction='received'
            ))
            return message
        except Exception as e:
            self.connection_info['last_error'] = str(e)
            return None

    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            **self.connection_info,
            'message_count': len(self.messages),
            'is_connected': self.is_connected
        }

    def get_message_history(self) -> List[Dict[str, Any]]:
        """Get message history."""
        return [
            {
                'content': msg.content,
                'direction': msg.direction,
                'timestamp': msg.timestamp
            }
            for msg in self.messages
        ]

    def clear_message_history(self):
        """Clear message history."""
        self.messages = []
