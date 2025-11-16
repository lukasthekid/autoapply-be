from django.test import TestCase
from .models import JobListing, JobSearch


class JobListingModelTest(TestCase):
    """Test cases for JobListing model"""
    
    def setUp(self):
        """Set up test data"""
        self.job = JobListing.objects.create(
            job_id="test123",
            linkedin_url="https://www.linkedin.com/jobs/view/test123",
            title="Test Data Scientist",
            company_name="Test Company",
            location="Vienna, Austria",
            description="Test description",
            employment_type="full_time",
            experience_level="mid_senior_level",
        )
    
    def test_job_creation(self):
        """Test job listing creation"""
        self.assertEqual(self.job.job_id, "test123")
        self.assertEqual(self.job.title, "Test Data Scientist")
        self.assertEqual(self.job.company_name, "Test Company")
    
    def test_job_string_representation(self):
        """Test job string representation"""
        expected_str = "Test Data Scientist at Test Company"
        self.assertEqual(str(self.job), expected_str)


class JobSearchModelTest(TestCase):
    """Test cases for JobSearch model"""
    
    def setUp(self):
        """Set up test data"""
        self.search = JobSearch.objects.create(
            keyword="Data Scientist",
            location="Vienna",
            job_types=["full_time"],
            experience_levels=["mid_senior_level"],
            total_results=100,
            results_fetched=25,
        )
    
    def test_search_creation(self):
        """Test job search creation"""
        self.assertEqual(self.search.keyword, "Data Scientist")
        self.assertEqual(self.search.location, "Vienna")
        self.assertEqual(self.search.job_types, ["full_time"])
    
    def test_search_string_representation(self):
        """Test search string representation"""
        expected_str = "Search: Data Scientist in Vienna"
        self.assertEqual(str(self.search), expected_str)
