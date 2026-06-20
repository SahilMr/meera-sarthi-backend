import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from src.router.inward_router import router as inward_router
from src.router.office_note_router import router as office_note_router
from src.db.mock_db import inwards_db, office_notes_db, enclosures_db
from src.utils.common_utils import UPLOAD_DIR

app = FastAPI(
    title="SAARTHI Mock API Backend",
    description="A mock API backend for the SAARTHI application implementing core business flows with a clean src/ layout.",
    version="1.0.0"
)

# Root health status route
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "SAARTHI Backend",
        "version": "1.0.0"
    }

# Register API routers with v1 prefix
app.include_router(inward_router, prefix="/api/v1")
app.include_router(office_note_router, prefix="/api/v1")

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
