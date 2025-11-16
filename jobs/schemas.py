from typing import List, Optional
from datetime import datetime
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

