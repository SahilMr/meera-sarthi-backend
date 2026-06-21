import io
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.db.database import reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    reset_db()

def test_create_soft_copy_inward():
    file_content = b"Mock document content"
    file = io.BytesIO(file_content)
    
    data = {
        "department": "DBR",
        "division": "Legis",
        "sub_section": "Section A",
        "case_access_level": "limited",
        "privacy_level": "confidential",
        "inward_priority_level": "high",
        "year": 2025,
        "inward_subject": "Draft Banking Bill 2025",
        "inward_type": "Legislative Ref",
        "from_which_office": "Central Office",
        "from_which_department": "Legal",
        "inward_date": "2025-06-01",
        "letter_type": "Official letter",
        "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-12-31",
        "process_type": "Standard",
        "letter_language": "English",
        "assigned_to": "officer_bob"
    }
    
    response = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("test_doc.pdf", file, "application/pdf")},
        headers={"X-User-Id": "officer_alice"}
    )
    
    assert response.status_code == 201
    resp_json = response.json()
    assert resp_json["message"] == "Success"
    assert resp_json["error"] is None
    assert "inward_id" in resp_json["data"]
    
    inward_id = resp_json["data"]["inward_id"]
    # Verify the generated inward_id formatting matches RBI style
    assert "CO.DBR.LEGIS.no.No.S" in inward_id
    assert "\\2025-2026" in inward_id


def test_fetch_inward_single_and_list():
    # 1. Create an inward
    file_content = b"Content"
    file = io.BytesIO(file_content)
    data = {
        "department": "DBR",
        "division": "Legis",
        "sub_section": "Sec 1",
        "case_access_level": "wider",
        "privacy_level": "public",
        "inward_priority_level": "medium",
        "year": 2025,
        "inward_subject": "Subject A",
        "inward_type": "Type A",
        "from_which_office": "Office X",
        "from_which_department": "Dept Y",
        "inward_date": "2025-06-01",
        "letter_type": "Ltr",
        "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-06-10",
        "process_type": "Proc A",
        "letter_language": "Hindi",
        "assigned_to": "officer_bob"
    }
    create_resp = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("doc.txt", file, "text/plain")},
        headers={"X-User-Id": "officer_alice"}
    )
    inward_id = create_resp.json()["data"]["inward_id"]
    
    # 2. Fetch specific inward
    fetch_resp = client.get(f"/api/v1/fetch_inward/{inward_id}")
    assert fetch_resp.status_code == 200
    fetch_json = fetch_resp.json()
    assert len(fetch_json["data"]) == 1
    record = fetch_json["data"][0]
    assert record["inward_id"] == inward_id
    assert record["assigned_to"] == "officer_bob"
    assert record["status"] == "registered"
    assert record["created_by"] == "officer_alice"
    assert len(record["audit_history"]) == 1
    assert record["audit_history"][0]["action"] == "create_soft_copy_inward"

    # 3. Fetch specific inward via query param instead of path param
    fetch_query_resp = client.get(f"/api/v1/fetch_inward?inward_id={inward_id}")
    assert fetch_query_resp.status_code == 200
    assert fetch_query_resp.json()["data"][0]["inward_id"] == inward_id
    
    # 4. Fetch list/work queue
    list_resp = client.get("/api/v1/fetch_inward?assigned_to=officer_bob")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1
    assert list_resp.json()["data"][0]["inward_id"] == inward_id

    # Filter with non-existent assignee
    empty_list_resp = client.get("/api/v1/fetch_inward?assigned_to=officer_charlie")
    assert empty_list_resp.status_code == 200
    assert len(empty_list_resp.json()["data"]) == 0

    # 5. Fetch non-existent inward_id (404)
    non_existent_resp = client.get("/api/v1/fetch_inward/CO.NONE.123")
    assert non_existent_resp.status_code == 404
    assert non_existent_resp.json()["error"] == "INWARD_NOT_FOUND"


