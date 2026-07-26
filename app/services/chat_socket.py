from fastapi import WebSocket
from typing import List, Dict
from bot.utils.logger import LogInfo, LogError, LogType
import json


class ChatWebSocketManager:
    """Quản lý các kết nối WebSocket từ Frontend Web Chat."""

    def __init__(self):
        # List các WebSocket active: list of WebSocket objects
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        LogInfo(f"[ChatWS] New client connected. Total active clients: {len(self.active_connections)}", LogType.SYSTEM_STATUS)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            LogInfo(f"[ChatWS] Client disconnected. Remaining active clients: {len(self.active_connections)}", LogType.SYSTEM_STATUS)

    async def broadcast_event(self, event_type: str, data: dict):
        """Broadcast 1 event JSON tới tất cả các WebSocket client đang kết nối."""
        if not self.active_connections:
            LogInfo(f"[ChatWS Broadcast] Event '{event_type}' triggered but no active WebSocket clients connected.", LogType.SYSTEM_STATUS)
            return

        chat_id_info = data.get("chat_id", "N/A")
        msg_id_info = data.get("message_id", "N/A")
        LogInfo(f"[ChatWS Broadcast] Event: '{event_type}' (chat_id={chat_id_info}, msg_id={msg_id_info}) -> Broadcasting to {len(self.active_connections)} client(s)...", LogType.SYSTEM_STATUS)

        payload = json.dumps({
            "event": event_type,
            "data": data
        }, default=str)

        disconnected_clients = []
        sent_count = 0
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
                sent_count += 1
            except Exception as e:
                LogError(f"[ChatWS Broadcast Error] Failed sending to client {connection.client}: {e}", LogType.SYSTEM_STATUS)
                disconnected_clients.append(connection)

        LogInfo(f"[ChatWS Broadcast Done] Successfully sent '{event_type}' to {sent_count}/{len(self.active_connections)} client(s).", LogType.SYSTEM_STATUS)

        # Cleanup disconnected clients
        for client in disconnected_clients:
            self.disconnect(client)


# Global singleton instance
chat_ws_manager = ChatWebSocketManager()
