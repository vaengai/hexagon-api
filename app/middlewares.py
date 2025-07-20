from fastapi import Request
from logger import logger
import time
from fastapi.responses import JSONResponse

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

async def exception_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception(f"Exception occurred on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"message": str(e)},
        )

def register_middleware(app):
    app.middleware("http")(log_timing_middleware)
    app.add_middleware(log_request)
    app.add_middleware(exception_handler)