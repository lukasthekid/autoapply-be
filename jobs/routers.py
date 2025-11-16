from ninja import Router
from typing import List
from django.db import transaction
import logging

from .schemas import (
    JobSearchRequest,
    JobSearchResponse,
    JobListingSchema,
    CreateJobFromUrlRequest,
    ErrorResponse
)
from .services import LinkedInJobScraper
from .models import JobListing, JobSearch

logger = logging.getLogger(__name__)
router = Router(tags=["Jobs"])


@router.post("/search", response={200: JobSearchResponse, 400: ErrorResponse, 500: ErrorResponse})
def search_jobs(request, payload: JobSearchRequest):
    """
    Search for jobs on LinkedIn
    
    This endpoint searches LinkedIn for jobs matching the specified criteria:
    - keyword: Job title or keyword (e.g., "Data Scientist")
    - location: Location to search (e.g., "Vienna")
    - job_types: Optional list of job types (full_time, part_time, contract, temporary, internship)
    - experience_levels: Optional list of experience levels (internship, entry_level, associate, mid_senior_level, director)
    - date_posted: Optional filter by posting date (any_time, past_24_hours, past_week, past_month)
    - limit: Maximum number of results to return (default: 25)
    
    Returns:
        JobSearchResponse with list of matching jobs
    """
    try:
        # Initialize LinkedIn scraper
        scraper = LinkedInJobScraper()
        
        # Convert enum values to strings
        job_types = [jt.value for jt in payload.job_types] if payload.job_types else None
        experience_levels = [el.value for el in payload.experience_levels] if payload.experience_levels else None
        date_posted = payload.date_posted.value if payload.date_posted else None
        
        # Search for jobs
        logger.info(f"Searching jobs: keyword='{payload.keyword}', location='{payload.location}', date_posted='{date_posted}'")
        jobs_data = scraper.search_jobs(
            keyword=payload.keyword,
            location=payload.location,
            job_types=job_types,
            experience_levels=experience_levels,
            date_posted=date_posted,
            limit=payload.limit or 25
        )
        
        # Store jobs in database
        job_listings = []
        with transaction.atomic():
            # Create job search record
            job_search = JobSearch.objects.create(
                keyword=payload.keyword,
                location=payload.location,
                job_types=job_types or [],
                experience_levels=experience_levels or [],
                total_results=len(jobs_data),
                results_fetched=len(jobs_data)
            )
            
            # Store job listings
            for job_data in jobs_data:
                try:
                    # Check if job already exists
                    job_listing, created = JobListing.objects.update_or_create(
                        job_id=job_data['job_id'],
                        defaults={
                            'linkedin_url': job_data.get('linkedin_url', ''),
                            'title': job_data.get('title', ''),
                            'company_name': job_data.get('company_name', ''),
                            'location': job_data.get('location', ''),
                            'description': job_data.get('description'),
                            'employment_type': job_data.get('employment_type'),
                            'experience_level': job_data.get('experience_level'),
                            'posted_date': job_data.get('posted_date'),
                            'applicants_count': job_data.get('applicants_count'),
                            'company_logo_url': job_data.get('company_logo_url'),
                            'search_keyword': job_data.get('search_keyword'),
                            'search_location': job_data.get('search_location'),
                        }
                    )
                    job_listings.append(job_listing)
                    
                    if created:
                        logger.info(f"Created new job listing: {job_listing.job_id}")
                    else:
                        logger.info(f"Updated existing job listing: {job_listing.job_id}")
                        
                except Exception as e:
                    logger.error(f"Error storing job {job_data.get('job_id')}: {str(e)}")
                    continue
        
        # Convert to response schema
        job_schemas = []
        for job in job_listings:
            job_schemas.append(JobListingSchema(
                job_id=job.job_id,
                linkedin_url=job.linkedin_url,
                title=job.title,
                company_name=job.company_name,
                location=job.location,
                description=job.description,
                employment_type=job.employment_type,
                experience_level=job.experience_level,
                posted_date=job.posted_date,
                applicants_count=job.applicants_count,
                company_logo_url=job.company_logo_url,
            ))
        
        # Build response
        response = JobSearchResponse(
            success=True,
            total_results=len(jobs_data),
            results_count=len(job_schemas),
            jobs=job_schemas,
            search_params={
                'keyword': payload.keyword,
                'location': payload.location,
                'job_types': job_types or [],
                'experience_levels': experience_levels or [],
                'date_posted': date_posted,
                'limit': payload.limit or 25
            },
            message=f"Successfully fetched {len(job_schemas)} jobs"
        )
        
        return 200, response
        
    except Exception as e:
        logger.error(f"Error in job search: {str(e)}", exc_info=True)
        return 500, ErrorResponse(
            success=False,
            error="Failed to search jobs",
            details=str(e)
        )


