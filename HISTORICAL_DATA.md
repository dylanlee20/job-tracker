# Historical Data Backfill - Using Wayback Machine

## The Problem

When you first start **NewWhale Job Tracker**, the initial snapshot shows all current jobs as "new" (e.g., "205 new jobs this week"). While technically accurate for the tracking system, this doesn't reflect actual market changes.

**Year-over-year comparisons require 52 weeks of data** - meaning you'd need to wait a full year to see trends like "Investment Banking roles are up 30% YoY."

## The Solution: Wayback Machine

The **Internet Archive's Wayback Machine** archives snapshots of websites over time. We can potentially retrieve historical job data from archived career pages to **immediately backfill months or even years of data**.

### How It Works

1. **Query Wayback Machine API** - Find available snapshots of career pages
2. **Retrieve Archived HTML** - Get the historical webpage content
3. **Extract Job Counts** - Parse HTML to estimate number of positions
4. **Create Historical Snapshots** - Populate database with backdated data

### Limitations

⚠️ **Important Caveats:**

- **JavaScript-rendered sites**: Most modern career sites load jobs via JavaScript/AJAX, which Wayback Machine doesn't execute. This means we often can't see the actual job listings.

- **Estimation, not precision**: Extracted job counts are *estimates* based on HTML parsing, not exact figures from live scraping.

- **Archive availability**: Not all sites are archived regularly. Some may have zero usable snapshots.

- **Data quality varies**: Older archives may have broken layouts or incomplete data.

## Usage

### 1. Check Availability (Quick Test)

First, check which companies have good Wayback Machine coverage:

```bash
python3 test_wayback_quick.py
```

**Expected Output:**
```
Company                   Snapshots       Likelihood      URL
--------------------------------------------------------------------------------
Goldman Sachs            12              High            https://higher.gs.com/...
JPMorgan                 0               Low             https://jpmc.fa.oracle...
Blackstone              5               Medium          https://blackstone.wd1...
...

Summary:
  High Likelihood:   2 companies - Good candidates for backfill
  Medium Likelihood: 3 companies - May have partial data
  Low Likelihood:    3 companies - Unlikely to have useful data
```

### 2. Test Single Company Backfill

Try backfilling one company first to see results:

```bash
python3 backfill_historical_data.py
```

Select option **2** (Backfill specific company), then choose a company with "High" likelihood.

**This will:**
- Search for up to 52 weeks of archived pages
- Attempt to extract job counts from each snapshot
- Show you the results before saving to database

**Example output:**
```
Backfilling Historical Data for Goldman Sachs
======================================================================
Fetching snapshot from 2025-01-20...
  ✓ Estimated 198 jobs on 2025-01-20
Fetching snapshot from 2025-01-13...
  ✗ Could not extract job count
Fetching snapshot from 2025-01-06...
  ✓ Estimated 205 jobs on 2025-01-06
...

✓ Successfully retrieved 42 historical data points
```

### 3. Full Backfill (All Companies)

If tests look promising, run full backfill:

```bash
python3 backfill_historical_data.py
```

Select option **3** (Full backfill).

⏱️ **Time estimate**: 1-2 hours (makes ~200-500 requests to Wayback Machine)

⚠️ **Warning**: Be respectful of Wayback Machine's resources. The script includes delays between requests.

## Expected Success Rates

Based on typical career site architectures:

| Site Type | Success Likelihood | Reason |
|-----------|-------------------|---------|
| **Static HTML** | High (80%+) | Job listings in HTML, easy to parse |
| **Server-rendered** | Medium (40-60%) | Some data in HTML, may be incomplete |
| **JavaScript/React** | Low (10-20%) | Jobs loaded via AJAX, not in archived HTML |
| **Workday/Oracle** | Very Low (<5%) | Heavy JavaScript, dynamic forms |

## Why It Might Not Work

Most finance career sites use **modern JavaScript frameworks** (React, Vue, Angular) that load job listings dynamically. Examples:

- **JPMorgan** (Oracle Cloud) - Jobs loaded via REST API calls
- **Blackstone** (Workday) - Entire page rendered client-side
- **Citi** - Dynamic filtering via JavaScript

Wayback Machine captures the initial HTML but **doesn't execute JavaScript**, so it misses the actual job data.

## Alternative: Manual Historical Data

If Wayback Machine backfill doesn't work, you can manually create historical snapshots if you have:

1. **Excel exports** from other job tracking tools
2. **Screenshots** with visible job counts
3. **Estimates** from memory/LinkedIn data

Contact the system admin for manual snapshot import scripts.

## Recommendation

### Best Approach:

1. ✅ **Run the quick test** (`test_wayback_quick.py`) - Takes 2 minutes
2. ✅ **Try one company backfill** - See if it works for your sites
3. ❓ **If successful**: Run full backfill to get historical data immediately
4. ❓ **If unsuccessful**: Continue with live tracking - you'll have valuable data in 3-6 months

### Reality Check:

Given that most target companies use **Workday, Oracle Cloud, or custom JavaScript apps**, the success rate will likely be **low to medium**. However:

- ✅ **Worth trying** - 30 minutes of testing could give you a year of data
- ✅ **No harm in testing** - Doesn't affect your live tracking
- ✅ **Learn for free** - Understand which sites are archivable

## Long-term Strategy

Even if Wayback Machine backfill fails, remember:

📈 **Your live data becomes more valuable over time**

- Week 4: See weekly trends
- Week 12: Identify quarterly patterns
- Week 26: Understand seasonal cycles
- Week 52: **Year-over-year comparisons unlock**
- Year 2+: Multi-year trends (your **competitive moat**)

**Nobody else is tracking this data systematically**. In 6-12 months, you'll have proprietary market intelligence that doesn't exist anywhere else - not on LinkedIn, not on Glassdoor, not in any recruiter's database.

That's your **long-term competitive advantage**.

---

## Technical Details

### Wayback Machine CDX API

```python
GET https://web.archive.org/cdx/search/cdx
Parameters:
  url: Target URL
  from: Start date (YYYYMMDD)
  to: End date (YYYYMMDD)
  output: json
  filter: statuscode:200
  collapse: timestamp:8  # One per day
```

### Snapshot Creation

Historical snapshots include:
- ✅ Date and week number
- ✅ Total estimated jobs
- ✅ Company breakdown
- ❌ Category breakdown (unknown from archives)
- ❌ Location breakdown (unknown from archives)
- ❌ New vs closed (can't calculate without continuous data)

---

**Questions?** Check the main README or examine the `services/wayback_service.py` implementation.
