from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError
from typing import List
from django.contrib.auth import get_user_model

from .models import JobApplication, JobListing
from .schemas import (
    CreateJobApplicationRequest,
    CreateJobApplicationResponse,
    JobApplicationSchema,
    JobApplicationListResponse,
    CheckApplicationResponse,
    ErrorResponse,
)

User = get_user_model()
router = Router(tags=["applications"])


@router.post(
    "/",
    response={201: CreateJobApplicationResponse, 400: ErrorResponse, 404: ErrorResponse},
    auth=JWTAuth(),
    summary="Create a job application",
    description="Record a new job application for the authenticated user. Can link to an existing job listing or create a custom application. Requires authentication."
)
def create_job_application(request, payload: CreateJobApplicationRequest):
    """
    Create a new job application.
    
    This endpoint:
    1. Gets the authenticated user from JWT token
    2. Optionally links to an existing JobListing if job_id is provided
    3. Creates a JobApplication record with job details
    4. Returns the created application
    
    Requires a valid JWT token in the Authorization header.
    """
    # Get authenticated user from JWT token
    user = request.user
    
    # Validate that job_id exists if provided
    job_listing = None
    if payload.job_id:
        try:
            job_listing = JobListing.objects.get(job_id=payload.job_id)
        except JobListing.DoesNotExist:
            return 404, ErrorResponse(
                success=False,
                error="Job not found",
                details=f"Job with ID {payload.job_id} not found in database"
            )
    
    # Check for duplicate applications
    if job_listing:
        # Check if user has already applied to this job listing
        existing_application = JobApplication.objects.filter(
            user=user,
            job_listing=job_listing
        ).first()
        
        if existing_application:
            return 400, ErrorResponse(
                success=False,
                error="Duplicate application",
                details=f"You have already applied to this job on {existing_application.applied_at.strftime('%Y-%m-%d at %H:%M')}"
            )
    else:
        # For custom applications (no job_listing), check for duplicates
        # First check by job_url if provided (most reliable)
        if payload.job_url:
            existing_application = JobApplication.objects.filter(
                user=user,
                job_listing__isnull=True,
                job_url=payload.job_url
            ).first()
            
            if existing_application:
                return 400, ErrorResponse(
                    success=False,
                    error="Duplicate application",
                    details=f"You have already applied to this job on {existing_application.applied_at.strftime('%Y-%m-%d at %H:%M')}"
                )
        
        # Also check for same job_title + company_name (fallback for applications without URL)
        existing_application = JobApplication.objects.filter(
            user=user,
            job_listing__isnull=True,
            job_title=payload.job_title,
            company_name=payload.company_name
        ).first()
        
        if existing_application:
            return 400, ErrorResponse(
                success=False,
                error="Duplicate application",
                details=f"You have already applied to {payload.job_title} at {payload.company_name} on {existing_application.applied_at.strftime('%Y-%m-%d at %H:%M')}"
            )
    
    # Create the job application
    try:
        application = JobApplication.objects.create(
            user=user,
            job_listing=job_listing,
            job_title=payload.job_title,
            company_name=payload.company_name,
            job_location=payload.job_location,
            job_url=payload.job_url,
            notes=payload.notes,
        )
        
        # Build response schema
        application_schema = JobApplicationSchema(
            id=application.id,
            job_id=job_listing.job_id if job_listing else None,
            job_title=application.job_title,
            company_name=application.company_name,
            job_location=application.job_location,
            job_url=application.job_url,
            notes=application.notes,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
        )
        
        return 201, CreateJobApplicationResponse(
            success=True,
            application=application_schema
        )
        
    except Exception as e:
        return 400, ErrorResponse(
            success=False,
            error="Failed to create job application",
            details=str(e)
        )


