from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from .models import UserDocumentStatus
from .schemas import PDFUploadSchema, UploadResponseSchema, DocumentStatusSchema, DeleteDataResponseSchema
import base64
import io
from pypdf import PdfReader
import requests
from datetime import datetime
from django.utils import timezone

router = Router(tags=["documents"])


@router.post(
    "/upload-pdf",
    response={200: UploadResponseSchema, 400: dict, 413: dict},
    auth=JWTAuth(),
    summary="Upload PDF document",
    description="Upload a PDF document to vector storage. Accepts base64 encoded PDF files only."
)
def upload_pdf(request, payload: PDFUploadSchema):
    """
    Upload PDF document.
    
    Accepts a base64 encoded PDF file, extracts the text content,
    and sends it to the webhook for processing.
    """
    user = request.auth
    
    try:
        # Decode base64 PDF
        try:
            pdf_data = base64.b64decode(payload.file_base64)
        except Exception as e:
            raise HttpError(400, "Invalid base64 encoding")
        
        # Validate it's a PDF by checking magic number
        if not pdf_data.startswith(b'%PDF'):
            raise HttpError(400, "File is not a valid PDF document")
        
        # Extract text from PDF
        try:
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            if not text_content.strip():
                raise HttpError(400, "PDF document appears to be empty or contains no extractable text")
                
        except Exception as e:
            if isinstance(e, HttpError):
                raise e
            raise HttpError(400, f"Error reading PDF: {str(e)}")
        
        # Prepare webhook payload
        webhook_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "document": {
                "filename": payload.filename or "document.pdf",
                "text_content": text_content,
                "uploaded_at": datetime.now().isoformat(),
            }
        }
        
        # Send to webhook
        webhook_url = "https://n8n.project100x.run.place/webhook/upload_document"
        try:
            response = requests.post(
                webhook_url,
                json=webhook_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error while uploading document: {str(e)}")
            raise HttpError(500, f"Error while uploading document")
        
        # Update user document status
        doc_status, created = UserDocumentStatus.objects.get_or_create(user=user)
        doc_status.has_uploaded_document = True
        doc_status.last_upload_date = timezone.now()
        doc_status.save()
        
        return UploadResponseSchema(
            message="PDF uploaded successfully",
            success=True,
            uploaded_at=timezone.now().isoformat()
        )
        
    except HttpError:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during PDF upload for user {user.id}: {str(e)}")
        raise HttpError(500, f"Unexpected error: {str(e)}")


@router.get(
    "/status",
    response=DocumentStatusSchema,
    auth=JWTAuth(),
    summary="Get document upload status",
    description="Check if the current user has uploaded a document"
)
def get_document_status(request):
    """
    Get document upload status.
    
    Returns whether the authenticated user has uploaded a document.
    """
    user = request.auth
    doc_status, created = UserDocumentStatus.objects.get_or_create(user=user)
    
    return DocumentStatusSchema(
        has_uploaded_document=doc_status.has_uploaded_document,
        last_upload_date=doc_status.last_upload_date.isoformat() if doc_status.last_upload_date else None
    )


@router.delete(
    "/delete-data",
    response={200: DeleteDataResponseSchema, 500: dict},
    auth=JWTAuth(),
    summary="Delete user data",
    description="Delete user's document data from vector storage"
)
def delete_user_data(request):
    """
    Delete user data.
    
    Sends a request to the webhook to delete the user's document data
    and resets the user's document status.
    """
    user = request.auth
    
    try:
        # Prepare webhook payload with user_id
        webhook_data = {
            "user_id": user.id
        }
        
        # Send to webhook
        webhook_url = "https://n8n.project100x.run.place/webhook/delete_user_data"
        try:
            response = requests.delete(
                webhook_url,
                json=webhook_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error while deleting user data: {str(e)}")
            raise HttpError(500, f"Error while deleting user data")
        
        # Update user document status - reset the flags
        doc_status, created = UserDocumentStatus.objects.get_or_create(user=user)
        doc_status.has_uploaded_document = False
        doc_status.last_upload_date = None
        doc_status.save()
        
        return DeleteDataResponseSchema(
            message="User data deleted successfully",
            success=True
        )
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Unexpected error: {str(e)}")

