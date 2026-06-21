from pydantic import BaseModel
from typing import Optional

class ForwardInwardRequest(BaseModel):
    forward_to: str
    inward_id: str

class MarkOffInwardRequest(BaseModel):
    inward_id: str
    closure_classification: str
    file_number: str
    remarks: str

class CreateSoftCopyInwardRequest(BaseModel):
    department: str
    division: str
    sub_section: str
    case_access_level: str
    privacy_level: str
    inward_priority_level: str
    year: int
    inward_file: str
    inward_subject: str
    inward_type: str
    from_which_office: str
    from_which_department: str
    inward_date: str
    letter_type: str
    date_of_receipt: str
    estimated_date_of_closure: str
    process_type: str
    letter_language: str
    assigned_to: str
    user_name: Optional[str] = None