def test_forward_inward():
    # 1. Create an inward
    file = io.BytesIO(b"Data")
    data = {
        "department": "DBR", "division": "Legis", "sub_section": "Sec 1",
        "case_access_level": "wider", "privacy_level": "public", "inward_priority_level": "medium",
        "year": 2025, "inward_subject": "Subj", "inward_type": "Type",
        "from_which_office": "Office X", "from_which_department": "Legal",
        "inward_date": "2025-06-01", "letter_type": "Ltr", "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-06-10", "process_type": "Proc A",
        "letter_language": "Hindi", "assigned_to": "officer_bob"
    }
    create_resp = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("doc.txt", file, "text/plain")}
    )
    inward_id = create_resp.json()["data"]["inward_id"]

    # 2. Forward the inward
    forward_resp = client.post(
        "/api/v1/forward_inward",
        json={"inward_id": inward_id, "forward_to": "supervisor_clara"},
        headers={"X-User-Id": "officer_bob"}
    )
    assert forward_resp.status_code == 200
    assert forward_resp.json()["message"] == "Success"

    # 3. Retrieve and verify updated owner, status and audit log
    fetch_resp = client.get(f"/api/v1/fetch_inward/{inward_id}")
    record = fetch_resp.json()["data"][0]
    assert record["assigned_to"] == "supervisor_clara"
    assert record["status"] == "forwarded"
    assert len(record["audit_history"]) == 2
    assert record["audit_history"][1]["action"] == "forward_inward"
    assert "officer_bob" in record["audit_history"][1]["acted_by"]
    assert "supervisor_clara" in record["audit_history"][1]["details"]


def test_office_note_flow():
    # 1. Create inward
    file = io.BytesIO(b"Data")
    data = {
        "department": "DBR", "division": "Legis", "sub_section": "Sec 1",
        "case_access_level": "wider", "privacy_level": "public", "inward_priority_level": "medium",
        "year": 2025, "inward_subject": "Subj", "inward_type": "Type",
        "from_which_office": "Office X", "from_which_department": "Legal",
        "inward_date": "2025-06-01", "letter_type": "Ltr", "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-06-10", "process_type": "Proc A",
        "letter_language": "Hindi", "assigned_to": "officer_bob"
    }
    create_resp = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("doc.txt", file, "text/plain")}
    )
    inward_id = create_resp.json()["data"]["inward_id"]

    # 2. Try creating note with empty content (400)
    note_resp_err = client.post(
        "/api/v1/create_office_note",
        json={"inward_id": inward_id, "office_note": ""}
    )
    assert note_resp_err.status_code == 400
    assert note_resp_err.json()["error"] == "OFFICE_NOTE_REQUIRED"

    # 3. Create a valid office note
    note_resp = client.post(
        "/api/v1/create_office_note",
        json={"inward_id": inward_id, "office_note": "This is a detailed analysis and recommendation."},
        headers={"X-User-Id": "officer_bob"}
    )
    assert note_resp.status_code == 201
    note_id = note_resp.json()["data"]["office_note_id"]
    assert "ON-" in note_id

    # 4. Fetch office note detail
    detail_resp = client.get(f"/api/v1/office-notes/{note_id}")
    assert detail_resp.status_code == 200
    note_detail = detail_resp.json()["data"][0]
    assert note_detail["office_note_id"] == note_id
    assert note_detail["inward_id"] == inward_id
    assert note_detail["office_note"] == "This is a detailed analysis and recommendation."
    assert note_detail["created_by"] == "officer_bob"
    assert note_detail["reviewed_by"] is None

    # 5. Forward the office note
    forward_note_resp = client.post(
        "/api/v1/forward_office_note",
        json={"office_note_id": note_id, "forward_to": "supervisor_clara"},
        headers={"X-User-Id": "officer_bob"}
    )
    assert forward_note_resp.status_code == 200
    assert forward_note_resp.json()["message"] == "Success"

    # 6. Re-fetch office note and check reviewed_by
    detail_resp_2 = client.get(f"/api/v1/office-notes/{note_id}")
    note_detail_2 = detail_resp_2.json()["data"][0]
    assert note_detail_2["reviewed_by"] == "supervisor_clara"

    # 7. Check audit log on the inward
    inward_resp = client.get(f"/api/v1/fetch_inward/{inward_id}")
    audit_log = inward_resp.json()["data"][0]["audit_history"]
    # creation, office note creation, forwarding office note
    assert len(audit_log) == 3
    assert audit_log[1]["action"] == "create_office_note"
    assert audit_log[2]["action"] == "forward_office_note"


