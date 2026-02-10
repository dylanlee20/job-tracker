"""
Utility functions for job processing
"""

import re


def normalize_location(location):
    """
    Normalize location names to avoid duplicates

    Args:
        location: Raw location string

    Returns:
        Normalized location string
    """
    if not location:
        return "Unknown"

    location = location.strip()

    # Location mapping for common variations
    location_map = {
        # New York variations
        'NEW YORK, NEW YORK, UNITED STATES': 'New York',
        'New York, NY, United States': 'New York',
        'New York, New York, United States': 'New York',
        'New York·United States': 'New York',
        'United States - New York': 'New York',

        # Chicago variations
        'Chicago, IL, United States': 'Chicago',
        'Chicago, Illinois, United States': 'Chicago',
        'Chicago·United States': 'Chicago',

        # San Francisco variations
        'San Francisco, California, United States': 'San Francisco',
        'San Francisco·United States': 'San Francisco',

        # Dallas variations
        'Dallas, Texas, United States': 'Dallas',
        'Dallas·United States': 'Dallas',

        # Houston variations
        'Houston, Texas, United States': 'Houston',
        'Houston·United States': 'Houston',

        # Salt Lake City variations
        'Salt Lake City·United States': 'Salt Lake City',

        # Miami variations
        'MIAMI, FLORIDA, UNITED STATES': 'Miami',

        # Jersey City variations
        'JERSEY CITY, NEW JERSEY, UNITED STATES': 'Jersey City',
        'Jersey City, NJ, United States': 'Jersey City',

        # Atlanta variations
        'Atlanta, GA, United States': 'Atlanta',

        # Columbus variations
        'Columbus, OH, United States': 'Columbus',

        # Jacksonville variations
        'Jacksonville, Florida, United States': 'Jacksonville',

        # Tampa variations
        'Tampa, Florida, United States': 'Tampa',

        # Hong Kong variations
        'Hong Kong SAR': 'Hong Kong',
        'Hong Kong SAR ': 'Hong Kong',

        # Switzerland variations
        'Switzerland - Western Switzerland': 'Switzerland',
        'Switzerland - Zürich': 'Switzerland',
        'Switzerland - Zürich ': 'Switzerland',

        # Multi-location entries
        '2 Locations': 'Multiple Locations',
        '3 Locations': 'Multiple Locations',
        'United States - California, United States - Illinois': 'Multiple US Locations',
        'United States - California, United States - Illinois, United States - New York': 'Multiple US Locations',
    }

    # Check if exact match exists in map
    if location in location_map:
        return location_map[location]

    # Pattern-based normalization
    # Remove trailing periods and spaces
    location = location.rstrip('. ')

    # Simplify "City, State, Country" to just "City"
    # Match patterns like "City, State, United States"
    us_pattern = r'^([^,]+),\s+[A-Z]{2},\s+United States$'
    match = re.match(us_pattern, location)
    if match:
        return match.group(1)

    # Match patterns like "City, State Name, United States"
    us_pattern2 = r'^([^,]+),\s+[A-Za-z\s]+,\s+United States$'
    match = re.match(us_pattern2, location)
    if match:
        return match.group(1)

    # Simplify "City·United States" to just "City"
    if '·United States' in location:
        return location.replace('·United States', '').strip()

    # Handle "United States - State" pattern
    if location.startswith('United States - '):
        state = location.replace('United States - ', '').strip()
        # Common state to city mapping for major financial centers
        state_map = {
            'California': 'California',
            'New York': 'New York',
            'Illinois': 'Chicago',
            'Texas': 'Texas',
        }
        return state_map.get(state, state)

    # If location is just "United States", keep it
    if location == 'United States':
        return 'United States'

    # Return as-is if no normalization rule applies
    return location


def categorize_job(title, description=''):
    """
    Categorize job based on title and description

    Args:
        title: Job title
        description: Job description (optional)

    Returns:
        Category string: 'Investment Banking', 'Sales & Trading',
                        'Structuring', 'Quant', 'Technology', 'Other'
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
        'real estate', 'infrastructure', 'energy', 'natural resources',
        'healthcare banking', 'financial institutions group', 'fig',
        'technology banking', 'tmt', 'industrials', 'consumer retail',
        'capital markets', 'ecm', 'dcm', 'equity capital markets',
        'debt capital markets', 'strategic partners', 'acquisitions'
    ]

    # Sales & Trading keywords
    st_keywords = [
        'sales', 'trading', 'trader', 'sales & trading', 's&t',
        'equities', 'equity', 'fixed income', 'ficc', 'commodities',
        'foreign exchange', 'fx', 'forex', 'macro', 'credit trading',
        'rates', 'currencies', 'electronic trading', 'market making',
        'flow trading', 'derivatives', 'options', 'futures'
    ]

    # Structuring keywords
    structuring_keywords = [
        'structuring', 'structured products', 'structured finance',
        'securitization', 'abs', 'mbs', 'cdo', 'clo',
        'exotic derivatives', 'structured credit', 'structured solutions'
    ]

    # Quant keywords
    quant_keywords = [
        'quant', 'quantitative', 'quantitative research', 'quantitative trading',
        'quantitative analytics', 'quantitative strategies', 'quantitative modeling',
        'risk analytics', 'model validation', 'strat', 'quantitative developer'
    ]

    # Technology keywords
    tech_keywords = [
        'technology', 'software', 'developer', 'engineer', 'engineering',
        'data science', 'data scientist', 'machine learning', 'ai ',
        'artificial intelligence', 'cloud', 'devops', 'cyber',
        'information security', 'it ', 'systems'
    ]

    # Research keywords
    research_keywords = [
        'research', 'equity research', 'credit research', 'analyst coverage',
        'sector analyst', 'research associate'
    ]

    # Check categories in order of specificity
    if any(keyword in combined for keyword in quant_keywords):
        return 'Quant'

    if any(keyword in combined for keyword in structuring_keywords):
        return 'Structuring'

    if any(keyword in combined for keyword in st_keywords):
        return 'Sales & Trading'

    if any(keyword in combined for keyword in research_keywords):
        return 'Research'

    if any(keyword in combined for keyword in ib_keywords):
        return 'Investment Banking'

    if any(keyword in combined for keyword in tech_keywords):
        return 'Technology'

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
        'Investment Banking': '#1e40af',  # Blue
        'Sales & Trading': '#16a34a',     # Green
        'Structuring': '#9333ea',         # Purple
        'Quant': '#dc2626',               # Red
        'Research': '#ea580c',            # Orange
        'Technology': '#0891b2',          # Cyan
        'Other': '#6b7280'                # Gray
    }
    return color_map.get(category, '#6b7280')
