from django.db import models
from django.contrib.postgres.fields import ArrayField


class JobListing(models.Model):
    """Model to store job listings from LinkedIn"""
    
    # Job identifiers
    job_id = models.CharField(max_length=255, unique=True, db_index=True)
    linkedin_url = models.URLField(max_length=500)
    
    # Basic job information
    title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    
    # Job details
    description = models.TextField(blank=True, null=True)
    employment_type = models.CharField(max_length=50, blank=True, null=True)  # full_time, part_time, etc.
    experience_level = models.CharField(max_length=50, blank=True, null=True)  # entry_level, mid_senior, etc.
    
    # Additional information
    posted_date = models.DateTimeField(blank=True, null=True)
    applicants_count = models.IntegerField(blank=True, null=True)
    company_logo_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Search metadata
    search_keyword = models.CharField(max_length=255, blank=True, null=True)
    search_location = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_id']),
            models.Index(fields=['title']),
            models.Index(fields=['company_name']),
            models.Index(fields=['location']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company_name}"


class JobSearch(models.Model):
    """Model to store job search history and cache results"""
    
    # Search parameters
    keyword = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    job_types = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    experience_levels = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    
    # Search results metadata
    total_results = models.IntegerField(default=0)
    results_fetched = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['keyword', 'location']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Search: {self.keyword} in {self.location}"
