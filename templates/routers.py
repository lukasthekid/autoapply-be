from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError
from .models import TypstTemplate
from .schemas import (
    TypstTemplateListResponse,
    CreateCoverLetterRequest,
    CreateCoverLetterSimpleRequest,
    CreateCoverLetterResponse,
)
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from jobs.models import JobListing
from authentication.models import UserProfile, Country
from jinja2 import Template
import requests
import base64
import typst
import uuid

User = get_user_model()
router = Router(tags=["templates"])


def escape_typst_characters(text: str) -> str:
    """
    Escape special Typst characters that need a backslash before them.
    Special characters: #, @, <, >, $, \\, _, *
    """
    if not text:
        return text
    
    # Escape backslash first to avoid double-escaping
    text = text.replace('\\', '\\\\')
    
    # Escape other special characters
    special_chars = ['#', '@', '<', '>', '$', '_', '*']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


@router.get(
    "/",
    response=TypstTemplateListResponse,
    auth=JWTAuth(),
    summary="Get all Typst templates",
    description="Retrieve all Typst templates from the database. Requires authentication."
)
def find_all_templates(request):
    """
    Find all Typst templates.
    
    Returns a list of all templates with their metadata.
    Requires a valid JWT token in the Authorization header.
    """
    templates = TypstTemplate.objects.all()
    templates_list = list(templates)
    
    return TypstTemplateListResponse(
        templates=templates_list,
        count=len(templates_list)
    )


@router.post(
    "/create-cover-letter",
    response=CreateCoverLetterResponse,
    auth=JWTAuth(),
    summary="Create a cover letter",
    description="Create a cover letter by combining a template with user and job data. Returns the cover letter text and a base64-encoded PDF. Requires authentication."
)
def create_cover_letter(request, payload: CreateCoverLetterRequest):
    """
    Create a cover letter using a template, user profile, and job listing.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Fetches the template and job from the database
    3. Sends the job and user data to an n8n webhook to generate content
    4. Replaces dynamic content in the template using Jinja2
    5. Returns the rendered result
    
    Requires a valid JWT token in the Authorization header.
    """
    
    # Get authenticated user from JWT token
    user = request.user
    
    # Ensure user profile exists
    try:
        user = User.objects.select_related('profile').get(id=user.id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    
    # Fetch template
    try:
        template = TypstTemplate.objects.get(id=payload.template_id)
    except TypstTemplate.DoesNotExist:
        raise HttpError(404, "Template not found")
    
    # Fetch job
    try:
        job = JobListing.objects.get(job_id=payload.job_id)
    except JobListing.DoesNotExist:
        raise HttpError(404, "Job not found")
    
    # Prepare data to send to n8n webhook
    webhook_url = "https://n8n.project100x.run.place/webhook/create_cover_letter"
    
    # Get user profile data
    profile = user.profile
    
    # Prepare user data
    user_data = {
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
    
    # Prepare webhook payload
    webhook_payload = {
        "user": user_data,
        "job": job_data,
        "language": payload.language.value,
    }
    
    # Add customer instructions if provided
    if payload.customer_instructions:
        webhook_payload["customer_instructions"] = payload.customer_instructions
    
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
        
        # Store original content before escaping (for returning in response)
        original_content = content
        
        # Escape Typst special characters in the content
        content = escape_typst_characters(content)
        
    except requests.exceptions.RequestException as e:
        raise HttpError(500, f"Failed to generate cover letter content: {str(e)}")
    
    # Prepare template variables for Jinja2
    template_vars = {
        "company_name": job.company_name,
        "street": profile.street or "",
        "post_code": profile.postcode or "",
        "city": profile.city or "",
        "country": Country(profile.country).label if profile.country else "",
        "email": escape_typst_characters(user.email),
        "content": content,
    }
    
    # Render the template with Jinja2
    try:
        jinja_template = Template(template.code)
        rendered_result = jinja_template.render(**template_vars)
    except Exception as e:
        raise HttpError(500, f"Failed to render template: {str(e)}")
    
    # Compile the Typst file to PDF using Python typst library
    try:
        # Compile Typst content directly to PDF bytes
        pdf_bytes = typst.compile(rendered_result.encode('utf-8'))
        
        # Base64 encode the PDF
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
    except Exception as e:
        raise HttpError(500, f"Failed to compile Typst to PDF: {str(e)}")
    
    return CreateCoverLetterResponse(
        cover_letter_text=original_content,
        pdf_base64=pdf_base64,
        success=True
    )


@router.post(
    "/create-cover-letter-simple",
    response=CreateCoverLetterResponse,
    auth=JWTAuth(),
    summary="Create a cover letter with custom job details",
    description="Create a cover letter by providing job details directly without requiring a stored job listing. Returns the cover letter text and a base64-encoded PDF. Requires authentication."
)
def create_cover_letter_simple(request, payload: CreateCoverLetterSimpleRequest):
    """
    Create a cover letter using a template and custom job details.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Fetches the template from the database
    3. Sends the job and user data to an n8n webhook to generate content
    4. Replaces dynamic content in the template using Jinja2
    5. Returns the rendered result
    
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
    
    # Fetch template
    try:
        template = TypstTemplate.objects.get(id=payload.template_id)
    except TypstTemplate.DoesNotExist:
        raise HttpError(404, "Template not found")
    
    # Prepare data to send to n8n webhook
    webhook_url = "https://n8n.project100x.run.place/webhook/create_cover_letter"
    
    # Get user profile data
    profile = user.profile
    
    # Prepare user data
    user_data = {
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
    
    # Prepare webhook payload
    webhook_payload = {
        "user": user_data,
        "job": job_data,
        "language": payload.language.value,
    }
    
    # Add customer instructions if provided
    if payload.customer_instructions:
        webhook_payload["customer_instructions"] = payload.customer_instructions
    
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
        
        # Store original content before escaping (for returning in response)
        original_content = content
        
        # Escape Typst special characters in the content
        content = escape_typst_characters(content)
        
    except requests.exceptions.RequestException as e:
        raise HttpError(500, f"Failed to generate cover letter content: {str(e)}")
    
    # Prepare template variables for Jinja2
    template_vars = {
        "company_name": payload.company_name,
        "street": profile.street or "",
        "post_code": profile.postcode or "",
        "city": profile.city or "",
        "country": Country(profile.country).label if profile.country else "",
        "email": escape_typst_characters(user.email),
        "content": content,
    }
    
    # Render the template with Jinja2
    try:
        jinja_template = Template(template.code)
        rendered_result = jinja_template.render(**template_vars)
    except Exception as e:
        raise HttpError(500, f"Failed to render template: {str(e)}")
    
    # Compile the Typst file to PDF using Python typst library
    try:
        # Compile Typst content directly to PDF bytes
        pdf_bytes = typst.compile(rendered_result.encode('utf-8'))
        
        # Base64 encode the PDF
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
    except Exception as e:
        raise HttpError(500, f"Failed to compile Typst to PDF: {str(e)}")
    
    return CreateCoverLetterResponse(
        cover_letter_text=original_content,
        pdf_base64=pdf_base64,
        success=True
    )

