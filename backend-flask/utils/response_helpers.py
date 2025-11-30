"""
Standardized API response helpers.
Demonstrates: Consistency, DRY Principle.
"""
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from datetime import datetime


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200
) -> JSONResponse:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        JSONResponse: Formatted response
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    status_code: int = 500,
    details: Optional[Dict] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        error_code: Error code identifier
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        JSONResponse: Formatted error response
    """
    content = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def validation_error_response(errors: list) -> JSONResponse:
    """
    Create validation error response.
    
    Args:
        errors: List of validation errors
        
    Returns:
        JSONResponse: Formatted validation error
    """
    return error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=422,
        details={"errors": errors}
    )
