# Update Remaining JPMorgan Scrapers with Infinite Scroll

## Status
- ✅ Hong Kong: Updated and tested (126 jobs)
- ⏳ US: Needs update
- ⏳ Australia: Needs update

## Next Steps
1. Update US scraper with infinite scroll
2. Update Australia scraper with infinite scroll
3. Test both scrapers
4. Restart Flask

## Infinite Scroll Logic
```python
# Load page once
self.driver.get(self.source_url)
time.sleep(5)

# Scroll to load all jobs
last_height = 0
scroll_attempts = 0
max_scroll_attempts = 15

while scroll_attempts < max_scroll_attempts:
    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    new_height = self.driver.execute_script("return document.body.scrollHeight")
    job_tiles = self.driver.find_elements(By.CSS_SELECTOR, 'div.job-tile')

    if new_height == last_height:
        break

    last_height = new_height
    scroll_attempts += 1

# Process all jobs after scrolling completes
```
