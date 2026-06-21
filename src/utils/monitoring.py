import json
import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi import UploadFile

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        message = json.dumps(data, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

class WebSocketLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        try:
            log_msg = record.getMessage()
            # Ignore websocket internal handshake/upgrade logs to avoid loop/clutter
            if "/api/v1/ws" in log_msg or "upgrade" in log_msg.lower():
                return
            
            formatted_msg = self.format(record)
            payload = {
                "type": "log",
                "message": formatted_msg,
                "levelname": record.levelname,
                "name": record.name,
                "asctime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast(payload))
            except RuntimeError:
                pass
        except Exception:
            self.handleError(record)

async def extract_request_info(request: Request) -> dict:
    info = {
        "method": request.method,
        "path": request.url.path,
        "params": {}
    }
    
    if request.url.path == "/api/v1/ws":
        return info

    info["params"].update(dict(request.query_params))
    
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        try:
            body_bytes = await request.body()
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            
            if body_bytes:
                body_json = json.loads(body_bytes)
                info["params"].update(body_json)
        except Exception:
            pass
            
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            body_bytes = await request.body()
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            
            form = await request.form()
            form_dict = {}
            for key, value in form.items():
                if hasattr(value, "filename"):
                    form_dict[key] = f"File({value.filename})"
                    if hasattr(value, "seek") and callable(value.seek):
                        await value.seek(0)
                else:
                    form_dict[key] = value
            info["params"].update(form_dict)
        except Exception:
            pass
            
    return info

def format_monitor_message(info: dict) -> Optional[str]:
    path = info["path"]
    params = info["params"]
    
    if "create_soft_copy_inward" in path:
        process_type = params.get("process_type", "N/A")
        assigned_to = params.get("assigned_to", "N/A")
        return f"An inward request has been made for {process_type} and has been allocated to {assigned_to}."
        
    elif "forward_inward" in path:
        inward_id = params.get("inward_id", "N/A")
        forward_to = params.get("forward_to", "N/A")
        return f"Inward request {inward_id} has been forwarded to {forward_to}."
        
    elif "create_enclosure" in path:
        inward_id = params.get("inward_id", "N/A")
        privacy_level = params.get("privacy_level", "N/A")
        return f"An enclosure with privacy level {privacy_level} was attached to inward {inward_id}."
        
    elif "mark_off_inward" in path:
        inward_id = params.get("inward_id", "N/A")
        closure = params.get("closure_classification", "N/A")
        return f"Inward request {inward_id} has been closed/marked off as {closure}."
        
    elif "create_office_note" in path:
        inward_id = params.get("inward_id", "N/A")
        return f"An office note has been created for inward {inward_id}."
        
    elif "forward_office_note" in path:
        office_note_id = params.get("office_note_id", "N/A")
        forward_to = params.get("forward_to", "N/A")
        return f"Office note {office_note_id} has been routed to {forward_to}."
        
    elif "fetch_inward" in path:
        parts = path.strip("/").split("/")
        if len(parts) > 2:
            inward_id = parts[-1]
            return f"Administrative record fetched for inward {inward_id}."
        elif params.get("inward_id"):
            return f"Administrative record fetched for inward {params['inward_id']}."
        else:
            assignee = params.get("assigned_to", "all")
            return f"Work queue fetched for assigned user: {assignee}."
            
    elif "office-notes" in path:
        parts = path.strip("/").split("/")
        note_id = parts[-1]
        return f"Office note details fetched for {note_id}."
        
    return None
