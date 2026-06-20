from fastapi import APIRouter
from src.controller.office_note_controller import OfficeNoteController

router = APIRouter(tags=["Office Notes"])

router.add_api_route(
    "/create_office_note",
    OfficeNoteController.create_office_note,
    methods=["POST"],
    summary="Create office note tied to an inward"
)

router.add_api_route(
    "/office-notes/{office_note_id}",
    OfficeNoteController.fetch_office_note_detail,
    methods=["GET"],
    summary="Fetch office note by ID"
)

router.add_api_route(
    "/forward_office_note",
    OfficeNoteController.forward_office_note,
    methods=["POST"],
    summary="Forward office note to next reviewer"
)
