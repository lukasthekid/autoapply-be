from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError
from .schemas import (
    CreateResumeRequest,
    CreateResumeResponse,
)
from django.contrib.auth import get_user_model
from authentication.models import Country
import requests

User = get_user_model()
router = Router(tags=["resumes"])


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


def _call_webhook_for_resume(user_data: dict, job_description: str, language: str) -> str:
    """
    Helper function to call the n8n webhook and generate resume content.
    
    Args:
        user_data: Dictionary containing user information
        job_description: Job description text
        language: Language for the resume
        
    Returns:
        str: Generated resume text
        
    Raises:
        HttpError: If webhook call fails or returns empty content
    """
    webhook_url = "https://n8n.project100x.run.place/webhook/create_resume"
    
    # Prepare webhook payload
    webhook_payload = {
        "user": user_data,
        "job_description": job_description,
        "language": language,
    }
    
    # Send POST request to n8n webhook
    # Increased timeout to 120 seconds as resume generation can take a while
    try:
        webhook_response = requests.post(
            webhook_url,
            json=webhook_payload,
            timeout=120
        )
        webhook_response.raise_for_status()
        
        # Extract the content from the webhook response
        # Try to parse as JSON first, fall back to plain text
        content = None
        try:
            webhook_data = webhook_response.json()
            content = webhook_data.get("content") or webhook_data.get("text") or webhook_data.get("resume")
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
        
    except requests.exceptions.Timeout:
        raise HttpError(504, "Resume generation timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise HttpError(500, f"Failed to generate resume content: {str(e)}")


@router.post(
    "/create-resume",
    response=CreateResumeResponse,
    auth=JWTAuth(),
    summary="Create a resume",
    description="Generate resume text using AI based on user profile and job description. Returns the generated resume text. Generation may take a while. Requires authentication."
)
def create_resume(request, payload: CreateResumeRequest):
    """
    Create a resume using user profile and job description.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Sends the user data, job description, and language to an n8n webhook to generate content
    3. Returns the generated resume text
    
    Note: Resume generation can take a while, so the request may take up to 2 minutes to complete.
    
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
    
    # Call webhook to generate resume content
    resume_text = _call_webhook_for_resume(
        user_data=user_data,
        job_description=payload.job_description,
        language=payload.language.value
    )
    
    return CreateResumeResponse(
        resume_text=resume_text,
        success=True
    )
