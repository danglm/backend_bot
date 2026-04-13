from typing import Dict, Any

import random

class ApprovalManager:
    """Manages pending leave approvals."""
    def __init__(self):
        # {approver_id: {request_id: str: {requester_id: int, chat_id: int, data: Dict[str, Any]}}}
        self._pending: Dict[int, Dict[str, Dict[str, Any]]] = {}

    def add_pending(self, approver_id: int, requester_id: int, chat_id: int, data: Dict[str, Any]) -> str:
        """Store a pending approval request and return its unique ID."""
        if approver_id not in self._pending:
            self._pending[approver_id] = {}
        
        # Generate a unique 4-digit ID for this approver's queue
        while True:
            req_id = str(random.randint(1000, 9999))
            if req_id not in self._pending[approver_id]:
                break
        
        self._pending[approver_id][req_id] = {
            "requester_id": requester_id,
            "chat_id": chat_id,
            "data": data,
            "id": req_id
        }
        return req_id

    def get_pending(self, approver_id: int, req_id: str = None) -> Dict[str, Any]:
        """Retrieve a specific pending request or the most recent one if no ID provided."""
        approver_requests = self._pending.get(approver_id, {})
        if not approver_requests:
            return None
        
        if req_id:
            return approver_requests.get(req_id)
        
        # Fallback to the last added request if no ID is specified
        last_id = list(approver_requests.keys())[-1]
        return approver_requests[last_id]

    def clear_pending(self, approver_id: int, req_id: str):
        """Remove a specific pending approval request."""
        if approver_id in self._pending and req_id in self._pending[approver_id]:
            del self._pending[approver_id][req_id]
            if not self._pending[approver_id]:
                del self._pending[approver_id]

class RequestTracker:
    """Tracks mappings between user request messages and bot summary messages."""
    def __init__(self):
        # {chat_id: {user_msg_id: bot_msg_id}}
        self._mappings: Dict[int, Dict[int, int]] = {}

    def track(self, chat_id: int, user_msg_id: int, bot_msg_id: int):
        if chat_id not in self._mappings:
            self._mappings[chat_id] = {}
        self._mappings[chat_id][user_msg_id] = bot_msg_id

    def get_summary_id(self, chat_id: int, user_msg_id: int) -> int:
        return self._mappings.get(chat_id, {}).get(user_msg_id)

    def clear(self, chat_id: int, user_msg_id: int):
        if chat_id in self._mappings and user_msg_id in self._mappings[chat_id]:
            del self._mappings[chat_id][user_msg_id]

# Singleton instances
approval_manager = ApprovalManager()
request_tracker = RequestTracker()
