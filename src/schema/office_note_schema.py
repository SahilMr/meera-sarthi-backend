from pydantic import BaseModel

class CreateOfficeNoteRequest(BaseModel):
    inward_id: str
    office_note: str

class ForwardOfficeNoteRequest(BaseModel):
    forward_to: str
    office_note_id: str
