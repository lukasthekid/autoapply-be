from django.contrib import admin
from .models import JobListing, JobSearch


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    """Admin interface for JobListing model"""
    
    list_display = [
        'job_id',
        'title',
        'company_name',
        'location',
        'employment_type',
        'experience_level',
        'posted_date',
        'created_at',
    ]
    
    list_filter = [
        'employment_type',
        'experience_level',
        'created_at',
        'posted_date',
    ]
    
    search_fields = [
        'job_id',
        'title',
        'company_name',
        'location',
        'description',
    ]
    
    readonly_fields = [
        'job_id',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Job Information', {
            'fields': (
                'job_id',
                'linkedin_url',
                'title',
                'company_name',
                'location',
                'description',
            )
        }),
        ('Job Details', {
            'fields': (
                'employment_type',
                'experience_level',
                'posted_date',
                'applicants_count',
                'company_logo_url',
            )
        }),
        ('Search Metadata', {
            'fields': (
                'search_keyword',
                'search_location',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    
    ordering = ['-created_at']


@admin.register(JobSearch)
class JobSearchAdmin(admin.ModelAdmin):
    """Admin interface for JobSearch model"""
    
    list_display = [
        'id',
        'keyword',
        'location',
        'total_results',
        'results_fetched',
        'created_at',
    ]
    
    list_filter = [
        'created_at',
    ]
    
    search_fields = [
        'keyword',
        'location',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Search Parameters', {
            'fields': (
                'keyword',
                'location',
                'job_types',
                'experience_levels',
            )
        }),
        ('Results', {
            'fields': (
                'total_results',
                'results_fetched',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    
    ordering = ['-created_at']
