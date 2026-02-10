from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')

# Get chromedriver path
driver_path = ChromeDriverManager().install()
if 'THIRD_PARTY_NOTICES' in driver_path or not os.path.exists(driver_path):
    cache_base = os.path.expanduser('~/.wdm/drivers/chromedriver/mac64')
    for root, dirs, files in os.walk(cache_base):
        if 'chromedriver' in files:
            potential_path = os.path.join(root, 'chromedriver')
            try:
                os.chmod(potential_path, 0o755)
                if os.path.getsize(potential_path) > 1000000:
                    driver_path = potential_path
                    break
            except:
                continue

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = 'https://www.morganstanley.com/careers/career-opportunities-search?opportunity=sg#'
    print(f"Loading: {url}")
    driver.get(url)

    print("Waiting 20 seconds for page to load...")
    time.sleep(20)

    # Look for Load More button
    print("\n=== Looking for Load More/Pagination ===")
    load_more_selectors = [
        'button[class*="load"]',
        'button[class*="more"]',
        'a[class*="load"]',
        'a[class*="more"]',
        'button[class*="show"]',
        'div[class*="pagination"]',
        'button[class*="next"]',
        'a[class*="next"]'
    ]

    for selector in load_more_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\nFound {len(elements)} elements with selector: {selector}")
                for elem in elements:
                    print(f"  - Text: '{elem.text}', Tag: {elem.tag_name}, Classes: {elem.get_attribute('class')}")
        except:
            pass

    # Check job count display
    print("\n=== Looking for Job Count Display ===")
    count_selectors = [
        'div[class*="result"]',
        'span[class*="result"]',
        'div[class*="count"]',
        'span[class*="count"]',
        'div[class*="total"]'
    ]

    for selector in count_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                for elem in elements[:5]:  # Show first 5
                    text = elem.text.strip()
                    if text and ('result' in text.lower() or 'job' in text.lower() or any(c.isdigit() for c in text)):
                        print(f"  - {text} (selector: {selector})")
        except:
            pass

    # Count job cards
    print("\n=== Job Cards ===")
    job_cards = driver.find_elements(By.CSS_SELECTOR, 'div.jobcard div.cmp-jobcard')
    print(f"Total job cards found: {len(job_cards)}")

    # Check if page has scrollable container
    print("\n=== Checking for scrollable containers ===")
    try:
        containers = driver.find_elements(By.CSS_SELECTOR, 'div[class*="list"]')
        for container in containers[:3]:
            height = driver.execute_script("return arguments[0].scrollHeight", container)
            visible_height = driver.execute_script("return arguments[0].clientHeight", container)
            if height > visible_height:
                print(f"Found scrollable container: height={height}, visible={visible_height}")
                print(f"  Classes: {container.get_attribute('class')}")
    except:
        pass

finally:
    driver.quit()
    print("\nBrowser closed")
