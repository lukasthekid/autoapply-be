from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model

User = get_user_model()


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


class SearchProfile(models.Model):
    """Model to store user-defined job search profiles"""
    
    # User who owns this profile
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_profiles',
        db_index=True
    )
    
    # Profile name/title (optional, for user identification)
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional name for this search profile"
    )
    
    # Search parameters (matching JobSearchRequest)
    keyword = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    job_types = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="List of job types (full_time, part_time, contract, etc.)"
    )
    experience_levels = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text="List of experience levels (entry_level, mid_senior_level, etc.)"
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['keyword', 'location']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Search Profile'
        verbose_name_plural = 'Search Profiles'
    
    def __str__(self):
        profile_name = f" ({self.name})" if self.name else ""
        return f"Profile{profile_name}: {self.keyword} in {self.location}"


class JobApplication(models.Model):
    """Model to track user job applications"""
    
    # Application status choices
    class ApplicationStatus(models.TextChoices):
        APPLIED = "applied", "Applied"
        DECLINED = "declined", "Declined"
        PHONE_SCREENING = "phone_screening", "Phone Screening"
        FIRST_ROUND = "first_round", "First Round"
        SECOND_ROUND = "second_round", "Second Round"
        THIRD_ROUND = "third_round", "Third Round"
        OFFER = "offer", "Offer"
    
    # User who applied
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        db_index=True
    )
    
    # Link to job listing (nullable for custom applications)
    job_listing = models.ForeignKey(
        JobListing,
        on_delete=models.SET_NULL,
        related_name='applications',
        null=True,
        blank=True,
        db_index=True
    )
    
    # Job details (stored directly for custom jobs or as backup)
    job_title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=500)
    job_location = models.CharField(max_length=500, blank=True, null=True)
    job_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Application metadata
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about the application")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED,
        db_index=True,
        help_text="Current status of the application"
    )
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', '-applied_at']),
            models.Index(fields=['-applied_at']),
            models.Index(fields=['company_name']),
            models.Index(fields=['status']),
        ]
        constraints = [
            # Prevent duplicate applications for the same user and job listing
            models.UniqueConstraint(
                fields=['user', 'job_listing'],
                condition=models.Q(job_listing__isnull=False),
                name='unique_user_job_listing'
            ),
        ]
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
    
    def __str__(self):
        return f"{self.user.username} applied to {self.job_title} at {self.company_name}"
