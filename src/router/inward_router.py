from fastapi import APIRouter
from src.controller.inward_controller import InwardController

router = APIRouter(tags=["Inwards"])

router.add_api_route(
    "/create_soft_copy_inward/",
    InwardController.create_soft_copy_inward,
    methods=["POST"],
    summary="Create soft copy inward registration"
)

router.add_api_route(
    "/fetch_inward",
    InwardController.fetch_inward,
    methods=["GET"],
    summary="Fetch administrative records or work queue"
)

router.add_api_route(
    "/fetch_inward/{inward_id}",
    InwardController.fetch_inward,
    methods=["GET"],
    summary="Fetch administrative record for a specific inward"
)

router.add_api_route(
    "/forward_inward",
    InwardController.forward_inward,
    methods=["POST"],
    summary="Forward inward to higher authority"
)

router.add_api_route(
    "/create_enclosure",
    InwardController.create_enclosure,
    methods=["POST"],
    summary="Attach enclosures to an inward"
)

router.add_api_route(
    "/mark_off_inward",
    InwardController.mark_off_inward,
    methods=["POST"],
    summary="Mark off/Close an inward"
)
