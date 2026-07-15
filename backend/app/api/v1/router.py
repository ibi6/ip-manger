from fastapi import APIRouter

from app.api.v1 import addresses, auth, conflicts, dashboard, devices, io_csv, sites, subnets, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router)
api_router.include_router(devices.router)
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(sites.router, tags=["sites"])
api_router.include_router(subnets.router, tags=["subnets"])
api_router.include_router(addresses.router, tags=["addresses"])
api_router.include_router(conflicts.router, tags=["conflicts"])
api_router.include_router(io_csv.router)
