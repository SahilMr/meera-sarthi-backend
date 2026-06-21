import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from src.db.database import get_db_connection, get_next_sequence
from src.utils.common_utils import generate_inward_id

class InwardService:
    @staticmethod
    def inward_exists(inward_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM inwards WHERE inward_id = ?;", (inward_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def create_soft_copy_inward(data: dict, file_name: str, created_by: str) -> str:
        seq = get_next_sequence("inward")
        year = int(data.get("year", datetime.now().year))
        inward_id = generate_inward_id(
            department=data.get("department", "GEN"),
            division=data.get("division", "GEN"),
            seq=seq,
            year=year
        )
        
        created_at = datetime.now().isoformat()
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inwards (
                    inward_id, department, division, sub_section, case_access_level, privacy_level,
                    inward_priority_level, year, inward_file, inward_subject, inward_type,
                    from_which_office, from_which_department, inward_date, letter_type,
                    date_of_receipt, estimated_date_of_closure, process_type, letter_language,
                    assigned_to, status, created_at, created_by, closure_classification,
                    file_number, remarks, marked_off_on
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    inward_id,
                    data.get("department"),
                    data.get("division"),
                    data.get("sub_section"),
                    data.get("case_access_level"),
                    data.get("privacy_level"),
                    data.get("inward_priority_level"),
                    year,
                    file_name,
                    data.get("inward_subject"),
                    data.get("inward_type"),
                    data.get("from_which_office"),
                    data.get("from_which_department"),
                    data.get("inward_date"),
                    data.get("letter_type"),
                    data.get("date_of_receipt"),
                    data.get("estimated_date_of_closure"),
                    data.get("process_type"),
                    data.get("letter_language"),
                    data.get("assigned_to"),
                    "registered",
                    created_at,
                    created_by,
                    None,
                    None,
                    None,
                    None
                )
            )
            
            # Log audit
            details = f"Inward registered and assigned to {data.get('assigned_to')}"
            cursor.execute(
                """
                INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details)
                VALUES (?, ?, ?, ?, ?);
                """,
                (inward_id, "create_soft_copy_inward", created_by, created_at, details)
            )
            conn.commit()
            return inward_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_inward_by_id(inward_id: str) -> Optional[dict]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inwards WHERE inward_id = ?;", (inward_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            cursor.execute(
                "SELECT action, acted_by, acted_at, details FROM audit_logs WHERE inward_id = ? ORDER BY id ASC;",
                (inward_id,)
            )
            audit_rows = cursor.fetchall()
            audit_history = [dict(r) for r in audit_rows]
            
            record = dict(row)
            record["audit_history"] = audit_history
            return record
        finally:
            conn.close()

    @staticmethod
    def get_inwards_list(assigned_to: Optional[str] = None, page: int = 1, limit: int = 10) -> List[dict]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            offset = (page - 1) * limit
            if assigned_to is not None:
                cursor.execute(
                    "SELECT * FROM inwards WHERE assigned_to = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                    (assigned_to, limit, offset)
                )
            else:
                cursor.execute(
                    "SELECT * FROM inwards ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                    (limit, offset)
                )
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                cursor.execute(
                    "SELECT action, acted_by, acted_at, details FROM audit_logs WHERE inward_id = ? ORDER BY id ASC;",
                    (row["inward_id"],)
                )
                audit_rows = cursor.fetchall()
                audit_history = [dict(r) for r in audit_rows]
                
                record = dict(row)
                record["audit_history"] = audit_history
                results.append(record)
            
            return results
        finally:
            conn.close()

    @staticmethod
    def forward_inward(inward_id: str, forward_to: str, acted_by: str) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT assigned_to, status FROM inwards WHERE inward_id = ?;", (inward_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            old_owner = row["assigned_to"]
            cursor.execute(
                "UPDATE inwards SET assigned_to = ?, status = 'forwarded' WHERE inward_id = ?;",
                (forward_to, inward_id)
            )
            
            # Log audit
            acted_at = datetime.now().isoformat()
            details = f"Ownership reassigned from {old_owner} to {forward_to}"
            cursor.execute(
                "INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details) VALUES (?, ?, ?, ?, ?);",
                (inward_id, "forward_inward", acted_by, acted_at, details)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def create_enclosure(inward_id: str, filename: str, privacy_level: str, created_by: str, original_filename: Optional[str] = None) -> Optional[str]:
        if not InwardService.inward_exists(inward_id):
            return None
        
        seq = get_next_sequence("enclosure")
        enclosure_id = f"ENC-{seq:04d}"
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            created_at = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO enclosures (enclosure_id, inward_id, filename, privacy_level, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (enclosure_id, inward_id, filename, privacy_level, created_at, created_by)
            )
            
            display_name = original_filename or filename
            details = f"Enclosure {enclosure_id} ({display_name}) attached with privacy level {privacy_level}"
            cursor.execute(
                "INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details) VALUES (?, ?, ?, ?, ?);",
                (inward_id, "create_enclosure", created_by, created_at, details)
            )
            conn.commit()
            return enclosure_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def mark_off_inward(inward_id: str, closure_classification: str, file_number: str, remarks: str, acted_by: str) -> Optional[dict]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM inwards WHERE inward_id = ?;", (inward_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            if row["status"] == "marked_off":
                return {"error": "INWARD_ALREADY_MARKED_OFF"}
            
            marked_off_on = datetime.now().isoformat()
            cursor.execute(
                """
                UPDATE inwards
                SET status = 'marked_off', marked_off_on = ?, closure_classification = ?, file_number = ?, remarks = ?
                WHERE inward_id = ?;
                """,
                (marked_off_on, closure_classification, file_number, remarks, inward_id)
            )
            
            details = f"Inward marked off. Classification: {closure_classification}, File: {file_number}, Remarks: {remarks}"
            cursor.execute(
                "INSERT INTO audit_logs (inward_id, action, acted_by, acted_at, details) VALUES (?, ?, ?, ?, ?);",
                (inward_id, "mark_off_inward", acted_by, marked_off_on, details)
            )
            conn.commit()
            return {
                "inward_id": inward_id,
                "status": "marked_off",
                "marked_off_on": marked_off_on
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
