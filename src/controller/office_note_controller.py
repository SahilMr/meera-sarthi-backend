from typing import Optional
from fastapi import status, Header, Path
from fastapi.responses import JSONResponse
from src.schema.office_note_schema import CreateOfficeNoteRequest, ForwardOfficeNoteRequest
from src.service.office_note_service import OfficeNoteService
from src.db.mock_db import inwards_db, office_notes_db

class OfficeNoteController:
    @staticmethod
    async def create_office_note(
        body: CreateOfficeNoteRequest,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            inward_id = body.inward_id
            office_note = body.office_note
            created_by = x_user_id or "system"
            
            if inward_id not in inwards_db:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            if not office_note or not office_note.strip():
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "data": None,
                        "message": "Office note content cannot be empty",
                        "error": "OFFICE_NOTE_REQUIRED"
                    }
                )
                
            office_note_id = OfficeNoteService.create_office_note(
                inward_id, office_note, created_by
            )
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "data": {
                        "office_note_id": office_note_id
                    },
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )

    @staticmethod
    async def fetch_office_note_detail(
        office_note_id: str = Path(..., description="The unique ID of the office note")
    ):
        try:
            note = OfficeNoteService.get_office_note_by_id(office_note_id)
            if note is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Office note not found",
                        "error": "OFFICE_NOTE_FOUND"
                    }
                )
                
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "data": [note],
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )

    @staticmethod
    async def forward_office_note(
        body: ForwardOfficeNoteRequest,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            office_note_id = body.office_note_id
            forward_to = body.forward_to
            acted_by = x_user_id or "system"
            
            if office_note_id not in office_notes_db:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Office note not found",
                        "error": "OFFICE_NOTE_FOUND"
                    }
                )
                
            success = OfficeNoteService.forward_office_note(office_note_id, forward_to, acted_by)
            if not success:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Office note not found",
                        "error": "OFFICE_NOTE_FOUND"
                    }
                )
                
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )
