from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError
from .schemas import (
    CreateCoverLetterRequest,
    CreateCoverLetterSimpleRequest,
    CreateCoverLetterResponse,
)
from django.contrib.auth import get_user_model
from jobs.models import JobListing
from authentication.models import Country
import requests
import uuid

User = get_user_model()
router = Router(tags=["cover-letters"])


def _prepare_user_data(user, profile):
    """
    Helper function to prepare user data dictionary.
    
    Args:
        user: Django User object
        profile: UserProfile object
        
    Returns:
        dict: User data dictionary
    """
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "phone_number": profile.phone_number or "",
        "street": profile.street or "",
        "city": profile.city or "",
        "postcode": profile.postcode or "",
        "country": profile.country or "",
        "country_display": Country(profile.country).label if profile.country else "",
    }


def _call_webhook_for_cover_letter(user_data: dict, job_data: dict, language: str, customer_instructions: str = None) -> str:
    """
    Helper function to call the n8n webhook and generate cover letter content.
    
    Args:
        user_data: Dictionary containing user information
        job_data: Dictionary containing job information
        language: Language for the cover letter
        customer_instructions: Optional custom instructions
        
    Returns:
        str: Generated cover letter text
        
    Raises:
        HttpError: If webhook call fails or returns empty content
    """
    webhook_url = "https://n8n.project100x.run.place/webhook/create_cover_letter"
    
    # Prepare webhook payload
    webhook_payload = {
        "user": user_data,
        "job": job_data,
        "language": language,
    }
    
    # Add customer instructions if provided
    if customer_instructions:
        webhook_payload["customer_instructions"] = customer_instructions
    
    # Send POST request to n8n webhook
    try:
        webhook_response = requests.post(
            webhook_url,
            json=webhook_payload,
            timeout=30
        )
        webhook_response.raise_for_status()
        
        # Extract the content from the webhook response
        # Try to parse as JSON first, fall back to plain text
        content = None
        try:
            webhook_data = webhook_response.json()
            content = webhook_data.get("content") or webhook_data.get("text")
        except ValueError:
            # Response is not JSON, use raw text
            pass
        
        # If no content from JSON, use the raw response text
        if not content:
            content = webhook_response.text
        
        # Check if we got any content
        if not content or not content.strip():
            raise HttpError(500, "Webhook returned empty content")
        
        return content
        
    except requests.exceptions.RequestException as e:
        raise HttpError(500, f"Failed to generate cover letter content: {str(e)}")


@router.post(
    "/create-cover-letter",
    response=CreateCoverLetterResponse,
    auth=JWTAuth(),
    summary="Create a cover letter",
    description="Generate cover letter text using AI based on user profile and job listing. Returns only the plain text content. Requires authentication."
)
def create_cover_letter(request, payload: CreateCoverLetterRequest):
    """
    Create a cover letter using user profile and job listing.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Fetches the job from the database
    3. Sends the job and user data to an n8n webhook to generate content
    4. Returns the generated text
    
    Requires a valid JWT token in the Authorization header.
    """
    
    # Get authenticated user from JWT token
    user = request.user
    
    # Ensure user profile exists
    try:
        user = User.objects.select_related('profile').get(id=user.id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    
    # Fetch job
    try:
        job = JobListing.objects.get(job_id=payload.job_id)
    except JobListing.DoesNotExist:
        raise HttpError(404, "Job not found")
    
    # Get user profile data
    profile = user.profile
    
    # Prepare user data using helper function
    user_data = _prepare_user_data(user, profile)
    
    # Prepare job data
    job_data = {
        "job_id": job.job_id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "description": job.description or "",
        "employment_type": job.employment_type or "",
        "experience_level": job.experience_level or "",
        "linkedin_url": job.linkedin_url,
    }
    
    # Call webhook to generate cover letter content
    cover_letter_text = _call_webhook_for_cover_letter(
        user_data=user_data,
        job_data=job_data,
        language=payload.language.value,
        customer_instructions=payload.customer_instructions
    )
    
    return CreateCoverLetterResponse(
        cover_letter_text=cover_letter_text,
        success=True
    )


@router.post(
    "/create-cover-letter-simple",
    response=CreateCoverLetterResponse,
    auth=JWTAuth(),
    summary="Create a cover letter with custom job details",
    description="Generate cover letter text using AI based on user profile and custom job details. Returns only the plain text content. Requires authentication."
)
def create_cover_letter_simple(request, payload: CreateCoverLetterSimpleRequest):
    """
    Create a cover letter using custom job details.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Sends the job and user data to an n8n webhook to generate content
    3. Returns the generated text
    
    This is a simplified version that doesn't require a pre-stored job listing.
    Ideal for users who want to quickly generate a cover letter with custom job details.
    
    Requires a valid JWT token in the Authorization header.
    """
    
    # Get authenticated user from JWT token
    user = request.user
    
    # Ensure user profile exists
    try:
        user = User.objects.select_related('profile').get(id=user.id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    
    # Get user profile data
    profile = user.profile
    
    # Prepare user data using helper function
    user_data = _prepare_user_data(user, profile)
    
    # Prepare job data from the request payload
    # Generate a random job_id for webhook compatibility
    job_data = {
        "job_id": str(uuid.uuid4()),
        "title": payload.position_title,
        "company_name": payload.company_name,
        "location": payload.job_location,
        "description": payload.job_description,
        "employment_type": "",
        "experience_level": "",
        "linkedin_url": "",
    }
    
    # Call webhook to generate cover letter content
    cover_letter_text = _call_webhook_for_cover_letter(
        user_data=user_data,
        job_data=job_data,
        language=payload.language.value,
        customer_instructions=payload.customer_instructions
    )
    
    return CreateCoverLetterResponse(
        cover_letter_text=cover_letter_text,
        success=True
    )

