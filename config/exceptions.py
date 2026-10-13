"""
Custom Exception Handler for consistent REST API responses
"""

import uuid
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request_id = str(uuid.uuid4())

    if response is not None:
        custom_data = {
            "error": {
                "code": getattr(exc, "default_code", "API_ERROR").upper(),
                "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                "details": response.data,
                "request_id": request_id
            }
        }
        response.data = custom_data
        return response

    return Response({
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred during quantum execution or request processing.",
            "details": {},
            "request_id": request_id
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
