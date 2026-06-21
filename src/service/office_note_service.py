from datetime import datetime
from typing import Optional
from src.db.database import get_db_connection, get_next_sequence
from src.service.inward_service import InwardService

class OfficeNoteService:
    @staticmethod
    def office_note_exists(office_note_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM office_notes WHERE office_note_id = ?;", (office_note_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def create_office_note(inward_id: str, office_note_text: str, created_by: str) -> Optional[str]:
        if not InwardService.inward_exists(inward_id):
            return None
        
        seq = get_next_sequence("office_note")
        office_note_id = f"ON-{seq:04d}"
        
        created_at = datetime.now().isoformat()
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO office_notes (office_note_id, inward_id, office_note, created_at, created_by, reviewed_by, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (office_note_id, inward_id, office_note_text, created_at, created_by, None, None)
            )
            
            # Log audit trail on parent inward
            details = f"Office note {office_note_id} created"
            cursor.execute(
                """
                INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details)
                VALUES (?, ?, ?, ?, ?);
                """,
                (inward_id, "create_office_note", created_by, created_at, details)
            )
            conn.commit()
            return office_note_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_office_note_by_id(office_note_id: str) -> Optional[dict]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM office_notes WHERE office_note_id = ?;", (office_note_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    @staticmethod
    def forward_office_note(office_note_id: str, forward_to: str, acted_by: str) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT inward_id, reviewed_by FROM office_notes WHERE office_note_id = ?;", (office_note_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            inward_id = row["inward_id"]
            old_reviewer = row["reviewed_by"]
            
            cursor.execute(
                "UPDATE office_notes SET reviewed_by = ? WHERE office_note_id = ?;",
                (forward_to, office_note_id)
            )
            
            # Log to parent inward audit log
            acted_at = datetime.now().isoformat()
            details = f"Office note {office_note_id} routed for review to {forward_to} (previously reviewed by {old_reviewer or 'none'})"
            cursor.execute(
                """
                INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details)
                VALUES (?, ?, ?, ?, ?);
                """,
                (inward_id, "forward_office_note", acted_by, acted_at, details)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
