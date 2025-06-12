from fastapi import APIRouter
from . import auth, users, labs, devices, groups, network, pairing

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(labs.router)
api_router.include_router(devices.router)
api_router.include_router(groups.router)
api_router.include_router(network.router)
api_router.include_router(pairing.router)
