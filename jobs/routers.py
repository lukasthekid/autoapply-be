from ninja import Router
from typing import List
from ninja_jwt.authentication import JWTAuth
import logging
import time

from .schemas import (
    ProfileSearchRequest,
    JobSearchResponse,
    JobListingSchema,
    CreateJobFromUrlRequest,
    ErrorResponse,
    CreateSearchProfileRequest,
    UpdateSearchProfileRequest,
    SearchProfileSchema,
    SearchProfileListResponse,
    JobTypeEnum,
    ExperienceLevelEnum,
)
from .services import LinkedInJobScraper
from .models import JobListing, JobSearch, SearchProfile

logger = logging.getLogger(__name__)
router = Router(tags=["Jobs"])


def _convert_string_list_to_enums(string_list: List[str], enum_class) -> List:
    """Convert a list of strings to a list of enum values"""
    if not string_list:
        return []
    result = []
    for value in string_list:
        try:
            result.append(enum_class(value))
        except ValueError:
            # Skip invalid enum values
            logger.warning(f"Invalid enum value '{value}' for {enum_class.__name__}, skipping")
    return result


@router.post(
    "/search",
    response={200: JobSearchResponse, 400: ErrorResponse, 500: ErrorResponse},
    auth=JWTAuth(),
)
def search_jobs(request, payload: ProfileSearchRequest):
    """
    Search for jobs on LinkedIn using saved search profiles and enrich them.
    
    This endpoint:
    - Takes only `date_posted` and `limit` from the request payload
    - Loads all search profiles for the authenticated user
    - Executes a LinkedIn search per profile (keyword/location from profile)
    - Collects unique jobs (by job_id) with only job_id and linkedin_url
    - Enriches jobs that are not already in the database
    - Stores enriched jobs in the database
    - Returns full job listings from the database
    """
    try:
        logger.info("=" * 80)
        logger.info("STARTING JOB SEARCH")
        logger.info("=" * 80)
        
        user = request.auth
        profiles = list(SearchProfile.objects.filter(user=user))
        if not profiles:
            logger.warning("No search profiles found for user")
            return 400, ErrorResponse(
                success=False,
                error="No search profiles found",
                details="Create at least one search profile to run a search."
            )

        total_limit = payload.limit or 25
        date_posted = payload.date_posted.value if payload.date_posted else None
        
        logger.info(f"Search parameters: limit={total_limit}, date_posted={date_posted}")
        logger.info(f"Found {len(profiles)} search profile(s) to process")
        
        scraper = LinkedInJobScraper()

        # Evenly distribute the limit across profiles
        per_profile_base = total_limit // len(profiles)
        remainder = total_limit % len(profiles)

        # Collect unique jobs by job_id (only job_id and linkedin_url from search)
        jobs_by_id = {}
        search_meta = []

        # Step 1: Search for jobs across all profiles
        logger.info("-" * 80)
        logger.info("STEP 1: Searching for jobs across all profiles")
        logger.info("-" * 80)
        
        for idx, profile in enumerate(profiles):
            per_profile_limit = per_profile_base + (1 if idx < remainder else 0)
            if per_profile_limit <= 0:
                continue

            logger.info(
                f"[Profile {idx + 1}/{len(profiles)}] Searching jobs for profile ID {profile.id}: "
                f"keyword='{profile.keyword}', location='{profile.location}', "
                f"date_posted='{date_posted}', limit={per_profile_limit}"
            )

            jobs_data = scraper.search_jobs(
                keyword=profile.keyword,
                location=profile.location,
                job_types=profile.job_types or None,
                experience_levels=profile.experience_levels or None,
                date_posted=date_posted,
                limit=per_profile_limit,
            )

            logger.info(
                f"[Profile {idx + 1}/{len(profiles)}] Found {len(jobs_data)} jobs from search"
            )

            search_meta.append({
                "profile_id": profile.id,
                "keyword": profile.keyword,
                "location": profile.location,
                "job_types": profile.job_types,
                "experience_levels": profile.experience_levels,
                "date_posted": date_posted,
                "limit": per_profile_limit,
                "results": len(jobs_data),
            })

            # Collect unique jobs (only job_id and linkedin_url)
            new_jobs_count = 0
            for job_data in jobs_data:
                job_id = job_data.get("job_id")
                if not job_id or job_id in jobs_by_id:
                    continue
                jobs_by_id[job_id] = job_data.get("linkedin_url", f"https://www.linkedin.com/jobs/view/{job_id}")
                new_jobs_count += 1

            logger.info(
                f"[Profile {idx + 1}/{len(profiles)}] Added {new_jobs_count} new unique jobs. "
                f"Total unique jobs so far: {len(jobs_by_id)}"
            )

            # Stop early if we've reached the overall limit
            if len(jobs_by_id) >= total_limit:
                logger.info(f"Reached total limit of {total_limit} unique jobs. Stopping search.")
                break

        # Step 2: Get list of unique job IDs to process
        logger.info("-" * 80)
        logger.info("STEP 2: Combining unique jobs from all profiles")
        logger.info("-" * 80)
        
        unique_job_ids = list(jobs_by_id.keys())[:total_limit]
        logger.info(f"Total unique jobs collected: {len(unique_job_ids)}")
        
        if not unique_job_ids:
            logger.warning("No jobs found for the given criteria")
            return 200, JobSearchResponse(
                success=True,
                total_results=0,
                results_count=0,
                jobs=[],
                search_params={
                    "limit": total_limit,
                    "date_posted": date_posted,
                    "profiles_used": search_meta,
                },
                message="No jobs found for the given criteria",
            )

        # Step 3: Check which jobs are already in the database
        logger.info("-" * 80)
        logger.info("STEP 3: Checking which jobs are already in database")
        logger.info("-" * 80)
        
        existing_jobs = set(
            JobListing.objects.filter(job_id__in=unique_job_ids)
            .values_list('job_id', flat=True)
        )
        
        jobs_to_enrich = [
            job_id for job_id in unique_job_ids 
            if job_id not in existing_jobs
        ]

        logger.info(
            f"Database check complete: {len(existing_jobs)} jobs already exist, "
            f"{len(jobs_to_enrich)} jobs need enrichment"
        )

        # Step 4: Enrich jobs that are not in the database
        logger.info("-" * 80)
        logger.info("STEP 4: Enriching jobs that are not in database")
        logger.info("-" * 80)
        
        if not jobs_to_enrich:
            logger.info("No jobs need enrichment. All jobs already exist in database.")
        else:
            logger.info(f"Starting enrichment of {len(jobs_to_enrich)} jobs...")
        
        enriched_count = 0
        failed_count = 0
        
        for idx, job_id in enumerate(jobs_to_enrich):
            try:
                # Rate limiting: wait 2 seconds between enrichment requests to avoid blocking
                # Apply delay before each request (except the first one) to be respectful to LinkedIn
                if idx > 0:
                    logger.debug(f"Rate limiting: waiting 2 seconds before next enrichment...")
                    time.sleep(2)
                
                logger.info(f"[{idx + 1}/{len(jobs_to_enrich)}] Enriching job {job_id}...")
                job_details = scraper.get_job_details(job_id)
                
                if not job_details:
                    logger.warning(f"[{idx + 1}/{len(jobs_to_enrich)}] ✗ Failed to enrich job {job_id}: No details returned")
                    failed_count += 1
                    continue
                
                # Validate required fields
                if not job_details.get('title'):
                    logger.warning(f"[{idx + 1}/{len(jobs_to_enrich)}] ✗ Failed to enrich job {job_id}: Missing title")
                    failed_count += 1
                    continue
                
                # Create job listing in database
                JobListing.objects.create(
                    job_id=job_id,
                    linkedin_url=job_details.get('linkedin_url', jobs_by_id[job_id]),
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
                
                enriched_count += 1
                logger.info(
                    f"[{idx + 1}/{len(jobs_to_enrich)}] ✓ Successfully enriched and stored job {job_id}: "
                    f"'{job_details.get('title', 'Unknown')}' at {job_details.get('company_name', 'Unknown')}"
                )
                
            except Exception as e:
                logger.error(f"[{idx + 1}/{len(jobs_to_enrich)}] ✗ Error enriching job {job_id}: {str(e)}", exc_info=True)
                failed_count += 1
                # Continue with next job even if this one fails
                continue

        logger.info("-" * 80)
        logger.info(
            f"Enrichment complete: {enriched_count} enriched, "
            f"{failed_count} failed, {len(existing_jobs)} already existed"
        )
        logger.info("-" * 80)

        # Step 5: Query database and return full job listings
        logger.info("-" * 80)
        logger.info("STEP 5: Querying database and preparing response")
        logger.info("-" * 80)
        
        job_listings = JobListing.objects.filter(job_id__in=unique_job_ids).order_by('-created_at')
        logger.info(f"Retrieved {job_listings.count()} job listings from database")
        
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

        logger.info("=" * 80)
        logger.info("JOB SEARCH COMPLETE")
        logger.info(f"Total results: {len(job_schemas)}")
        logger.info(f"Summary: {enriched_count} enriched, {failed_count} failed, {len(existing_jobs)} already existed")
        logger.info("=" * 80)

        response = JobSearchResponse(
            success=True,
            total_results=len(job_schemas),
            results_count=len(job_schemas),
            jobs=job_schemas,
            search_params={
                "limit": total_limit,
                "date_posted": date_posted,
                "profiles_used": search_meta,
                "enriched": enriched_count,
                "failed": failed_count,
                "existing": len(existing_jobs),
            },
            message=f"Successfully fetched {len(job_schemas)} unique jobs across {len(profiles)} profiles. Enriched {enriched_count} new jobs.",
        )
        
        return 200, response
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("JOB SEARCH FAILED")
        logger.error("=" * 80)
        logger.error(f"Error in job search: {str(e)}", exc_info=True)
        logger.error("=" * 80)
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


@router.post(
    "/search-profiles",
    response={201: SearchProfileSchema, 400: ErrorResponse},
    auth=JWTAuth(),
    summary="Create a search profile",
    description="Create a new search profile for the authenticated user"
)
def create_search_profile(request, payload: CreateSearchProfileRequest):
    """
    Create a new search profile.
    
    Creates a new search profile with the specified search parameters.
    The profile is linked to the authenticated user.
    """
    try:
        user = request.auth
        
        # Create the search profile
        search_profile = SearchProfile.objects.create(
            user=user,
            name=payload.name,
            keyword=payload.keyword,
            location=payload.location,
            job_types=[jt.value for jt in payload.job_types] if payload.job_types else [],
            experience_levels=[el.value for el in payload.experience_levels] if payload.experience_levels else [],
        )
        
        logger.info(f"Created search profile {search_profile.id} for user {user.username}")
        
        return 201, SearchProfileSchema(
            id=search_profile.id,
            name=search_profile.name,
            keyword=search_profile.keyword,
            location=search_profile.location,
            job_types=_convert_string_list_to_enums(search_profile.job_types, JobTypeEnum),
            experience_levels=_convert_string_list_to_enums(search_profile.experience_levels, ExperienceLevelEnum),
            created_at=search_profile.created_at,
            updated_at=search_profile.updated_at,
        )
        
    except Exception as e:
        logger.error(f"Error creating search profile: {str(e)}", exc_info=True)
        return 400, ErrorResponse(
            success=False,
            error="Failed to create search profile",
            details=str(e)
        )


@router.get(
    "/search-profiles",
    response=SearchProfileListResponse,
    auth=JWTAuth(),
    summary="List search profiles",
    description="Get all search profiles for the authenticated user"
)
def list_search_profiles(request):
    """
    List all search profiles.
    
    Returns all search profiles created by the authenticated user.
    """
    try:
        user = request.auth
        profiles = SearchProfile.objects.filter(user=user).order_by('-created_at')
        
        profile_schemas = []
        for profile in profiles:
            profile_schemas.append(SearchProfileSchema(
                id=profile.id,
                name=profile.name,
                keyword=profile.keyword,
                location=profile.location,
                job_types=_convert_string_list_to_enums(profile.job_types, JobTypeEnum),
                experience_levels=_convert_string_list_to_enums(profile.experience_levels, ExperienceLevelEnum),
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            ))
        
        return SearchProfileListResponse(
            profiles=profile_schemas,
            count=len(profile_schemas)
        )
        
    except Exception as e:
        logger.error(f"Error listing search profiles: {str(e)}", exc_info=True)
        return SearchProfileListResponse(profiles=[], count=0)


@router.get(
    "/search-profiles/{profile_id}",
    response={200: SearchProfileSchema, 404: ErrorResponse},
    auth=JWTAuth(),
    summary="Get a search profile",
    description="Get a specific search profile by ID"
)
def get_search_profile(request, profile_id: int):
    """
    Get a specific search profile.
    
    Returns the search profile with the specified ID if it belongs to the authenticated user.
    """
    try:
        user = request.auth
        
        try:
            profile = SearchProfile.objects.get(id=profile_id, user=user)
        except SearchProfile.DoesNotExist:
            return 404, ErrorResponse(
                success=False,
                error="Search profile not found",
                details=f"Search profile with ID {profile_id} not found or you don't have permission to access it"
            )
        
        return 200, SearchProfileSchema(
            id=profile.id,
            name=profile.name,
            keyword=profile.keyword,
            location=profile.location,
            job_types=_convert_string_list_to_enums(profile.job_types, JobTypeEnum),
            experience_levels=_convert_string_list_to_enums(profile.experience_levels, ExperienceLevelEnum),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
        
    except Exception as e:
        logger.error(f"Error getting search profile: {str(e)}", exc_info=True)
        return 404, ErrorResponse(
            success=False,
            error="Failed to get search profile",
            details=str(e)
        )


@router.put(
    "/search-profiles/{profile_id}",
    response={200: SearchProfileSchema, 404: ErrorResponse, 400: ErrorResponse},
    auth=JWTAuth(),
    summary="Update a search profile",
    description="Update an existing search profile"
)
def update_search_profile(request, profile_id: int, payload: UpdateSearchProfileRequest):
    """
    Update a search profile.
    
    Updates the specified search profile. Only provided fields will be updated.
    The profile must belong to the authenticated user.
    """
    try:
        user = request.auth
        
        try:
            profile = SearchProfile.objects.get(id=profile_id, user=user)
        except SearchProfile.DoesNotExist:
            return 404, ErrorResponse(
                success=False,
                error="Search profile not found",
                details=f"Search profile with ID {profile_id} not found or you don't have permission to access it"
            )
        
        # Update fields if provided
        if payload.name is not None:
            profile.name = payload.name
        
        if payload.keyword is not None:
            profile.keyword = payload.keyword
        
        if payload.location is not None:
            profile.location = payload.location
        
        if payload.job_types is not None:
            profile.job_types = [jt.value for jt in payload.job_types]
        
        if payload.experience_levels is not None:
            profile.experience_levels = [el.value for el in payload.experience_levels]
        
        profile.save()
        
        logger.info(f"Updated search profile {profile.id} for user {user.username}")
        
        return 200, SearchProfileSchema(
            id=profile.id,
            name=profile.name,
            keyword=profile.keyword,
            location=profile.location,
            job_types=_convert_string_list_to_enums(profile.job_types, JobTypeEnum),
            experience_levels=_convert_string_list_to_enums(profile.experience_levels, ExperienceLevelEnum),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
        
    except Exception as e:
        logger.error(f"Error updating search profile: {str(e)}", exc_info=True)
        return 400, ErrorResponse(
            success=False,
            error="Failed to update search profile",
            details=str(e)
        )


@router.delete(
    "/search-profiles/{profile_id}",
    response={200: dict, 404: ErrorResponse},
    auth=JWTAuth(),
    summary="Delete a search profile",
    description="Delete a search profile"
)
def delete_search_profile(request, profile_id: int):
    """
    Delete a search profile.
    
    Deletes the specified search profile. The profile must belong to the authenticated user.
    """
    try:
        user = request.auth
        
        try:
            profile = SearchProfile.objects.get(id=profile_id, user=user)
        except SearchProfile.DoesNotExist:
            return 404, ErrorResponse(
                success=False,
                error="Search profile not found",
                details=f"Search profile with ID {profile_id} not found or you don't have permission to access it"
            )
        
        profile.delete()
        
        logger.info(f"Deleted search profile {profile_id} for user {user.username}")
        
        return 200, {"success": True, "message": "Search profile deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting search profile: {str(e)}", exc_info=True)
        return 404, ErrorResponse(
            success=False,
            error="Failed to delete search profile",
            details=str(e)
        )

