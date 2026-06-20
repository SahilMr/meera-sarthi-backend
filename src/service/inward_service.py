import os
from datetime import datetime
from typing import List, Dict, Optional
from src.db.mock_db import (
    inwards_db, enclosures_db, 
    get_next_inward_seq, get_next_enclosure_seq
)
from src.utils.common_utils import generate_inward_id, create_audit_record

class InwardService:
    @staticmethod
    def create_soft_copy_inward(data: dict, file_name: str, created_by: str) -> str:
        seq = get_next_inward_seq()
        year = int(data.get("year", datetime.now().year))
        inward_id = generate_inward_id(
            department=data.get("department", "GEN"),
            division=data.get("division", "GEN"),
            seq=seq,
            year=year
        )
        
        inward_record = {
            "inward_id": inward_id,
            "department": data.get("department"),
            "division": data.get("division"),
            "sub_section": data.get("sub_section"),
            "case_access_level": data.get("case_access_level"),
            "privacy_level": data.get("privacy_level"),
            "inward_priority_level": data.get("inward_priority_level"),
            "year": year,
            "inward_file": file_name,
            "inward_subject": data.get("inward_subject"),
            "inward_type": data.get("inward_type"),
            "from_which_office": data.get("from_which_office"),
            "from_which_department": data.get("from_which_department"),
            "inward_date": data.get("inward_date"),
            "letter_type": data.get("letter_type"),
            "date_of_receipt": data.get("date_of_receipt"),
            "estimated_date_of_closure": data.get("estimated_date_of_closure"),
            "process_type": data.get("process_type"),
            "letter_language": data.get("letter_language"),
            "assigned_to": data.get("assigned_to"),
            "status": "registered",
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "audit_history": [
                create_audit_record(
                    "create_soft_copy_inward", 
                    created_by, 
                    f"Inward registered and assigned to {data.get('assigned_to')}"
                )
            ],
            "office_notes": [],
            "enclosures": [],
            "closure_classification": None,
            "file_number": None,
            "remarks": None,
            "marked_off_on": None
        }
        
        inwards_db[inward_id] = inward_record
        return inward_id

    @staticmethod
    def get_inward_by_id(inward_id: str) -> Optional[dict]:
        if inward_id not in inwards_db:
            return None
        # Copy to return
        record = inwards_db[inward_id].copy()
        # Clean helper fields not in the public schema
        record.pop("office_notes", None)
        record.pop("enclosures", None)
        return record

    @staticmethod
    def get_inwards_list(assigned_to: Optional[str] = None, page: int = 1, limit: int = 10) -> List[dict]:
        filtered_inwards = []
        for record in inwards_db.values():
            if assigned_to is None or record["assigned_to"] == assigned_to:
                rec_copy = record.copy()
                rec_copy.pop("office_notes", None)
                rec_copy.pop("enclosures", None)
                filtered_inwards.append(rec_copy)
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        return filtered_inwards[start:end]

    @staticmethod
    def forward_inward(inward_id: str, forward_to: str, acted_by: str) -> bool:
        if inward_id not in inwards_db:
            return False
        
        inward = inwards_db[inward_id]
        old_owner = inward["assigned_to"]
        inward["assigned_to"] = forward_to
        inward["status"] = "forwarded"
        
        inward["audit_history"].append(
            create_audit_record("forward_inward", acted_by, f"Ownership reassigned from {old_owner} to {forward_to}")
        )
        return True

    @staticmethod
    def create_enclosure(inward_id: str, filename: str, privacy_level: str, created_by: str, original_filename: Optional[str] = None) -> Optional[str]:
        if inward_id not in inwards_db:
            return None
        
        seq = get_next_enclosure_seq()
        enclosure_id = f"ENC-{seq:04d}"
        
        enclosure_record = {
            "enclosure_id": enclosure_id,
            "inward_id": inward_id,
            "filename": filename,
            "privacy_level": privacy_level,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by
        }
        
        enclosures_db[enclosure_id] = enclosure_record
        
        # Link to inward and log audit
        display_name = original_filename or filename
        inwards_db[inward_id]["enclosures"].append(enclosure_id)
        inwards_db[inward_id]["audit_history"].append(
            create_audit_record(
                "create_enclosure",
                created_by,
                f"Enclosure {enclosure_id} ({display_name}) attached with privacy level {privacy_level}"
            )
        )
        return enclosure_id

    @staticmethod
    def mark_off_inward(inward_id: str, closure_classification: str, file_number: str, remarks: str, acted_by: str) -> Optional[dict]:
        if inward_id not in inwards_db:
            return None
        
        inward = inwards_db[inward_id]
        # Check if already marked off
        if inward["status"] == "marked_off":
            return {"error": "INWARD_ALREADY_MARKED_OFF"}
        
        marked_off_on = datetime.now().isoformat()
        inward["status"] = "marked_off"
        inward["marked_off_on"] = marked_off_on
        inward["closure_classification"] = closure_classification
        inward["file_number"] = file_number
        inward["remarks"] = remarks
        
        inward["audit_history"].append(
            create_audit_record(
                "mark_off_inward",
                acted_by,
                f"Inward marked off. Classification: {closure_classification}, File: {file_number}, Remarks: {remarks}"
            )
        )
        return {
            "inward_id": inward_id,
            "status": "marked_off",
            "marked_off_on": marked_off_on
        }
