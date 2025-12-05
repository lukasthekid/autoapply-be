import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import time
import logging

logger = logging.getLogger(__name__)


class LinkedInJobScraper:
    """Service to scrape job listings from LinkedIn"""
    
    BASE_URL = "https://www.linkedin.com/jobs/search"
    
    # LinkedIn job type mapping
    JOB_TYPE_MAPPING = {
        "full_time": "F",
        "part_time": "P",
        "contract": "C",
        "temporary": "T",
        "internship": "I",
    }
    
    # LinkedIn experience level mapping
    EXPERIENCE_LEVEL_MAPPING = {
        "internship": "1",
        "entry_level": "2",
        "associate": "3",
        "mid_senior_level": "4",
        "director": "5",
    }
    
    # LinkedIn date posted mapping (f_TPR parameter)
    # TPR = Time Posted Range
    DATE_POSTED_MAPPING = {
        "any_time": None,  # No filter
        "past_24_hours": "r86400",  # 24 hours in seconds
        "past_week": "r604800",  # 7 days in seconds
        "past_month": "r2592000",  # 30 days in seconds
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def build_search_url(
        self,
        keyword: str,
        location: str,
        job_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        date_posted: Optional[str] = None,
        start: int = 0
    ) -> str:
        """Build LinkedIn job search URL with parameters"""
        
        params = {
            'keywords': keyword,
            'location': location,
            'start': start,
        }
        
        # Add job type filters
        if job_types:
            job_type_codes = [self.JOB_TYPE_MAPPING.get(jt) for jt in job_types if jt in self.JOB_TYPE_MAPPING]
            if job_type_codes:
                params['f_JT'] = ','.join(job_type_codes)
        
        # Add experience level filters
        if experience_levels:
            exp_level_codes = [self.EXPERIENCE_LEVEL_MAPPING.get(el) for el in experience_levels if el in self.EXPERIENCE_LEVEL_MAPPING]
            if exp_level_codes:
                params['f_E'] = ','.join(exp_level_codes)
        
        # Add date posted filter
        if date_posted and date_posted in self.DATE_POSTED_MAPPING:
            date_code = self.DATE_POSTED_MAPPING.get(date_posted)
            if date_code:  # Only add if not None (any_time)
                params['f_TPR'] = date_code
        
        # Build URL with parameters
        param_string = '&'.join([f"{key}={requests.utils.quote(str(value))}" for key, value in params.items()])
        return f"{self.BASE_URL}?{param_string}"
    
    def parse_job_card(self, job_card) -> Optional[Dict]:
        """Parse individual job card from LinkedIn HTML"""
        try:
            job_data = {}
            
            # Extract job ID from data attribute or link
            job_id = job_card.get('data-entity-urn', '')
            if job_id:
                job_id = job_id.split(':')[-1]
            else:
                # Try to extract from link
                link = job_card.find('a', class_='base-card__full-link')
                if link and link.get('href'):
                    job_id_match = re.search(r'/view/(\d+)', link.get('href'))
                    if job_id_match:
                        job_id = job_id_match.group(1)
            
            if not job_id:
                return None
            
            job_data['job_id'] = job_id
            
            # Extract job title
            title_elem = job_card.find('h3', class_='base-search-card__title')
            if title_elem:
                job_data['title'] = title_elem.get_text(strip=True)
            else:
                return None
            
            # Extract company name
            company_elem = job_card.find('h4', class_='base-search-card__subtitle')
            if not company_elem:
                company_elem = job_card.find('a', class_='hidden-nested-link')
            if company_elem:
                job_data['company_name'] = company_elem.get_text(strip=True)
            else:
                job_data['company_name'] = 'Unknown'
            
            # Extract location
            location_elem = job_card.find('span', class_='job-search-card__location')
            if location_elem:
                job_data['location'] = location_elem.get_text(strip=True)
            else:
                job_data['location'] = 'Unknown'
            
            # Extract LinkedIn URL
            link_elem = job_card.find('a', class_='base-card__full-link')
            if link_elem and link_elem.get('href'):
                job_url = link_elem.get('href')
                # Clean URL (remove query parameters)
                job_url = job_url.split('?')[0]
                job_data['linkedin_url'] = job_url
            else:
                job_data['linkedin_url'] = f"https://www.linkedin.com/jobs/view/{job_id}"
            
            # Extract posted date
            time_elem = job_card.find('time')
            if time_elem and time_elem.get('datetime'):
                try:
                    job_data['posted_date'] = datetime.fromisoformat(time_elem.get('datetime').replace('Z', '+00:00'))
                except:
                    job_data['posted_date'] = None
            else:
                job_data['posted_date'] = None
            
            # Extract company logo
            logo_elem = job_card.find('img', class_='artdeco-entity-image')
            if logo_elem and logo_elem.get('data-delayed-url'):
                job_data['company_logo_url'] = logo_elem.get('data-delayed-url')
            elif logo_elem and logo_elem.get('src'):
                job_data['company_logo_url'] = logo_elem.get('src')
            else:
                job_data['company_logo_url'] = None
            
            # Extract job description snippet if available
            desc_elem = job_card.find('p', class_='base-search-card__snippet')
            if desc_elem:
                job_data['description'] = desc_elem.get_text(strip=True)
            else:
                job_data['description'] = None
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing job card: {str(e)}")
            return None
    
    def search_jobs(
        self,
        keyword: str,
        location: str,
        job_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        date_posted: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn
        
        Args:
            keyword: Job title or keyword
            location: Location to search
            job_types: List of job types (full_time, part_time, etc.)
            experience_levels: List of experience levels
            date_posted: Filter by posting date (any_time, past_24_hours, past_week, past_month)
            limit: Maximum number of results to return
            
        Returns:
            List of job dictionaries containing only 'job_id' and 'linkedin_url'
        """
        jobs = []
        seen_job_ids = set()  # Track job IDs to avoid duplicates
        start = 0
        
        try:
            while len(jobs) < limit:
                # Build search URL
                url = self.build_search_url(
                    keyword=keyword,
                    location=location,
                    job_types=job_types,
                    experience_levels=experience_levels,
                    date_posted=date_posted,
                    start=start
                )
                
                logger.info(f"Fetching jobs from: {url}")
                
                # Make request
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Parse HTML (use lxml for speed, fallback to html.parser if not available)
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards
                job_cards = soup.find_all('div', class_='base-card')
                if not job_cards:
                    # Try alternative class name
                    job_cards = soup.find_all('div', class_='job-search-card')
                
                if not job_cards:
                    logger.warning("No job cards found on page")
                    break
                
                jobs_found_on_page = 0
                
                # Parse each job card
                for job_card in job_cards:
                    if len(jobs) >= limit:
                        break
                    
                    job_data = self.parse_job_card(job_card)
                    if job_data:
                        # Check for duplicates
                        job_id = job_data.get('job_id')
                        if job_id and job_id not in seen_job_ids:
                            # Only return job_id and linkedin_url
                            jobs.append({
                                'job_id': job_id,
                                'linkedin_url': job_data.get('linkedin_url', f"https://www.linkedin.com/jobs/view/{job_id}")
                            })
                            seen_job_ids.add(job_id)
                            jobs_found_on_page += 1
                        elif job_id:
                            logger.debug(f"Skipping duplicate job: {job_id}")
                
                # Check if we got any new jobs on this page
                if jobs_found_on_page == 0 or len(jobs) >= limit:
                    logger.info(f"No new jobs found on page or limit reached. Total unique jobs: {len(jobs)}")
                    break
                
                # Move to next page
                start += 25
                
                # Be respectful with rate limiting
                time.sleep(1)
            
            logger.info(f"Successfully fetched {len(jobs)} jobs")
            return jobs[:limit]
            
        except requests.RequestException as e:
            logger.error(f"Error fetching jobs from LinkedIn: {str(e)}")
            raise Exception(f"Failed to fetch jobs from LinkedIn: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in job search: {str(e)}")
            raise Exception(f"Failed to search jobs: {str(e)}")
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific job
        
        Args:
            job_id: LinkedIn job ID
            
        Returns:
            Job details dictionary
        """
        try:
            url = f"https://www.linkedin.com/jobs/view/{job_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML (use lxml for speed, fallback to html.parser if not available)
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except:
                soup = BeautifulSoup(response.content, 'html.parser')
            
            job_details = {
                'job_id': job_id,
                'linkedin_url': url,
            }
            
            # Extract job title
            title_elem = soup.find('h1', class_='top-card-layout__title')
            if not title_elem:
                title_elem = soup.find('h1', class_='topcard__title')
            if title_elem:
                job_details['title'] = title_elem.get_text(strip=True)
            
            # Extract company name
            company_elem = soup.find('a', class_='topcard__org-name-link')
            if not company_elem:
                company_elem = soup.find('span', class_='topcard__flavor')
            if company_elem:
                job_details['company_name'] = company_elem.get_text(strip=True)
            
            # Extract location
            location_elem = soup.find('span', class_='topcard__flavor--bullet')
            if not location_elem:
                # Try alternative location selectors
                location_elem = soup.find('span', class_='topcard-layout__bullet')
            if location_elem:
                job_details['location'] = location_elem.get_text(strip=True)
            
            # Extract posted date
            # Look for time element in the top card area
            posted_date = None
            time_elem = soup.find('time')
            if not time_elem:
                # Try finding in top card layout
                top_card = soup.find('div', class_='top-card-layout')
                if top_card:
                    time_elem = top_card.find('time')
            
            if time_elem and time_elem.get('datetime'):
                try:
                    datetime_str = time_elem.get('datetime')
                    # Handle different datetime formats
                    if 'Z' in datetime_str:
                        posted_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    else:
                        posted_date = datetime.fromisoformat(datetime_str)
                except Exception as e:
                    logger.debug(f"Could not parse datetime '{time_elem.get('datetime')}': {e}")
            
            # If still no date, try to find relative date text and parse it
            if not posted_date:
                # Look for text patterns like "4 days ago", "2 weeks ago", etc.
                date_pattern = re.compile(r'(\d+)\s+(day|days|hour|hours|week|weeks|month|months)\s+ago', re.I)
                for elem in soup.find_all(['span', 'div', 'p', 'time']):
                    text = elem.get_text(strip=True)
                    match = date_pattern.search(text)
                    if match:
                        # Calculate approximate date (for relative dates)
                        # This is approximate - in production you might want more sophisticated parsing
                        value = int(match.group(1))
                        unit = match.group(2).lower()
                        
                        if 'day' in unit:
                            posted_date = datetime.now() - timedelta(days=value)
                        elif 'hour' in unit:
                            posted_date = datetime.now() - timedelta(hours=value)
                        elif 'week' in unit:
                            posted_date = datetime.now() - timedelta(weeks=value)
                        elif 'month' in unit:
                            posted_date = datetime.now() - timedelta(days=value * 30)  # Approximate
                        break
            
            job_details['posted_date'] = posted_date
            if posted_date:
                logger.debug(f"Extracted posted_date for job {job_id}: {posted_date}")
            else:
                logger.debug(f"Could not extract posted_date for job {job_id}")
            
            # Extract full job description
            desc_elem = soup.find('div', class_='show-more-less-html__markup')
            if not desc_elem:
                desc_elem = soup.find('div', class_='description__text')
            if desc_elem:
                # Preserve line breaks and spacing for better readability
                job_details['description'] = desc_elem.get_text(separator='\n', strip=False).strip()
            
            # Extract employment type and seniority level
            criteria_items = soup.find_all('li', class_='description__job-criteria-item')
            for item in criteria_items:
                header = item.find('h3', class_='description__job-criteria-subheader')
                if header:
                    header_text = header.get_text(strip=True)
                    value = item.find('span', class_='description__job-criteria-text')
                    
                    if value:
                        value_text = value.get_text(strip=True)
                        
                        if 'Employment type' in header_text or 'Job type' in header_text:
                            # Normalize employment type
                            employment_type = value_text.lower().replace(' ', '_').replace('-', '_')
                            job_details['employment_type'] = employment_type
                        
                        elif 'Seniority level' in header_text or 'Experience' in header_text:
                            # Normalize experience level
                            experience_level = value_text.lower().replace(' ', '_').replace('-', '_')
                            job_details['experience_level'] = experience_level
            
            # Extract applicants count
            applicants_elem = soup.find('span', class_='num-applicants__caption')
            if not applicants_elem:
                applicants_elem = soup.find('figcaption', class_='num-applicants__caption')
            if applicants_elem:
                applicants_text = applicants_elem.get_text(strip=True)
                # Extract number from text like "50 applicants" or "Be among the first 25 applicants"
                applicants_match = re.search(r'(\d+)', applicants_text)
                if applicants_match:
                    job_details['applicants_count'] = int(applicants_match.group(1))
            
            # Extract company logo
            # Try multiple selectors for company logo
            logo_elem = soup.find('img', class_='artdeco-entity-image')
            if not logo_elem:
                # Try finding in top card layout entity image container
                top_card_entity = soup.find('div', class_='top-card-layout__entity-image')
                if top_card_entity:
                    logo_elem = top_card_entity.find('img')
            if not logo_elem:
                # Try alternative class names
                logo_elem = soup.find('img', {'class': re.compile(r'.*logo.*', re.I)})
            if not logo_elem:
                # Look in top card layout area
                top_card = soup.find('div', class_='top-card-layout')
                if top_card:
                    logo_elem = top_card.find('img', class_=re.compile(r'.*entity.*image.*', re.I))
            if not logo_elem:
                # Try finding company logo near company name
                topcard_org = soup.find('a', class_='topcard__org-name-link')
                if topcard_org:
                    # Look for img in nearby elements
                    parent = topcard_org.find_parent()
                    if parent:
                        logo_elem = parent.find('img')
                        if not logo_elem:
                            # Try finding in siblings
                            for sibling in parent.find_next_siblings():
                                logo_elem = sibling.find('img')
                                if logo_elem:
                                    break
            
            if logo_elem:
                # Try src first, then data-delayed-url, then data-src, then data-original-url
                logo_url = (logo_elem.get('src') or 
                           logo_elem.get('data-delayed-url') or 
                           logo_elem.get('data-src') or
                           logo_elem.get('data-original-url'))
                if logo_url:
                    job_details['company_logo_url'] = logo_url
                    logger.debug(f"Found company logo URL for job {job_id}: {logo_url}")
                else:
                    logger.debug(f"Found logo element for job {job_id} but no valid URL attribute")
            else:
                logger.debug(f"Could not find company logo element for job {job_id}")
            
            logger.info(f"Successfully extracted details for job {job_id}")
            return job_details
            
        except Exception as e:
            logger.error(f"Error fetching job details for {job_id}: {str(e)}")
            return None

