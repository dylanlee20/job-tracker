# Citi Careers Website Information

## Website Details
- **URL**: https://jobs.citi.com/search-jobs
- **Type**: Single Page Application (SPA) - URL doesn't change with filters/pagination
- **Jobs per page**: 30
- **Total pages**: 169 pages (~5,000 jobs)

## Key Findings

### Job Elements
- **Selector**: `[data-job-id]` (30 per page)
- **Job ID format**: `data-job-id="90104324896"`
- **Job URL format**: `/job/{city}/{title}/287/{job-id}`

### Pagination
- Uses "Next" button to navigate pages
- Selector: `a[class*="next"]`
- No lazy loading - must click Next button
- **Important**: 169 pages × 30 seconds/page = **85+ minutes** to scrape all

### Location Format
- Example: "Jersey City, New Jersey, United States"
- Example: "Irving, Texas, United States"
- Example: "Getzville, New York, United States"

## Recommended Approach

### Option 1: Filter by US Locations (Recommended)
- Add location filter before scraping
- Use checkboxes or search to filter by US states
- This would reduce from 169 pages to manageable number

### Option 2: Filter by Department/Division
- Add department/division filters
- Focus on specific areas (e.g., Investment Banking, Markets)
- Combine with location filter

### Option 3: Scrape All (Not Recommended)
- Would take 85+ minutes
- ~5,000 jobs (many not relevant)
- Database would be very large

## Implementation Notes

1. **Must use Selenium interactions** - cannot just change URL
2. **Need to click "Next" button** for each page
3. **Wait for page to reload** after each click (~3-5 seconds)
4. **Apply filters first** before starting pagination
5. **Consider rate limiting** to avoid being blocked

## Filters Available

The test found:
- **1,588 checkboxes** for various filters
- **Location filters** (countries, states, cities)
- **Department/division filters**
- **Job type filters**

## Next Steps

**Decide on filters:**
- Which locations? (US only? Specific states?)
- Which departments? (Investment Banking? Technology?)
- Other criteria?

Once filters are decided, I can implement:
1. Navigate to page
2. Apply selected filters
3. Wait for results to load
4. Scrape current page (30 jobs)
5. Click "Next" button
6. Repeat until no more pages or max limit reached
