from fastapi import Request
import logging
from logging_config import logger
import time
import uuid
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("hexagon")

origins = [
    "http://localhost:5173",
    "https://hexagon-1ny1.onrender.com"
]


async def log_request(request: Request, call_next):
    logger.info(f" {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f" {request.method} {request.url.path} - {response.status_code}")
    return response


async def log_timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round(time.time() - start_time, 4)
    logger.info(f" {request.method} {request.url.path} took {duration} seconds")
    return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Exception occurred on {request.method} {request.url.path}")
            return JSONResponse(
                status_code=500,
                content={"message": str(e)},
            )

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        logger.info(f"[{request_id}] Request started: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(f"[{request_id}] Request completed in {process_time:.4f}s with status {response.status_code}")

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response


def register_middleware(app):

    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                       allow_headers=["*"])
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RequestContextMiddleware)

