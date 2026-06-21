import os
import shutil
import uuid
from typing import Optional
from fastapi import status, Form, File, UploadFile, Query, Header, Path
from fastapi.responses import JSONResponse
from src.schema.inward_schema import ForwardInwardRequest, MarkOffInwardRequest, CreateSoftCopyInwardRequest
from src.service.inward_service import InwardService
from src.utils.common_utils import UPLOAD_DIR
from src.utils.validation_utils import validate_field, ValidationError

class InwardController:
    @staticmethod
    async def create_soft_copy_inward(
        body: CreateSoftCopyInwardRequest
    ):
        try:
            # Perform validations
            validate_field("department", body.department)
            validate_field("division", body.division)
            validate_field("sub_section", body.sub_section)
            validate_field("case_access_level", body.case_access_level)
            validate_field("privacy_level", body.privacy_level)
            validate_field("inward_priority_level", body.inward_priority_level)
            validate_field("office", body.from_which_office)
            validate_field("department", body.from_which_department)
            validate_field("letter_type", body.letter_type)
            validate_field("process_type", body.process_type)
            validate_field("letter_language", body.letter_language)

            data = body.model_dump()

            
            created_by = body.user_name or "system"
            
            inward_id = InwardService.create_soft_copy_inward(data, body.inward_file, created_by)
            
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
        except ValidationError as ve:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "data": None,
                    "message": ve.message,
                    "error": ve.error_code
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
            
            inward = InwardService.get_inward_by_id(inward_id)
            if not inward:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
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
            if not InwardService.inward_exists(inward_id):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "data": None,
                        "message": "Inward not found",
                        "error": "INWARD_NOT_FOUND"
                    }
                )
                
            # Validate privacy_level
            validate_field("privacy_level", privacy_level)
                
            file_ext = os.path.splitext(enclosure.filename)[-1] if enclosure.filename else ""
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
        except ValidationError as ve:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "data": None,
                    "message": ve.message,
                    "error": ve.error_code
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
            
            if not InwardService.inward_exists(inward_id):
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
