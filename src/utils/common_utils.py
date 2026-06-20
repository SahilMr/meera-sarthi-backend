import os
from datetime import datetime

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_inward_id(department: str, division: str, seq: int, year: int) -> str:
    """
    Generates a unique inward identifier matching the RBI style format:
    e.g. CO.DBR.LEGIS.no.No.S92\2025-2026
    """
    dept_clean = department.upper().replace(" ", "")
    div_clean = division.upper().replace(" ", "")
    return f"CO.{dept_clean}.{div_clean}.no.No.S{seq}\\{year}-{year+1}"

def create_audit_record(action: str, acted_by: str, details: str) -> dict:
    """
    Returns an audit trail record format.
    """
    return {
        "action": action,
        "acted_by": acted_by,
        "acted_at": datetime.now().isoformat(),
        "details": details
    }
