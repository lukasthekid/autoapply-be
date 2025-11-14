from ninja import Schema
from typing import Optional
from pydantic import EmailStr, Field
from django.contrib.auth import get_user_model
from .models import Country

User = get_user_model()


class RegisterSchema(Schema):
    """Schema for user registration."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=150)
    last_name: Optional[str] = Field(None, max_length=150)


class LoginSchema(Schema):
    """Schema for user login."""
    
    username: str
    password: str


class TokenResponseSchema(Schema):
    """Schema for JWT token response."""
    
    access: str
    refresh: str
    user: dict


class UserSchema(Schema):
    """Schema for user information."""
    
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    date_joined: str
    
    class Config:
        from_attributes = True


class RefreshTokenSchema(Schema):
    """Schema for token refresh."""
    
    refresh: str


class MessageSchema(Schema):
    """Schema for simple message responses."""
    
    message: str


class UserProfileUpdateSchema(Schema):
    """Schema for updating user profile information."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=150)
    last_name: Optional[str] = Field(None, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=20)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postcode: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)


class UserProfileSchema(Schema):
    """Schema for user profile information."""
    
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_display: Optional[str] = None
    date_joined: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class CountryOptionSchema(Schema):
    """Schema for country option."""
    
    code: str
    name: str


class CountriesListSchema(Schema):
    """Schema for list of countries."""
    
    countries: list[CountryOptionSchema]

