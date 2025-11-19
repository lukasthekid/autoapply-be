from ninja import Schema
from datetime import datetime
from enum import Enum


class CoverLetterLanguage(str, Enum):
    """Supported languages for cover letters."""
    ENGLISH = "english"
    GERMAN = "german"
    FRENCH = "french"
    ITALIAN = "italian"
    SPANISH = "spanish"


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


class CreateCoverLetterRequest(Schema):
    """Schema for create cover letter request."""
    
    job_id: str
    language: CoverLetterLanguage = CoverLetterLanguage.ENGLISH
    customer_instructions: str = None


class CreateCoverLetterSimpleRequest(Schema):
    """Schema for simple cover letter request without requiring a stored job listing."""
    
    position_title: str
    company_name: str
    job_location: str
    job_description: str
    language: CoverLetterLanguage = CoverLetterLanguage.ENGLISH
    customer_instructions: str = None


class CreateCoverLetterResponse(Schema):
    """Schema for create cover letter response."""
    
    cover_letter_text: str
    success: bool = True


class ConvertToPdfRequest(Schema):
    """Schema for converting cover letter text to PDF."""
    
    template_id: int
    content: str
    company_name: str


class ConvertToPdfResponse(Schema):
    """Schema for convert to PDF response."""
    
    pdf_base64: str
    success: bool = True

