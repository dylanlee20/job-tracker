"""
Utility functions for job processing
"""

import re


def normalize_location(location):
    """
    Normalize location names to "Country, City" format

    Args:
        location: Raw location string

    Returns:
        Normalized location string in "Country, City" format
    """
    if not location:
        return "Unknown"

    location = location.strip().rstrip('. ')

    # Helper function to title case city names properly
    def title_case_city(city):
        """Convert city names to proper title case"""
        city = city.strip()
        # Special cases for acronyms and abbreviations
        special_cases = {
            'NYC': 'New York',
            'SF': 'San Francisco',
            'LA': 'Los Angeles'
        }
        if city in special_cases:
            return special_cases[city]
        # Title case with proper handling of 'and', 'of', etc.
        return city.title()

    # Direct mapping for common variations to "Country, City" format
    location_map = {
        # Multiple locations patterns
        '2 Locations': 'Multiple Locations',
        '3 Locations': 'Multiple Locations',
        '4 Locations': 'Multiple Locations',
        '5 Locations': 'Multiple Locations',
        '6 Locations': 'Multiple Locations',
        'Multiple Locations': 'Multiple Locations',
        'Multiple US Locations': 'Multiple Locations',

        # New York variations
        'NEW YORK, NEW YORK, UNITED STATES': 'United States, New York',
        'New York, NY, United States': 'United States, New York',
        'New York, New York, United States': 'United States, New York',
        'New York·United States': 'United States, New York',
        'United States - New York': 'United States, New York',
        'New York, United States': 'United States, New York',
        'New York': 'United States, New York',
        'NY, New York': 'United States, New York',
        'NY (1271 AOA/6th Ave), New York': 'United States, New York',
        'NYC (1285)': 'United States, New York',

        # Other US cities
        'Chicago, IL, United States': 'United States, Chicago',
        'Chicago, Illinois, United States': 'United States, Chicago',
        'Chicago·United States': 'United States, Chicago',
        'Chicago, United States': 'United States, Chicago',
        'Chicago': 'United States, Chicago',
        'IL, Chicago': 'United States, Chicago',

        'San Francisco, California, United States': 'United States, San Francisco',
        'San Francisco·United States': 'United States, San Francisco',
        'San Francisco, United States': 'United States, San Francisco',
        'San Francisco': 'United States, San Francisco',
        'San Francisco (Greenhill)': 'United States, San Francisco',
        'CA, San Francisco': 'United States, San Francisco',

        'Dallas, Texas, United States': 'United States, Dallas',
        'Dallas·United States': 'United States, Dallas',
        'Dallas, United States': 'United States, Dallas',
        'Dallas': 'United States, Dallas',

        'Houston, Texas, United States': 'United States, Houston',
        'Houston·United States': 'United States, Houston',
        'Houston, United States': 'United States, Houston',
        'Houston': 'United States, Houston',
        'TX, Houston': 'United States, Houston',
        'TX-Main Street, Houston 4': 'United States, Houston',

        'Salt Lake City·United States': 'United States, Salt Lake City',
        'Salt Lake City, United States': 'United States, Salt Lake City',
        'Salt Lake City': 'United States, Salt Lake City',

        'MIAMI, FLORIDA, UNITED STATES': 'United States, Miami',
        'Miami, United States': 'United States, Miami',
        'Miami': 'United States, Miami',

        'JERSEY CITY, NEW JERSEY, UNITED STATES': 'United States, Jersey City',
        'Jersey City, NJ, United States': 'United States, Jersey City',
        'Jersey City, United States': 'United States, Jersey City',
        'Jersey City': 'United States, Jersey City',

        'Atlanta, GA, United States': 'United States, Atlanta',
        'Atlanta, United States': 'United States, Atlanta',
        'Atlanta': 'United States, Atlanta',

        'BOSTON, MASSACHUSETTS, UNITED STATES': 'United States, Boston',
        'Boston, United States': 'United States, Boston',
        'Boston': 'United States, Boston',

        'Los Angeles, United States': 'United States, Los Angeles',
        'Los Angeles': 'United States, Los Angeles',
        'Philadelphia, United States': 'United States, Philadelphia',
        'Philadelphia': 'United States, Philadelphia',
        'Seattle, United States': 'United States, Seattle',
        'Seattle': 'United States, Seattle',
        'Denver, United States': 'United States, Denver',
        'Denver': 'United States, Denver',
        'CO, Denver': 'United States, Denver',
        'Phoenix, United States': 'United States, Phoenix',
        'Phoenix': 'United States, Phoenix',
        'Detroit, United States': 'United States, Detroit',
        'Detroit': 'United States, Detroit',
        'Tampa, United States': 'United States, Tampa',
        'Tampa': 'United States, Tampa',
        'Columbus, United States': 'United States, Columbus',
        'Columbus': 'United States, Columbus',
        'Jacksonville, United States': 'United States, Jacksonville',
        'Jacksonville': 'United States, Jacksonville',
        'Las Vegas, United States': 'United States, Las Vegas',
        'Las Vegas': 'United States, Las Vegas',
        'Kansas City, United States': 'United States, Kansas City',
        'KS, Kansas City': 'United States, Kansas City',
        'Minneapolis, United States': 'United States, Minneapolis',
        'MN - HQ, Minneapolis': 'United States, Minneapolis',

        # US States (map to just country)
        'California': 'United States',
        'Ohio': 'United States',

        # Cambridge - could be US or UK, default to US
        'Cambridge': 'United States, Cambridge',

        # Hong Kong variations
        'Hong Kong SAR': 'China, Hong Kong',
        'Hong Kong SAR ': 'China, Hong Kong',
        'Hong Kong, China': 'China, Hong Kong',
        'Hong Kong': 'China, Hong Kong',
        'Hong Kong, Hong Kong Island': 'China, Hong Kong',
        'Hong Kong, Kowloon': 'China, Hong Kong',
        'Central and Western, Hong Kong Island, Hong Kong': 'China, Hong Kong',
        'Kwun Tong, Kowloon, Hong Kong': 'China, Hong Kong',
        'Singapore, Singapore': 'Singapore',

        # Mainland China
        'Shanghai': 'China, Shanghai',
        'Beijing': 'China, Beijing',
        'Shenzhen': 'China, Shenzhen',
        'Guangzhou': 'China, Guangzhou',
        'Xian': 'China, Xian',
        'Mainland China': 'China',
        'Mainland China, China': 'China',
        'China': 'China',

        # Singapore
        'Singapore': 'Singapore',

        # UK
        'London': 'United Kingdom, London',
        'London, United Kingdom': 'United Kingdom, London',
        'Birmingham': 'United Kingdom, Birmingham',
        'Birmingham, United Kingdom': 'United Kingdom, Birmingham',
        'Glasgow, United Kingdom': 'United Kingdom, Glasgow',

        # Canada
        'Canada, Calgary': 'Canada, Calgary',
        'Canada, CALGARY': 'Canada, Calgary',
        'Canada, Toronto': 'Canada, Toronto',
        'Canada, Montreal': 'Canada, Montreal',

        # Australia
        'Sydney': 'Australia, Sydney',
        'Sydney, Australia': 'Australia, Sydney',
        'Sydney, NSW, Australia': 'Australia, Sydney',
        'Melbourne': 'Australia, Melbourne',
        'Melbourne, Australia': 'Australia, Melbourne',
        'Australia': 'Australia',

        # New Zealand
        'Auckland': 'New Zealand, Auckland',
        'Auckland, New Zealand': 'New Zealand, Auckland',
        'New Zealand': 'New Zealand',

        # Japan
        'Tokyo': 'Japan, Tokyo',
        'Japan, Tokyo': 'Japan, Tokyo',
        'Japan, Minato-Ku': 'Japan, Tokyo',
        'Japan': 'Japan',

        # South Korea
        'Seoul': 'South Korea, Seoul',
        'Republic of, Seoul·Korea': 'South Korea, Seoul',

        # Middle East
        'Dubai': 'UAE, Dubai',
        'United Arab Emirates, Dubai': 'UAE, Dubai',
        'United Arab Emirates': 'UAE',

        # Europe
        'Zürich': 'Switzerland, Zürich',
        'Switzerland - Zürich': 'Switzerland, Zürich',
        'Switzerland - Western Switzerland': 'Switzerland, Geneva',
        'Switzerland, Switzerland': 'Switzerland',
        'Switzerland': 'Switzerland',

        'Paris': 'France, Paris',
        'France, Paris': 'France, Paris',

        'Frankfurt': 'Germany, Frankfurt',
        'Germany, Frankfurt': 'Germany, Frankfurt',
        'Munich': 'Germany, Munich',
        'Germany, Munich': 'Germany, Munich',
        'Germany': 'Germany',

        'Milan': 'Italy, Milan',
        'Italy, Milan': 'Italy, Milan',
        'Italy': 'Italy',

        'Budapest': 'Hungary, Budapest',
        'Hungary, Budapest': 'Hungary, Budapest',

        'Madrid': 'Spain, Madrid',
        'Spain, Madrid': 'Spain, Madrid',

        'Tel Aviv': 'Israel, Tel Aviv',
        'Israel, Tel Aviv': 'Israel, Tel Aviv',

        'Sao Paulo': 'Brazil, Sao Paulo',
        'Brazil, Sao Paulo': 'Brazil, Sao Paulo',

        # Generic
        'United States': 'United States',
        'United States of America': 'United States',
        'USA': 'United States',
        'Unknown': 'Unknown',
    }

    # Check exact match first
    if location in location_map:
        return location_map[location]

    # Pattern-based normalization for "City, State, United States" or "CITY, STATE, UNITED STATES"
    us_pattern = r'^([^,]+),\s+(?:[A-Z]{2}|[A-Za-z\s]+),\s+United States(?:\s+of\s+America)?$'
    match = re.match(us_pattern, location, re.IGNORECASE)
    if match:
        city = title_case_city(match.group(1))
        return f"United States, {city}"

    # Pattern for "United States of America, City" with possible ALL CAPS
    usa_pattern = r'^United States(?: of America)?,\s+(.+)$'
    match = re.match(usa_pattern, location, re.IGNORECASE)
    if match:
        city = title_case_city(match.group(1))
        return f"United States, {city}"

    # Pattern for "City·United States" → "United States, City"
    if '·United States' in location:
        city = location.replace('·United States', '').strip()
        city = title_case_city(city)
        return f"United States, {city}"

    # Pattern for "United States - City/State" → "United States, City"
    if location.startswith('United States - '):
        place = location.replace('United States - ', '').strip()
        return f"United States, {place}"

    # Pattern for "Country, City" where city might be ALL CAPS
    if ', ' in location:
        parts = [p.strip() for p in location.split(',')]

        # Handle multiple commas - take first (should be country or city) and last (should be city or country)
        if len(parts) > 2:
            # For "City, State/Region, Country" patterns, use first and last
            country = parts[-1]
            city = parts[0]
        elif len(parts) == 2:
            # Check if it's already "Country, City" format
            first_part = parts[0]
            second_part = parts[1]

            # List of known countries
            known_countries = [
                'United States', 'United States of America', 'China', 'Japan', 'Singapore',
                'United Kingdom', 'Australia', 'New Zealand', 'UAE', 'Switzerland',
                'South Korea', 'Canada', 'France', 'Germany', 'Italy', 'Spain',
                'Hungary', 'Israel', 'Brazil', 'Hong Kong'
            ]

            if first_part in known_countries:
                # Already in "Country, City" format
                country = first_part
                city = second_part
            elif second_part in known_countries:
                # In "City, Country" format, need to flip
                country = second_part
                city = first_part
            else:
                # Assume second part is country
                country = second_part
                city = first_part
        else:
            return location_map.get(location, location)

        # Normalize country name
        if country.lower() == 'united states of america':
            country = 'United States'

        # Title case the city if it's ALL CAPS
        city = title_case_city(city)

        return f"{country}, {city}"

    # Pattern for "City·Country" → "Country, City"
    if '·' in location:
        parts = location.split('·')
        if len(parts) == 2:
            city = title_case_city(parts[0].strip())
            country = parts[1].strip()
            return f"{country}, {city}"

    # Default: Return as-is if no rule applies
    return location


