from ninja import Schema
from datetime import datetime


class TypstTemplateSchema(Schema):
    """Schema for TypstTemplate serialization."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    version: int
    name: str
    code: str
    
    class Config:
        from_attributes = True


class TypstTemplateListResponse(Schema):
    """Response schema for listing all templates."""
    
    templates: list[TypstTemplateSchema]
    count: int


class ConvertToPdfRequest(Schema):
    """Schema for converting cover letter text to PDF."""
    
    template_id: int
    content: str
    company_name: str


class ConvertToPdfResponse(Schema):
    """Schema for convert to PDF response."""
    
    pdf_base64: str
    success: bool = True

