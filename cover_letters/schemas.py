from ninja import Schema
from enum import Enum


class CoverLetterLanguage(str, Enum):
    """Supported languages for cover letters."""
    ENGLISH = "english"
    GERMAN = "german"
    FRENCH = "french"
    ITALIAN = "italian"
    SPANISH = "spanish"


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
