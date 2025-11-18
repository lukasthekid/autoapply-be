"""
Custom exception handlers for the documents app.
"""
from django.core.exceptions import RequestDataTooBig
from ninja.errors import HttpError


def handle_request_too_large(request, exc):
    """
    Handle RequestDataTooBig exception.
    
    This is called when a request exceeds DATA_UPLOAD_MAX_MEMORY_SIZE.
    """
    print(f"[ERROR] Request too large from {request.META.get('REMOTE_ADDR', 'unknown')}")
    print(f"[ERROR] RequestDataTooBig: {str(exc)}")
    
    return {
        "detail": "PDF file is too large. Maximum file size is 5MB. Please upload a smaller PDF."
    }