def categorize_job(title, description=''):
    """
    Categorize job based on title and description

    Args:
        title: Job title
        description: Job description (optional)

    Returns:
        Category string: 'Investment Banking', 'Sales & Trading', 'Structuring',
                        'Quant', 'Research', 'Technology', 'Risk Management',
                        'Operations', 'Compliance', 'Finance & Accounting', 'Other'
    """
    if not title:
        return 'Other'

    title_lower = title.lower()
    desc_lower = description.lower() if description else ''
    combined = f"{title_lower} {desc_lower}"

    # Investment Banking keywords
    ib_keywords = [
        'investment banking', 'ibd', 'ib ', ' ib,', 'mergers', 'acquisitions',
        'm&a', 'coverage', 'corporate finance', 'leveraged finance',
        'private equity', 'pe ', 'growth equity', 'venture capital',
        'real estate banking', 'infrastructure finance', 'energy banking',
        'natural resources', 'healthcare banking', 'financial institutions group',
        'fig', 'technology banking', 'tmt banking', 'industrials banking',
        'consumer retail banking', 'capital markets', 'ecm', 'dcm',
        'equity capital markets', 'debt capital markets', 'origination',
        'underwriting', 'syndicate'
    ]

    # Sales & Trading keywords
    st_keywords = [
        'sales & trading', 's&t', 'sales and trading', 'trading', 'trader',
        'equities sales', 'equity sales', 'fixed income sales', 'ficc sales',
        'equity trading', 'fixed income trading', 'ficc trading',
        'commodities trading', 'foreign exchange', 'fx trading', 'fx sales',
        'forex', 'macro trading', 'credit trading', 'rates trading',
        'currencies', 'electronic trading', 'market making', 'flow trading',
        'derivatives trading', 'options trading', 'futures trading',
        'voice trading', 'desk strategist', 'execution services'
    ]

    # Structuring keywords (check before S&T as it's more specific)
    structuring_keywords = [
        'structuring', 'structured products', 'structured finance',
        'securitization', 'abs', 'mbs', 'cdo', 'clo', 'cmbs',
        'exotic derivatives', 'structured credit', 'structured solutions',
        'product structuring', 'structurer'
    ]

    # Quant keywords
    quant_keywords = [
        'quant', 'quantitative', 'quantitative research', 'quantitative trading',
        'quantitative analytics', 'quantitative strategies', 'quantitative modeling',
        'quantitative developer', 'quantitative analyst', 'strat', 'strategist',
        'model validation', 'pricing model', 'algo trading', 'algorithmic trading'
    ]

    # Research keywords
    research_keywords = [
        'research', 'equity research', 'credit research', 'fixed income research',
        'research analyst', 'research associate', 'sector coverage', 'sector analyst',
        'industry coverage', 'fundamental research', 'macro research',
        'economic research', 'strategy research'
    ]

    # Technology keywords
    tech_keywords = [
        'technology', 'software', 'developer', 'engineer', 'engineering',
        'data science', 'data scientist', 'machine learning', 'ai engineer',
        'artificial intelligence', 'cloud', 'devops', 'platform engineer',
        'infrastructure engineer', 'cybersecurity', 'information security',
        'it analyst', 'systems analyst', 'application', 'technical analyst',
        'business analyst', 'data analyst', 'data engineer', 'full stack',
        'front end', 'backend', 'database', 'network'
    ]

    # Risk Management keywords
    risk_keywords = [
        'risk management', 'market risk', 'credit risk', 'operational risk',
        'risk analyst', 'risk associate', 'risk control', 'risk modeling',
        'enterprise risk', 'financial risk', 'regulatory risk', 'compliance risk',
        'fraud risk', 'liquidity risk', 'counterparty risk', 'var', 'value at risk'
    ]

    # Operations keywords
    ops_keywords = [
        'operations', 'operations analyst', 'operations associate', 'trade support',
        'settlement', 'clearing', 'reconciliation', 'middle office', 'back office',
        'transaction processing', 'client services', 'service delivery',
        'processing', 'cash management', 'collateral management', 'securities services'
    ]

    # Compliance & Legal keywords
    compliance_keywords = [
        'compliance', 'regulatory', 'legal', 'attorney', 'counsel', 'aml',
        'anti-money laundering', 'kyc', 'know your customer', 'regulatory affairs',
        'governance', 'audit', 'internal audit', 'compliance officer',
        'regulatory reporting', 'control', 'surveillance', 'financial crimes'
    ]

    # Finance & Accounting keywords
    finance_keywords = [
        'finance', 'accounting', 'financial reporting', 'controller',
        'treasury', 'fp&a', 'financial planning', 'budgeting', 'forecasting',
        'financial analysis', 'cost accounting', 'tax', 'accounts payable',
        'accounts receivable', 'general ledger', 'financial control'
    ]

    # Check categories in order of specificity (most specific first)
    if any(keyword in combined for keyword in quant_keywords):
        return 'Quant'

    if any(keyword in combined for keyword in structuring_keywords):
        return 'Structuring'

    if any(keyword in combined for keyword in risk_keywords):
        return 'Risk Management'

    if any(keyword in combined for keyword in compliance_keywords):
        return 'Compliance'

    if any(keyword in combined for keyword in st_keywords):
        return 'Sales & Trading'

    if any(keyword in combined for keyword in research_keywords):
        return 'Research'

    if any(keyword in combined for keyword in ib_keywords):
        return 'Investment Banking'

    if any(keyword in combined for keyword in tech_keywords):
        return 'Technology'

    if any(keyword in combined for keyword in ops_keywords):
        return 'Operations'

    if any(keyword in combined for keyword in finance_keywords):
        return 'Finance & Accounting'

    # Default category
    return 'Other'


def get_location_display_name(location):
    """
    Get a clean display name for a location

    Args:
        location: Normalized location string

    Returns:
        Display-friendly location name
    """
    # Already normalized, just return as-is
    return location


def get_category_color(category):
    """
    Get a color code for each job category

    Args:
        category: Category string

    Returns:
        Hex color code
    """
    color_map = {
        'Investment Banking': '#1e40af',      # Blue
        'Sales & Trading': '#16a34a',         # Green
        'Structuring': '#9333ea',             # Purple
        'Quant': '#dc2626',                   # Red
        'Research': '#ea580c',                # Orange
        'Technology': '#0891b2',              # Cyan
        'Risk Management': '#f59e0b',         # Amber
        'Operations': '#8b5cf6',              # Violet
        'Compliance': '#ec4899',              # Pink
        'Finance & Accounting': '#14b8a6',    # Teal
        'Other': '#6b7280'                    # Gray
    }
    return color_map.get(category, '#6b7280')