@router.get(
    "/",
    response=JobApplicationListResponse,
    auth=JWTAuth(),
    summary="List all job applications",
    description="Get all job applications for the authenticated user, ordered by most recent first. Requires authentication."
)
def list_job_applications(request):
    """
    List all job applications for the authenticated user.
    
    Returns all applications ordered by applied_at (most recent first).
    Requires a valid JWT token in the Authorization header.
    """
    # Get authenticated user from JWT token
    user = request.user
    
    # Get all applications for this user
    applications = JobApplication.objects.filter(user=user).select_related('job_listing')
    
    # Convert to schema
    application_schemas = []
    for application in applications:
        application_schemas.append(JobApplicationSchema(
            id=application.id,
            job_id=application.job_listing.job_id if application.job_listing else None,
            job_title=application.job_title,
            company_name=application.company_name,
            job_location=application.job_location,
            job_url=application.job_url,
            notes=application.notes,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
        ))
    
    return JobApplicationListResponse(
        applications=application_schemas,
        count=len(application_schemas)
    )


@router.get(
    "/{application_id}",
    response={200: JobApplicationSchema, 404: ErrorResponse},
    auth=JWTAuth(),
    summary="Get a specific job application",
    description="Get details of a specific job application by ID. Only returns applications belonging to the authenticated user. Requires authentication."
)
def get_job_application(request, application_id: int):
    """
    Get a specific job application by ID.
    
    Only returns applications that belong to the authenticated user.
    Requires a valid JWT token in the Authorization header.
    """
    # Get authenticated user from JWT token
    user = request.user
    
    try:
        application = JobApplication.objects.select_related('job_listing').get(
            id=application_id,
            user=user  # Ensure user can only access their own applications
        )
        
        return 200, JobApplicationSchema(
            id=application.id,
            job_id=application.job_listing.job_id if application.job_listing else None,
            job_title=application.job_title,
            company_name=application.company_name,
            job_location=application.job_location,
            job_url=application.job_url,
            notes=application.notes,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
        )
        
    except JobApplication.DoesNotExist:
        return 404, ErrorResponse(
            success=False,
            error="Application not found",
            details=f"Job application with ID {application_id} not found or you don't have permission to access it"
        )


@router.get(
    "/check",
    response=CheckApplicationResponse,
    auth=JWTAuth(),
    summary="Check if user has applied to a job",
    description="Check if the authenticated user has already applied to a specific job. Checks in priority order: job_id → job_url → job_title + company_name. If multiple parameters are provided, only the highest priority one is used. Returns true if applied, false otherwise. Requires authentication."
)
def check_job_application(
    request,
    job_id: str = None,
    job_url: str = None,
    job_title: str = None,
    company_name: str = None
):
    """
    Check if the authenticated user has already applied to a job.
    
    This endpoint checks for existing applications in priority order:
    1. job_id (highest priority): Checks if user applied to a job listing with this job_id
    2. job_url: Checks if user applied to a custom job with this URL (only if job_id not provided)
    3. job_title + company_name: Checks if user applied to a custom job with these details (only if job_id and job_url not provided)
    
    If multiple parameters are provided, only the highest priority one is used.
    At least one of job_id, job_url, or (job_title + company_name) must be provided.
    
    Requires a valid JWT token in the Authorization header.
    """
    # Get authenticated user from JWT token
    user = request.user
    
    has_applied = False
    
    # Check by job_id (for job listings) - highest priority
    if job_id:
        try:
            job_listing = JobListing.objects.get(job_id=job_id)
            has_applied = JobApplication.objects.filter(
                user=user,
                job_listing=job_listing
            ).exists()
        except JobListing.DoesNotExist:
            # Job listing doesn't exist, so user hasn't applied
            has_applied = False
    
    # Check by job_url (for custom applications)
    elif job_url:
        has_applied = JobApplication.objects.filter(
            user=user,
            job_listing__isnull=True,
            job_url=job_url
        ).exists()
    
    # Check by job_title + company_name (for custom applications)
    elif job_title and company_name:
        has_applied = JobApplication.objects.filter(
            user=user,
            job_listing__isnull=True,
            job_title=job_title,
            company_name=company_name
        ).exists()
    
    else:
        # No valid parameters provided
        return 400, ErrorResponse(
            success=False,
            error="Invalid parameters",
            details="At least one of the following must be provided: job_id, job_url, or (job_title + company_name)"
        )
    
    return CheckApplicationResponse(has_applied=has_applied)