@router.get("/listings", response=List[JobListingSchema])
def get_job_listings(
    request,
    keyword: str = None,
    location: str = None,
    limit: int = 25,
    offset: int = 0
):
    """
    Get job listings from database
    
    This endpoint retrieves job listings stored in the database.
    You can filter by keyword and location.
    
    Args:
        keyword: Filter by job title keyword (optional)
        location: Filter by location (optional)
        limit: Maximum number of results (default: 25)
        offset: Offset for pagination (default: 0)
    
    Returns:
        List of job listings
    """
    try:
        queryset = JobListing.objects.all()
        
        # Apply filters
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Convert to schema
        job_schemas = []
        for job in queryset:
            job_schemas.append(JobListingSchema(
                job_id=job.job_id,
                linkedin_url=job.linkedin_url,
                title=job.title,
                company_name=job.company_name,
                location=job.location,
                description=job.description,
                employment_type=job.employment_type,
                experience_level=job.experience_level,
                posted_date=job.posted_date,
                applicants_count=job.applicants_count,
                company_logo_url=job.company_logo_url,
            ))
        
        return job_schemas
        
    except Exception as e:
        logger.error(f"Error getting job listings: {str(e)}")
        return []


@router.get("/listings/{job_id}", response={200: JobListingSchema, 404: ErrorResponse})
def get_job_by_id(request, job_id: str):
    """
    Get a specific job listing by ID
    
    Args:
        job_id: LinkedIn job ID
    
    Returns:
        Job listing details
    """
    try:
        job = JobListing.objects.get(job_id=job_id)
        
        return 200, JobListingSchema(
            job_id=job.job_id,
            linkedin_url=job.linkedin_url,
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            description=job.description,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            posted_date=job.posted_date,
            applicants_count=job.applicants_count,
            company_logo_url=job.company_logo_url,
        )
        
    except JobListing.DoesNotExist:
        return 404, ErrorResponse(
            success=False,
            error="Job not found",
            details=f"Job with ID {job_id} not found in database"
        )
    except Exception as e:
        logger.error(f"Error getting job by ID: {str(e)}")
        return 404, ErrorResponse(
            success=False,
            error="Failed to get job",
            details=str(e)
        )


@router.get("/search-history", response=List[dict])
def get_search_history(request, limit: int = 10):
    """
    Get recent job search history
    
    Args:
        limit: Maximum number of search records to return (default: 10)
    
    Returns:
        List of recent job searches
    """
    try:
        searches = JobSearch.objects.all()[:limit]
        
        search_list = []
        for search in searches:
            search_list.append({
                'id': search.id,
                'keyword': search.keyword,
                'location': search.location,
                'job_types': search.job_types,
                'experience_levels': search.experience_levels,
                'total_results': search.total_results,
                'results_fetched': search.results_fetched,
                'created_at': search.created_at.isoformat(),
            })
        
        return search_list
        
    except Exception as e:
        logger.error(f"Error getting search history: {str(e)}")
        return []


@router.post("/create-from-url", response={200: JobListingSchema, 400: ErrorResponse, 500: ErrorResponse})
def create_job_from_url(request, payload: CreateJobFromUrlRequest):
    """
    Create a job listing from a LinkedIn URL
    
    This endpoint:
    1. Takes a LinkedIn job URL
    2. Extracts the job ID from the URL
    3. Checks if the job already exists in the database
    4. If not, fetches the job page from LinkedIn
    5. Extracts all job information
    6. Creates a new JobListing in the database
    7. Returns the created job data
    
    Args:
        payload: Request containing the LinkedIn URL
    
    Returns:
        Created job listing with full details
    """
    try:
        linkedin_url = payload.linkedin_url.strip()
        
        # Extract job ID from LinkedIn URL
        # URLs can be like:
        # - https://www.linkedin.com/jobs/view/4309395824
        # - https://at.linkedin.com/jobs/view/software-engineer-at-company-4309395824
        # - https://linkedin.com/jobs/view/4309395824?param=value
        
        import re
        job_id_match = re.search(r'/jobs/view/(?:[\w-]+?-)?(\d+)', linkedin_url)
        
        if not job_id_match:
            return 400, ErrorResponse(
                success=False,
                error="Invalid LinkedIn URL",
                details="Could not extract job ID from URL. Please provide a valid LinkedIn job URL."
            )
        
        job_id = job_id_match.group(1)
        logger.info(f"Extracted job ID {job_id} from URL: {linkedin_url}")
        
        # Check if job already exists
        existing_job = JobListing.objects.filter(job_id=job_id).first()
        
        if existing_job:
            logger.info(f"Job {job_id} already exists in database")
            return 200, JobListingSchema(
                job_id=existing_job.job_id,
                linkedin_url=existing_job.linkedin_url,
                title=existing_job.title,
                company_name=existing_job.company_name,
                location=existing_job.location,
                description=existing_job.description,
                employment_type=existing_job.employment_type,
                experience_level=existing_job.experience_level,
                posted_date=existing_job.posted_date,
                applicants_count=existing_job.applicants_count,
                company_logo_url=existing_job.company_logo_url,
            )
        
        # Fetch job details from LinkedIn
        scraper = LinkedInJobScraper()
        job_details = scraper.get_job_details(job_id)
        
        if not job_details:
            return 500, ErrorResponse(
                success=False,
                error="Failed to fetch job details",
                details=f"Could not retrieve job information from LinkedIn for job {job_id}"
            )
        
        # Validate required fields
        if not job_details.get('title'):
            return 500, ErrorResponse(
                success=False,
                error="Incomplete job data",
                details="Could not extract job title from LinkedIn page"
            )
        
        # Create new job listing
        job_listing = JobListing.objects.create(
            job_id=job_id,
            linkedin_url=job_details.get('linkedin_url', linkedin_url),
            title=job_details.get('title', 'Unknown'),
            company_name=job_details.get('company_name', 'Unknown'),
            location=job_details.get('location', 'Unknown'),
            description=job_details.get('description'),
            employment_type=job_details.get('employment_type'),
            experience_level=job_details.get('experience_level'),
            posted_date=job_details.get('posted_date'),
            applicants_count=job_details.get('applicants_count'),
            company_logo_url=job_details.get('company_logo_url'),
        )
        
        logger.info(f"Successfully created job listing for {job_id}: {job_listing.title}")
        
        # Return the created job
        return 200, JobListingSchema(
            job_id=job_listing.job_id,
            linkedin_url=job_listing.linkedin_url,
            title=job_listing.title,
            company_name=job_listing.company_name,
            location=job_listing.location,
            description=job_listing.description,
            employment_type=job_listing.employment_type,
            experience_level=job_listing.experience_level,
            posted_date=job_listing.posted_date,
            applicants_count=job_listing.applicants_count,
            company_logo_url=job_listing.company_logo_url,
        )
        
    except Exception as e:
        logger.error(f"Error creating job from URL: {str(e)}", exc_info=True)
        return 500, ErrorResponse(
            success=False,
            error="Failed to create job from URL",
            details=str(e)
        )


