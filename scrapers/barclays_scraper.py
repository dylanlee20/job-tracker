from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class BarclaysScraper(BaseScraper):
    """Barclays scraper - Intern positions in US, Singapore, and Canada"""

    def __init__(self):
        super().__init__(
            company_name='Barclays',
            source_url='https://search.jobs.barclays/search-jobs'
        )

    def scrape_jobs(self):
        """Scrape Barclays job listings with filters for Intern positions"""
        all_jobs = []

        try:
            self.logger.info(f"Loading {self.source_url}")
            self.driver.get(self.source_url)
            time.sleep(10)

            # Dismiss cookie banner if present
            try:
                cookie_buttons = self.driver.find_elements(By.CSS_SELECTOR, '[id*="cookie"] button, [class*="cookie"] button, .onetrust-close-btn-handler')
                for btn in cookie_buttons:
                    try:
                        btn.click()
                        self.logger.info("Cookie banner dismissed")
                        time.sleep(2)
                        break
                    except:
                        continue
            except Exception as e:
                self.logger.info(f"No cookie banner or already dismissed: {e}")

            # Apply Country filter: United States
            self.logger.info("Applying country filters...")
            try:
                # Click on Country filter toggle
                country_toggle = self.driver.find_element(By.ID, 'country-toggle')
                self.driver.execute_script("arguments[0].scrollIntoView(true);", country_toggle)
                time.sleep(1)
                country_toggle.click()
                time.sleep(2)

                # Try to find and click United States checkbox
                # The ID pattern is typically country-filter-{id}
                country_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[id^="country-filter-"]')
                for checkbox in country_checkboxes:
                    try:
                        label = checkbox.find_element(By.XPATH, './following-sibling::label | ../label')
                        label_text = label.text.lower()
                        if 'united states' in label_text or 'usa' in label_text:
                            if not checkbox.is_selected():
                                checkbox.click()
                                self.logger.info("Selected United States")
                                time.sleep(2)
                            break
                    except:
                        continue

                # Try to find and click Singapore checkbox
                for checkbox in country_checkboxes:
                    try:
                        label = checkbox.find_element(By.XPATH, './following-sibling::label | ../label')
                        label_text = label.text.lower()
                        if 'singapore' in label_text:
                            if not checkbox.is_selected():
                                checkbox.click()
                                self.logger.info("Selected Singapore")
                                time.sleep(2)
                            break
                    except:
                        continue

                # Try to find and click Canada checkbox
                for checkbox in country_checkboxes:
                    try:
                        label = checkbox.find_element(By.XPATH, './following-sibling::label | ../label')
                        label_text = label.text.lower()
                        if 'canada' in label_text:
                            if not checkbox.is_selected():
                                checkbox.click()
                                self.logger.info("Selected Canada")
                                time.sleep(2)
                            break
                    except:
                        continue

                time.sleep(3)
                self.logger.info("Country filters applied")

            except Exception as e:
                self.logger.warning(f"Could not apply country filters: {e}")

            # Apply Job Type filter: Intern
            self.logger.info("Applying job type filter for Intern...")
            try:
                # Look for job type/level filter toggle
                job_type_selectors = [
                    'job-type-toggle',
                    'jobtype-toggle',
                    'custom_fields.jobtype-toggle',
                    'custom_fields.employmenttype-toggle',
                    'employment-type-toggle'
                ]

                job_type_toggle = None
                for selector_id in job_type_selectors:
                    try:
                        job_type_toggle = self.driver.find_element(By.ID, selector_id)
                        break
                    except:
                        continue

                if job_type_toggle:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", job_type_toggle)
                    time.sleep(1)
                    job_type_toggle.click()
                    time.sleep(2)

                    # Find and click Intern checkbox
                    job_type_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[id*="jobtype-filter"], input[id*="employment"]')
                    for checkbox in job_type_checkboxes:
                        try:
                            label = checkbox.find_element(By.XPATH, './following-sibling::label | ../label')
                            label_text = label.text.lower()
                            if 'intern' in label_text:
                                if not checkbox.is_selected():
                                    checkbox.click()
                                    self.logger.info("Selected Intern job type")
                                    time.sleep(3)
                                break
                        except:
                            continue

                self.logger.info("Job type filter applied")

            except Exception as e:
                self.logger.warning(f"Could not apply job type filter: {e}")

            time.sleep(5)

            # Get total pages
            try:
                search_results_section = self.driver.find_element(By.ID, 'search-results')
                total_pages = int(search_results_section.get_attribute('data-total-pages') or '1')
                total_results = int(search_results_section.get_attribute('data-total-results') or '0')
                self.logger.info(f"Total results: {total_results} across {total_pages} pages")
            except Exception as e:
                self.logger.warning(f"Could not get total pages: {e}, assuming 1 page")
                total_pages = 1

            # Scrape all pages
            current_page = 1
            max_pages = min(total_pages, 50)  # Safety limit

            while current_page <= max_pages:
                self.logger.info(f"Scraping page {current_page}/{max_pages}...")
                time.sleep(3)

                # Get job cards on current page
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, 'li[data-job-id], .job-tile, .search-results-item')

                if not job_cards:
                    # Alternative selectors
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, 'section.search-results li')

                self.logger.info(f"Found {len(job_cards)} job cards on page {current_page}")

                for idx, job_card in enumerate(job_cards):
                    try:
                        # Extract job link and title
                        try:
                            link_elem = job_card.find_element(By.CSS_SELECTOR, 'a[href*="/job/"]')
                            job_url = link_elem.get_attribute('href')
                            title = link_elem.text.strip()

                            if not title:
                                title = job_card.find_element(By.CSS_SELECTOR, 'h2, h3, .job-title').text.strip()

                            if not job_url.startswith('http'):
                                job_url = f"https://search.jobs.barclays{job_url}"
                        except Exception as e:
                            self.logger.warning(f"Could not extract link/title for job {idx + 1}: {e}")
                            continue

                        # Extract location
                        try:
                            location = job_card.find_element(By.CSS_SELECTOR, '.job-location, .location, [class*="location"]').text.strip()
                        except:
                            location = ""

                        # Extract date if available
                        try:
                            date_elem = job_card.find_element(By.CSS_SELECTOR, '.job-date, [class*="date"]')
                            post_date = date_elem.text.strip()
                        except:
                            post_date = None

                        job = {
                            'company': self.company_name,
                            'title': title,
                            'location': location,
                            'description': 'Intern position - US/Singapore/Canada',
                            'post_date': post_date,
                            'deadline': None,
                            'source_website': self.source_url,
                            'job_url': job_url
                        }

                        all_jobs.append(job)
                        self.logger.info(f"Page {current_page}, Job {idx + 1}: {title[:50]}...")

                    except Exception as e:
                        self.logger.warning(f"Error scraping job {idx + 1} on page {current_page}: {e}")
                        continue

                # Go to next page
                if current_page < max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 'a.next, button.next, [aria-label="Next"]')
                        if next_button.is_enabled() and next_button.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(1)
                            next_button.click()
                            self.logger.info(f"Navigating to page {current_page + 1}")
                            time.sleep(5)
                        else:
                            self.logger.info(f"Next button not available, stopping at page {current_page}")
                            break
                    except Exception as e:
                        self.logger.warning(f"Could not navigate to next page: {e}")
                        break

                current_page += 1

            self.logger.info(f"Completed scraping {len(all_jobs)} Barclays jobs")

        except Exception as e:
            self.logger.error(f"Error scraping Barclays jobs: {e}")
            import traceback
            traceback.print_exc()

        return all_jobs
