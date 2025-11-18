from ninja import Schema
from typing import Optional
from pydantic import Field


class PDFUploadSchema(Schema):
    """Schema for PDF document upload."""
    
    file_base64: str = Field(..., description="Base64 encoded PDF file")
    filename: Optional[str] = Field(None, description="Optional filename")


class UploadResponseSchema(Schema):
    """Schema for upload response."""
    
    message: str
    success: bool
    uploaded_at: str


class DocumentStatusSchema(Schema):
    """Schema for document status."""
    
    has_uploaded_document: bool
    last_upload_date: Optional[str] = None


class DeleteDataResponseSchema(Schema):
    """Schema for delete data response."""
    
    message: str
    success: bool

