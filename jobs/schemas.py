from typing import List, Optional, Dict
from datetime import datetime, date
from ninja import Schema
from enum import Enum


class JobTypeEnum(str, Enum):
    """Enum for job types matching LinkedIn's job types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"


class ExperienceLevelEnum(str, Enum):
    """Enum for experience levels matching LinkedIn's experience levels"""
    INTERNSHIP = "internship"
    ENTRY_LEVEL = "entry_level"
    ASSOCIATE = "associate"
    MID_SENIOR_LEVEL = "mid_senior_level"
    DIRECTOR = "director"


class DatePostedEnum(str, Enum):
    """Enum for date posted filter matching LinkedIn's time filters"""
    ANY_TIME = "any_time"
    PAST_24_HOURS = "past_24_hours"
    PAST_WEEK = "past_week"
    PAST_MONTH = "past_month"


class ApplicationStatusEnum(str, Enum):
    """Enum for job application status"""
    APPLIED = "applied"
    DECLINED = "declined"
    PHONE_SCREENING = "phone_screening"
    FIRST_ROUND = "first_round"
    SECOND_ROUND = "second_round"
    THIRD_ROUND = "third_round"
    OFFER = "offer"


class JobSearchRequest(Schema):
    """Schema for job search request"""
    keyword: str
    location: str
    job_types: Optional[List[JobTypeEnum]] = None
    experience_levels: Optional[List[ExperienceLevelEnum]] = None
    date_posted: Optional[DatePostedEnum] = None
    limit: Optional[int] = 25  # Default to 25 results
    
    class Config:
        # Example for API documentation
        schema_extra = {
            "example": {
                "keyword": "Data Scientist",
                "location": "Vienna",
                "job_types": ["full_time", "contract"],
                "experience_levels": ["entry_level", "mid_senior_level"],
                "date_posted": "past_week",
                "limit": 25
            }
        }


class JobListingSchema(Schema):
    """Schema for a single job listing"""
    job_id: str
    linkedin_url: str
    title: str
    company_name: str
    location: str
    description: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    posted_date: Optional[datetime] = None
    applicants_count: Optional[int] = None
    company_logo_url: Optional[str] = None
    is_enriched: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "3789456123",
                "linkedin_url": "https://www.linkedin.com/jobs/view/3789456123",
                "title": "Data Scientist",
                "company_name": "Tech Company Inc.",
                "location": "Vienna, Austria",
                "description": "We are looking for a talented Data Scientist...",
                "employment_type": "full_time",
                "experience_level": "mid_senior_level",
                "posted_date": "2025-11-15T10:30:00",
                "applicants_count": 50,
                "company_logo_url": "https://media.licdn.com/dms/image/..."
            }
        }


class JobSearchResponse(Schema):
    """Schema for job search response"""
    success: bool
    total_results: int
    results_count: int
    jobs: List[JobListingSchema]
    search_params: dict
    message: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "total_results": 150,
                "results_count": 25,
                "jobs": [
                    {
                        "job_id": "3789456123",
                        "linkedin_url": "https://www.linkedin.com/jobs/view/3789456123",
                        "title": "Data Scientist",
                        "company_name": "Tech Company Inc.",
                        "location": "Vienna, Austria",
                        "description": "We are looking for a talented Data Scientist...",
                        "employment_type": "full_time",
                        "experience_level": "mid_senior_level",
                        "posted_date": "2025-11-15T10:30:00",
                        "applicants_count": 50,
                        "company_logo_url": "https://media.licdn.com/dms/image/..."
                    }
                ],
                "search_params": {
                    "keyword": "Data Scientist",
                    "location": "Vienna",
                    "job_types": ["full_time"],
                    "experience_levels": ["mid_senior_level"]
                },
                "message": "Successfully fetched 25 jobs"
            }
        }


class CreateJobFromUrlRequest(Schema):
    """Schema for creating a job from LinkedIn URL"""
    linkedin_url: str
    
    class Config:
        schema_extra = {
            "example": {
                "linkedin_url": "https://www.linkedin.com/jobs/view/4309395824"
            }
        }


class ErrorResponse(Schema):
    """Schema for error response"""
    success: bool = False
    error: str
    details: Optional[str] = None


class CreateJobApplicationRequest(Schema):
    """Schema for creating a job application"""
    job_id: Optional[str] = None  # Optional: if provided, links to existing JobListing
    job_title: str
    company_name: str
    job_location: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "3789456123",
                "job_title": "Data Scientist",
                "company_name": "Tech Company Inc.",
                "job_location": "Vienna, Austria",
                "job_url": "https://www.linkedin.com/jobs/view/3789456123",
                "notes": "Applied via LinkedIn"
            }
        }


class JobApplicationSchema(Schema):
    """Schema for a job application"""
    id: int
    job_id: Optional[str] = None  # From linked JobListing if exists
    job_title: str
    company_name: str
    job_location: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None
    status: ApplicationStatusEnum = ApplicationStatusEnum.APPLIED
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "job_id": "3789456123",
                "job_title": "Data Scientist",
                "company_name": "Tech Company Inc.",
                "job_location": "Vienna, Austria",
                "job_url": "https://www.linkedin.com/jobs/view/3789456123",
                "notes": "Applied via LinkedIn",
                "status": "applied",
                "applied_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z"
            }
        }


class JobApplicationListResponse(Schema):
    """Schema for listing job applications"""
    applications: List[JobApplicationSchema]
    count: int
    
    class Config:
        schema_extra = {
            "example": {
                "applications": [
                    {
                        "id": 1,
                        "job_id": "3789456123",
                        "job_title": "Data Scientist",
                        "company_name": "Tech Company Inc.",
                        "job_location": "Vienna, Austria",
                        "job_url": "https://www.linkedin.com/jobs/view/3789456123",
                        "notes": "Applied via LinkedIn",
                        "applied_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T10:30:00Z"
                    }
                ],
                "count": 1
            }
        }


class CreateJobApplicationResponse(Schema):
    """Schema for create job application response"""
    success: bool = True
    application: JobApplicationSchema


class CheckApplicationResponse(Schema):
    """Schema for checking if user has applied to a job"""
    has_applied: bool
    
    class Config:
        schema_extra = {
            "example": {
                "has_applied": True
            }
        }


class UpdateApplicationStatusRequest(Schema):
    """Schema for updating application status"""
    status: ApplicationStatusEnum
    
    class Config:
        schema_extra = {
            "example": {
                "status": "phone_screening"
            }
        }


class UpdateApplicationStatusResponse(Schema):
    """Schema for update application status response"""
    success: bool = True
    application: JobApplicationSchema


class ApplicationStatsResponse(Schema):
    """Schema for job application statistics"""
    total_applications: int
    applications_this_week: int
    applications_last_7_days: Dict[str, int]  # Maps date (YYYY-MM-DD) to count
    status_counts: dict  # Maps status to count
    
    class Config:
        schema_extra = {
            "example": {
                "total_applications": 25,
                "applications_this_week": 5,
                "applications_last_7_days": {
                    "2025-01-15": 2,
                    "2025-01-16": 1,
                    "2025-01-17": 0,
                    "2025-01-18": 3,
                    "2025-01-19": 1,
                    "2025-01-20": 0,
                    "2025-01-21": 2
                },
                "status_counts": {
                    "applied": 15,
                    "phone_screening": 3,
                    "first_round": 2,
                    "second_round": 1,
                    "third_round": 0,
                    "offer": 1,
                    "declined": 3
                }
            }
        }