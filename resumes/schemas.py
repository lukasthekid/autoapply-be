from ninja import Schema
from enum import Enum


class ResumeLanguage(str, Enum):
    """Supported languages for resumes."""
    ENGLISH = "english"
    GERMAN = "german"
    FRENCH = "french"
    ITALIAN = "italian"
    SPANISH = "spanish"


class CreateResumeRequest(Schema):
    """Schema for create resume request."""
    
    job_description: str
    language: ResumeLanguage = ResumeLanguage.ENGLISH


class CreateResumeResponse(Schema):
    """Schema for create resume response."""
    
    resume_text: str
    success: bool = True