def test_create_enclosure():
    # 1. Create inward
    file = io.BytesIO(b"Data")
    data = {
        "department": "DBR", "division": "Legis", "sub_section": "Sec 1",
        "case_access_level": "wider", "privacy_level": "public", "inward_priority_level": "medium",
        "year": 2025, "inward_subject": "Subj", "inward_type": "Type",
        "from_which_office": "Office X", "from_which_department": "Legal",
        "inward_date": "2025-06-01", "letter_type": "Ltr", "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-06-10", "process_type": "Proc A",
        "letter_language": "Hindi", "assigned_to": "officer_bob"
    }
    create_resp = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("doc.txt", file, "text/plain")}
    )
    inward_id = create_resp.json()["data"]["inward_id"]

    # 2. Attach an enclosure with invalid privacy level (400)
    enc_file = io.BytesIO(b"Attachment data")
    enc_resp_err = client.post(
        "/api/v1/create_enclosure",
        data={"inward_id": inward_id, "privacy_level": "super_secret"},
        files={"enclosure": ("attachment.pdf", enc_file, "application/pdf")}
    )
    assert enc_resp_err.status_code == 400
    assert enc_resp_err.json()["error"] == "INVALID_PRIVACY_LEVEL"

    # 3. Attach a valid enclosure
    enc_file.seek(0)
    enc_resp = client.post(
        "/api/v1/create_enclosure",
        data={"inward_id": inward_id, "privacy_level": "confidential"},
        files={"enclosure": ("attachment.pdf", enc_file, "application/pdf")},
        headers={"X-User-Id": "officer_bob"}
    )
    assert enc_resp.status_code == 201
    enc_id = enc_resp.json()["data"]["enclosure_id"]
    assert "ENC-" in enc_id

    # 4. Verify audit trail is updated
    inward_resp = client.get(f"/api/v1/fetch_inward/{inward_id}")
    audit_log = inward_resp.json()["data"][0]["audit_history"]
    assert len(audit_log) == 2
    assert audit_log[1]["action"] == "create_enclosure"
    assert "attachment.pdf" in audit_log[1]["details"]
    assert "confidential" in audit_log[1]["details"]


