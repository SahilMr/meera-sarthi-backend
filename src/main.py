import os
import time
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.router.inward_router import router as inward_router
from src.router.office_note_router import router as office_note_router
from src.db.database import init_db
from src.utils.common_utils import UPLOAD_DIR
from src.utils.monitoring import (
    manager, WebSocketLogHandler, extract_request_info, format_monitor_message
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    init_db()
    
    # Attach our custom websocket logger handler to root logger
    ws_handler = WebSocketLogHandler()
    logging.getLogger().addHandler(ws_handler)
    logging.getLogger("uvicorn.access").addHandler(ws_handler)
    
    yield

app = FastAPI(
    title="SAARTHI Mock API Backend",
    description="A mock API backend for the SAARTHI application implementing core business flows with a clean src/ layout.",
    version="1.0.0",
    lifespan=lifespan
)

# Custom HTTP Middleware to intercept and broadcast API request details
@app.middleware("http")
async def monitor_api_requests(request: Request, call_next):
    # Skip WebSocket endpoint and static files serving to prevent circular notifications
    if request.url.path == "/api/v1/ws" or request.url.path.startswith("/frontend"):
        return await call_next(request)
        
    start_time = time.time()
    
    # Safely extract payload and request information
    info = await extract_request_info(request)
    
    # Process request
    response = await call_next(request)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Format a human-readable message and broadcast
    msg = format_monitor_message(info)
    if msg:
        payload = {
            "type": "request",
            "method": info["method"],
            "path": info["path"],
            "status_code": response.status_code,
            "message": msg,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "duration_ms": duration_ms,
            "params": info["params"]
        }
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast(payload))
        
    return response

# Register API routers with v1 prefix
app.include_router(inward_router, prefix="/api/v1")
app.include_router(office_note_router, prefix="/api/v1")

# WebSocket Endpoint for real-time monitoring events
@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any incoming messages or keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper: Download File endpoint
@app.get("/api/v1/download/{filename}", include_in_schema=False)
async def download_file(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=404,
            content={"message": "File not found"}
        )
    return FileResponse(filepath)

# Mount the static files directory for the frontend screen
os.makedirs("frontend", exist_ok=True)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)


