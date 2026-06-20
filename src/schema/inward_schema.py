from pydantic import BaseModel

class ForwardInwardRequest(BaseModel):
    forward_to: str
    inward_id: str

class MarkOffInwardRequest(BaseModel):
    inward_id: str
    closure_classification: str
    file_number: str
    remarks: str