@router.post("/enrich/{job_id}", response={200: JobListingSchema, 404: ErrorResponse, 500: ErrorResponse})
def enrich_job_details(request, job_id: str):
    """
    Fetch detailed job information from LinkedIn and update the database
    
    This endpoint:
    1. Takes a LinkedIn job ID
    2. Fetches the full job page from LinkedIn
    3. Extracts detailed information (full description, employment type, etc.)
    4. Updates the JobListing in the database
    5. Returns the enriched job data
    
    Args:
        job_id: LinkedIn job ID
    
    Returns:
        Updated job listing with full details
    """
    try:
        # Check if job exists in database
        try:
            job_listing = JobListing.objects.get(job_id=job_id)
            logger.info(f"Found existing job listing for {job_id}")
        except JobListing.DoesNotExist:
            return 404, ErrorResponse(
                success=False,
                error="Job not found",
                details=f"Job with ID {job_id} not found in database. Please search for jobs first."
            )
        
        # Fetch detailed information from LinkedIn
        scraper = LinkedInJobScraper()
        job_details = scraper.get_job_details(job_id)
        
        if not job_details:
            return 500, ErrorResponse(
                success=False,
                error="Failed to fetch job details",
                details=f"Could not retrieve details from LinkedIn for job {job_id}"
            )
        
        # Update the job listing with detailed information
        updated_fields = []
        
        if job_details.get('title') and not job_listing.title:
            job_listing.title = job_details['title']
            updated_fields.append('title')
        
        if job_details.get('company_name') and not job_listing.company_name:
            job_listing.company_name = job_details['company_name']
            updated_fields.append('company_name')
        
        if job_details.get('location') and not job_listing.location:
            job_listing.location = job_details['location']
            updated_fields.append('location')
        
        if job_details.get('description'):
            job_listing.description = job_details['description']
            updated_fields.append('description')
        
        if job_details.get('employment_type'):
            job_listing.employment_type = job_details['employment_type']
            updated_fields.append('employment_type')
        
        if job_details.get('experience_level'):
            job_listing.experience_level = job_details['experience_level']
            updated_fields.append('experience_level')
        
        if job_details.get('applicants_count'):
            job_listing.applicants_count = job_details['applicants_count']
            updated_fields.append('applicants_count')
        
        if job_details.get('company_logo_url') and not job_listing.company_logo_url:
            job_listing.company_logo_url = job_details['company_logo_url']
            updated_fields.append('company_logo_url')
        
        # Save the updated job listing
        job_listing.save()
        
        logger.info(f"Successfully enriched job {job_id}. Updated fields: {', '.join(updated_fields)}")
        
        # Return the updated job
        return 200, JobListingSchema(
            job_id=job_listing.job_id,
            linkedin_url=job_listing.linkedin_url,
            title=job_listing.title,
            company_name=job_listing.company_name,
            location=job_listing.location,
            description=job_listing.description,
            employment_type=job_listing.employment_type,
            experience_level=job_listing.experience_level,
            posted_date=job_listing.posted_date,
            applicants_count=job_listing.applicants_count,
            company_logo_url=job_listing.company_logo_url,
        )
        
    except Exception as e:
        logger.error(f"Error enriching job details: {str(e)}", exc_info=True)
        return 500, ErrorResponse(
            success=False,
            error="Failed to enrich job details",
            details=str(e)
        )

