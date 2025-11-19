"""
Django management command to delete job listings that have no applications.

This command removes job listings from the database where no user has applied.
This helps clean up junk data and keep the database lean.

Usage:
    python manage.py cleanup_unused_jobs
    
    # Dry run (show what would be deleted without actually deleting)
    python manage.py cleanup_unused_jobs --dry-run
    
    # Verbose output
    python manage.py cleanup_unused_jobs --verbose
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from jobs.models import JobListing, JobApplication
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete job listings that have no applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting cleanup of unused job listings...'))
        
        # Find all job listings that have no applications
        # Using a subquery to find job_listing IDs that are referenced in JobApplication
        job_listings_with_applications = JobApplication.objects.filter(
            job_listing__isnull=False
        ).values_list('job_listing_id', flat=True).distinct()
        
        # Get job listings that are NOT in the list of job listings with applications
        unused_jobs = JobListing.objects.exclude(
            id__in=job_listings_with_applications
        )
        
        count = unused_jobs.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No unused job listings found. Database is clean!'))
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {count} job listing(s) with no applications')
        )
        
        if verbose:
            self.stdout.write('\nJob listings to be deleted:')
            for job in unused_jobs[:10]:  # Show first 10
                self.stdout.write(f'  - {job.job_id}: {job.title} at {job.company_name}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: Would delete {count} job listing(s). '
                    'Run without --dry-run to actually delete them.'
                )
            )
        else:
            # Delete the unused job listings
            deleted_count, _ = unused_jobs.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully deleted {deleted_count} unused job listing(s)'
                )
            )
            logger.info(f'Deleted {deleted_count} unused job listings')