def test_mark_off_inward():
    # 1. Create inward
    file = io.BytesIO(b"Data")
    data = {
        "department": "DBR", "division": "Legis", "sub_section": "Sec 1",
        "case_access_level": "wider", "privacy_level": "public", "inward_priority_level": "medium",
        "year": 2025, "inward_subject": "Subj", "inward_type": "Type",
        "from_which_office": "Office X", "from_which_department": "Legal",
        "inward_date": "2025-06-01", "letter_type": "Ltr", "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-06-10", "process_type": "Proc A",
        "letter_language": "Hindi", "assigned_to": "officer_bob"
    }
    create_resp = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("doc.txt", file, "text/plain")}
    )
    inward_id = create_resp.json()["data"]["inward_id"]

    # 2. Mark off with invalid closure classification
    mark_off_resp_err = client.post(
        "/api/v1/mark_off_inward",
        json={
            "inward_id": inward_id,
            "closure_classification": "invalid_classification",
            "file_number": "FILE-2025-DBR-01",
            "remarks": "Completed successfully."
        }
    )
    assert mark_off_resp_err.status_code == 400
    assert mark_off_resp_err.json()["error"] == "INVALID_CLOSURE_CLASSIFICATION"

    # 3. Mark off successfully
    mark_off_resp = client.post(
        "/api/v1/mark_off_inward",
        json={
            "inward_id": inward_id,
            "closure_classification": "completely_processed",
            "file_number": "FILE-2025-DBR-01",
            "remarks": "Completed successfully."
        },
        headers={"X-User-Id": "supervisor_clara"}
    )
    assert mark_off_resp.status_code == 200
    assert mark_off_resp.json()["data"]["status"] == "marked_off"
    assert "marked_off_on" in mark_off_resp.json()["data"]

    # 4. Fetch the marked off inward and verify status and details
    inward_resp = client.get(f"/api/v1/fetch_inward/{inward_id}")
    record = inward_resp.json()["data"][0]
    assert record["status"] == "marked_off"
    assert record["closure_classification"] == "completely_processed"
    assert record["file_number"] == "FILE-2025-DBR-01"
    assert record["remarks"] == "Completed successfully."
    assert len(record["audit_history"]) == 2
    assert record["audit_history"][1]["action"] == "mark_off_inward"

    # 5. Try marking it off again (409 conflict)
    mark_off_again_resp = client.post(
        "/api/v1/mark_off_inward",
        json={
            "inward_id": inward_id,
            "closure_classification": "completely_processed",
            "file_number": "FILE-2025-DBR-01",
            "remarks": "Completed again."
        }
    )
    assert mark_off_again_resp.status_code == 409
    assert mark_off_again_resp.json()["error"] == "INWARD_ALREADY_MARKED_OFF"


def test_create_inward_validation_errors():
    # 1. Try creating with invalid process_type
    file_content = b"Mock document content"
    file = io.BytesIO(file_content)
    
    data = {
        "department": "DBR",
        "division": "Legis",
        "sub_section": "Section A",
        "case_access_level": "limited",
        "privacy_level": "confidential",
        "inward_priority_level": "high",
        "year": 2025,
        "inward_subject": "Draft Banking Bill 2025",
        "inward_type": "Legislative Ref",
        "from_which_office": "Central Office",
        "from_which_department": "Legal",
        "inward_date": "2025-06-01",
        "letter_type": "Official letter",
        "date_of_receipt": "2025-06-02",
        "estimated_date_of_closure": "2025-12-31",
        "process_type": "INVALID_PROCESS_VALUE",
        "letter_language": "English",
        "assigned_to": "officer_bob"
    }
    
    response = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("test_doc.pdf", file, "application/pdf")},
        headers={"X-User-Id": "officer_alice"}
    )
    
    assert response.status_code == 400
    resp_json = response.json()
    assert resp_json["error"] == "INVALID_PROCESS_TYPE"
    assert "Allowed values" in resp_json["message"]

    # 2. Try creating with invalid letter_language
    file.seek(0)
    data["process_type"] = "Standard"
    data["letter_language"] = "French"
    
    response = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("test_doc.pdf", file, "application/pdf")},
        headers={"X-User-Id": "officer_alice"}
    )
    
    assert response.status_code == 400
    resp_json = response.json()
    assert resp_json["error"] == "INVALID_LETTER_LANGUAGE"

    # 3. Try creating with invalid office
    file.seek(0)
    data["letter_language"] = "English"
    data["from_which_office"] = "Invalid Office Value"
    
    response = client.post(
        "/api/v1/create_soft_copy_inward/",
        data=data,
        files={"inward_file": ("test_doc.pdf", file, "application/pdf")},
        headers={"X-User-Id": "officer_alice"}
    )
    
    assert response.status_code == 400
    resp_json = response.json()
    assert resp_json["error"] == "INVALID_OFFICE"
