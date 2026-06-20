from datetime import datetime
from typing import Optional
from src.db.mock_db import (
    inwards_db, office_notes_db, get_next_office_note_seq
)
from src.utils.common_utils import create_audit_record

class OfficeNoteService:
    @staticmethod
    def create_office_note(inward_id: str, office_note_text: str, created_by: str) -> Optional[str]:
        if inward_id not in inwards_db:
            return None
        
        seq = get_next_office_note_seq()
        office_note_id = f"ON-{seq:04d}"
        
        note_record = {
            "office_note_id": office_note_id,
            "inward_id": inward_id,
            "office_note": office_note_text,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "reviewed_by": None,
            "comments": None
        }
        
        office_notes_db[office_note_id] = note_record
        
        # Link to inward and log audit trail on parent inward
        inwards_db[inward_id]["office_notes"].append(office_note_id)
        inwards_db[inward_id]["audit_history"].append(
            create_audit_record("create_office_note", created_by, f"Office note {office_note_id} created")
        )
        
        return office_note_id

    @staticmethod
    def get_office_note_by_id(office_note_id: str) -> Optional[dict]:
        if office_note_id not in office_notes_db:
            return None
        return office_notes_db[office_note_id]

    @staticmethod
    def forward_office_note(office_note_id: str, forward_to: str, acted_by: str) -> bool:
        if office_note_id not in office_notes_db:
            return False
        
        note = office_notes_db[office_note_id]
        inward_id = note["inward_id"]
        old_reviewer = note["reviewed_by"]
        note["reviewed_by"] = forward_to
        
        # Log to parent inward audit log
        if inward_id in inwards_db:
            inwards_db[inward_id]["audit_history"].append(
                create_audit_record(
                    "forward_office_note",
                    acted_by,
                    f"Office note {office_note_id} routed for review to {forward_to} (previously reviewed by {old_reviewer or 'none'})"
                )
            )
        return True
