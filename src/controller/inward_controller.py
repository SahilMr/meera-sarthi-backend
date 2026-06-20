import os
import shutil
from typing import Optional
from fastapi import status, Form, File, UploadFile, Query, Header, Path
from fastapi.responses import JSONResponse
from src.schema.inward_schema import ForwardInwardRequest, MarkOffInwardRequest
from src.service.inward_service import InwardService
from src.utils.common_utils import UPLOAD_DIR
from src.db.mock_db import inwards_db

class InwardController:
    @staticmethod
    async def create_soft_copy_inward(
        department: str = Form(...),
        division: str = Form(...),
        sub_section: str = Form(...),
        case_access_level: str = Form(...),
        privacy_level: str = Form(...),
        inward_priority_level: str = Form(...),
        year: int = Form(...),
        inward_file: UploadFile = File(...),
        inward_subject: str = Form(...),
        inward_type: str = Form(...),
        from_which_office: str = Form(...),
        from_which_department: str = Form(...),
        inward_date: str = Form(...),
        letter_type: str = Form(...),
        date_of_receipt: str = Form(...),
        estimated_date_of_closure: str = Form(...),
        process_type: str = Form(...),
        letter_language: str = Form(...),
        assigned_to: str = Form(...),
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            # We need to save the file
            # Let's get next index safely to avoid name conflicts.
            # We can use length of inwards_db or just a temporary unique name.
            # Let's find sequence by invoking the service.
            # Actually, to get the file name, we can pass a temp file name or invoke the service first.
            # Let's pass the form parameters as a dict to service.
            data = {
                "department": department,
                "division": division,
                "sub_section": sub_section,
                "case_access_level": case_access_level,
                "privacy_level": privacy_level,
                "inward_priority_level": inward_priority_level,
                "year": year,
                "inward_subject": inward_subject,
                "inward_type": inward_type,
                "from_which_office": from_which_office,
                "from_which_department": from_which_department,
                "inward_date": inward_date,
                "letter_type": letter_type,
                "date_of_receipt": date_of_receipt,
                "estimated_date_of_closure": estimated_date_of_closure,
                "process_type": process_type,
                "letter_language": letter_language,
                "assigned_to": assigned_to,
            }
            
            created_by = x_user_id or "system"
            
            # Save file to uploads folder temporarily
            file_ext = os.path.splitext(inward_file.filename)[-1] if inward_file.filename else ""
            # We will use a temp file name or just use index. Since we increment inward_seq in Service, 
            # let's write to a temp file or get sequence inside service.
            # Let's invoke create_soft_copy_inward. It needs file name. We will use a unique name.
            # Let's generate a unique filename:
            import uuid
            unique_filename = f"inward_{uuid.uuid4().hex}{file_ext}"
            filepath = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(inward_file.file, buffer)
                
            inward_id = InwardService.create_soft_copy_inward(data, unique_filename, created_by)
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "data": {
                        "inward_id": inward_id
                    },
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Failed to create inward",
                    "error": str(e)
                }
            )

    @staticmethod
    async def fetch_inward(
        inward_id: Optional[str] = None,
        assigned_to: Optional[str] = Query(None, description="Filter work queue by assigned user"),
        page: int = Query(1, ge=1, description="Page number for pagination"),
        limit: int = Query(10, ge=1, description="Number of items per page")
    ):
        try:
            if inward_id:
                record = InwardService.get_inward_by_id(inward_id)
                if not record:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={
                            "data": None,
                            "message": "Inward not found",
                            "error": "INWARD_NOT_FOUND"
                        }
                    )
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "data": [record],
                        "message": "Success",
                        "error": None
                    }
                )
            
            # Fetch work queue
            records = InwardService.get_inwards_list(assigned_to, page, limit)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "data": records,
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )

    @staticmethod
    async def forward_inward(
        body: ForwardInwardRequest,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            inward_id = body.inward_id
            forward_to = body.forward_to
            acted_by = x_user_id or "system"
            
            # Check existence first
            if inward_id not in inwards_db:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            inward = inwards_db[inward_id]
            if inward["status"] == "marked_off":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "data": None,
                        "message": "Cannot forward a marked-off inward",
                        "error": "INWARD_MARKED_OFF"
                    }
                )
                
            success = InwardService.forward_inward(inward_id, forward_to, acted_by)
            if not success:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )

    @staticmethod
    async def create_enclosure(
        inward_id: str = Form(...),
        enclosure: UploadFile = File(...),
        privacy_level: str = Form(...),
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            if inward_id not in inwards_db:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            if privacy_level not in ["public", "confidential"]:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "data": None,
                        "message": "Privacy level must be either 'public' or 'confidential'",
                        "error": "INVALID_PRIVACY_LEVEL"
                    }
                )
                
            # Save file
            file_ext = os.path.splitext(enclosure.filename)[-1] if enclosure.filename else ""
            import uuid
            unique_filename = f"enclosure_{uuid.uuid4().hex}{file_ext}"
            filepath = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(enclosure.file, buffer)
                
            created_by = x_user_id or "system"
            enclosure_id = InwardService.create_enclosure(
                inward_id=inward_id,
                filename=unique_filename,
                privacy_level=privacy_level,
                created_by=created_by,
                original_filename=enclosure.filename
            )
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "data": {
                        "enclosure_id": enclosure_id
                    },
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )

    @staticmethod
    async def mark_off_inward(
        body: MarkOffInwardRequest,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id")
    ):
        try:
            inward_id = body.inward_id
            closure_classification = body.closure_classification
            file_number = body.file_number
            remarks = body.remarks
            acted_by = x_user_id or "system"
            
            if inward_id not in inwards_db:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            if closure_classification not in ["completely_processed", "partially_processed"]:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "data": None,
                        "message": "Closure classification must be either 'completely_processed' or 'partially_processed'",
                        "error": "INVALID_CLOSURE_CLASSIFICATION"
                    }
                )
                
            res = InwardService.mark_off_inward(
                inward_id, closure_classification, file_number, remarks, acted_by
            )
            
            if res is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            if "error" in res:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "data": None,
                        "message": "The inward is already marked off",
                        "error": res["error"]
                    }
                )
                
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "data": res,
                    "message": "Success",
                    "error": None
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "data": None,
                    "message": "Internal Server Error",
                    "error": str(e)
                }
            )
