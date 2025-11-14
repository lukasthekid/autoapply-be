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

