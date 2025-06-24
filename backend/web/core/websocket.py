"""WebSocket connection manager for real-time LOOP updates."""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from utils.logger import get_logger

logger = get_logger("websocket")

class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Active connections
        self.connections: Dict[str, WebSocket] = {}
        
        # Room-based subscriptions
        self.rooms: Dict[str, Set[str]] = {
            "dashboard": set(),
            "progress": set(), 
            "wifi": set(),
            "system": set()
        }
        
        # Connection health tracking
        self.last_ping: Dict[str, float] = {}
        
    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection and return connection ID."""
        await websocket.accept()
        
        # Generate unique connection ID
        conn_id = f"conn_{int(time.time() * 1000)}_{id(websocket)}"
        
        self.connections[conn_id] = websocket
        self.last_ping[conn_id] = time.time()
        
        logger.info(f"WebSocket connected: {conn_id}")
        
        # Send connection confirmation
        await self._send_to_connection(conn_id, {
            "type": "connection",
            "status": "connected",
            "connection_id": conn_id,
            "timestamp": time.time()
        })
        
        return conn_id
    
    def disconnect(self, conn_id: str):
        """Clean up a disconnected WebSocket."""
        if conn_id in self.connections:
            del self.connections[conn_id]
            
        if conn_id in self.last_ping:
            del self.last_ping[conn_id]
            
        # Remove from all rooms
        for room_connections in self.rooms.values():
            room_connections.discard(conn_id)
            
        logger.info(f"WebSocket disconnected: {conn_id}")
    
    def subscribe(self, conn_id: str, room: str) -> bool:
        """Subscribe connection to a room."""
        if conn_id not in self.connections:
            return False
            
        if room not in self.rooms:
            logger.warning(f"Unknown room: {room}")
            return False
            
        self.rooms[room].add(conn_id)
        logger.debug(f"Connection {conn_id} subscribed to {room}")
        return True
    
    def unsubscribe(self, conn_id: str, room: str) -> bool:
        """Unsubscribe connection from a room."""
        if room not in self.rooms:
            return False
            
        self.rooms[room].discard(conn_id)
        logger.debug(f"Connection {conn_id} unsubscribed from {room}")
        return True
    
    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast message to all connections in a room."""
        if room not in self.rooms:
            logger.warning(f"Cannot broadcast to unknown room: {room}")
            return
            
        room_connections = self.rooms[room].copy()
        logger.info(f"📡 Broadcasting to {room} room: {len(room_connections)} connections")
        
        if len(room_connections) == 0:
            logger.warning(f"No connections subscribed to {room} room")
            return
            
        connections_to_remove = []
        successful_sends = 0
        
        for conn_id in room_connections:
            if conn_id not in self.connections:
                connections_to_remove.append(conn_id)
                continue
                
            try:
                await self._send_to_connection(conn_id, message)
                successful_sends += 1
            except Exception as e:
                logger.warning(f"Failed to send to {conn_id}: {e}")
                connections_to_remove.append(conn_id)
        
        # Clean up dead connections
        for conn_id in connections_to_remove:
            self.rooms[room].discard(conn_id)
            
        logger.info(f"📡 Broadcast complete: {successful_sends} successful, {len(connections_to_remove)} failed")
        
        if connections_to_remove:
            logger.debug(f"Cleaned up {len(connections_to_remove)} dead connections from {room}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients."""
        connections_to_remove = []
        
        for conn_id in list(self.connections.keys()):
            try:
                await self._send_to_connection(conn_id, message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to {conn_id}: {e}")
                connections_to_remove.append(conn_id)
        
        # Clean up dead connections
        for conn_id in connections_to_remove:
            self.disconnect(conn_id)
    
    async def _send_to_connection(self, conn_id: str, message: dict):
        """Send message to a specific connection."""
        if conn_id not in self.connections:
            raise ValueError(f"Connection {conn_id} not found")
            
        websocket = self.connections[conn_id]
        
        # Add timestamp to all messages
        message["timestamp"] = time.time()
        
        await websocket.send_text(json.dumps(message))
    
    async def handle_message(self, conn_id: str, message: dict):
        """Handle incoming message from client."""
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            room = message.get("room")
            if room:
                success = self.subscribe(conn_id, room)
                await self._send_to_connection(conn_id, {
                    "type": "subscribe_response",
                    "room": room,
                    "success": success
                })
        
        elif msg_type == "unsubscribe":
            room = message.get("room")
            if room:
                success = self.unsubscribe(conn_id, room)
                await self._send_to_connection(conn_id, {
                    "type": "unsubscribe_response", 
                    "room": room,
                    "success": success
                })
        
        elif msg_type == "ping":
            self.last_ping[conn_id] = time.time()
            await self._send_to_connection(conn_id, {
                "type": "pong",
                "timestamp": time.time()
            })
        
        else:
            logger.warning(f"Unknown message type from {conn_id}: {msg_type}")
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "rooms": {room: len(connections) for room, connections in self.rooms.items()},
            "healthy_connections": sum(1 for conn_id, last_ping in self.last_ping.items() 
                                     if time.time() - last_ping < 60)  # 60s timeout
        }

# Global connection manager instance
manager = ConnectionManager() 