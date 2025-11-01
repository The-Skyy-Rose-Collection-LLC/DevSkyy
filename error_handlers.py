    import os
from fastapi.responses import JSONResponse

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

from logger_config import get_logger
from typing import Any, Dict, Optional
import logging
import traceback

logger = logging.getLogger(__name__)
"""
Centralized Error Handlers for DevSkyy Platform
Enterprise-grade error handling with proper logging and user feedback
"""

logger = get_logger(__name__)

class DevSkyyException(Exception):
    """Base exception for DevSkyy platform."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseException(DevSkyyException):
    """Database-related exceptions."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class AuthenticationException(DevSkyyException):
    """Authentication-related exceptions."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, details=details)

class AuthorizationException(DevSkyyException):
    """Authorization-related exceptions."""

    def __init__(
        self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=403, details=details)

class ValidationException(DevSkyyException):
    """Validation-related exceptions."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)

class ResourceNotFoundException(DevSkyyException):
    """Resource not found exceptions."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, status_code=404)

class RateLimitException(DevSkyyException):
    """Rate limiting exceptions."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        details = {"retry_after": retry_after}
        super().__init__(message, status_code=429, details=details)

class ExternalServiceException(DevSkyyException):
    """External service integration exceptions."""

    def __init__(
        self, service: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        full_message = f"External service error ({service}): {message}"
        super().__init__(full_message, status_code=502, details=details)

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            }
        },
    )

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": errors,
                "path": str(request.url.path),
            }
        },
    )

async def devskyy_exception_handler(
    request: Request, exc: DevSkyyException
) -> JSONResponse:
    """Handle custom DevSkyy exceptions."""
    logger.error(
        f"DevSkyy Exception: {exc.status_code} - {exc.message} - Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
                "status_code": exc.status_code,
                "path": str(request.url.path),
            }
        },
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception on {request.url.path}",
        exc_info=True,
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    # Don't expose internal errors in production

    debug = os.environ.get("DEBUG", "false").lower() == "true"

    if debug:
        error_message = str(exc)
        error_details = {
            "traceback": traceback.format_exc(),
            "exception_type": exc.__class__.__name__,
        }
    else:
        error_message = "An internal server error occurred"
        error_details = {}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "message": error_message,
                "details": error_details,
                "status_code": 500,
                "path": str(request.url.path),
            }
        },
    )

def safe_execute(func, default_return=None, log_errors=True):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        default_return: Default return value on error
        log_errors: Whether to log errors

    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        return default_return

async def safe_execute_async(func, default_return=None, log_errors=True):
    """
    Safely execute an async function with error handling.

    Args:
        func: Async function to execute
        default_return: Default return value on error
        log_errors: Whether to log errors

    Returns:
        Function result or default_return on error
    """
    try:
        return await func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        return default_return

def register_error_handlers(app):
    """
    Register all error handlers with FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DevSkyyException, devskyy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")
