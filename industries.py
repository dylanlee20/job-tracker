"""
Industry classification configuration
Manages company-to-industry mappings and industry metadata
"""

# Company to industry mapping
COMPANY_INDUSTRY_MAPPING = {
    'JPMorgan': 'Investment Banking',
    'Goldman Sachs': 'Investment Banking',
    'Morgan Stanley': 'Investment Banking',
    'Bank of America': 'Investment Banking',
    'Citigroup': 'Investment Banking',
    'Barclays': 'Investment Banking',
    'Deutsche Bank': 'Investment Banking',
    'UBS': 'Investment Banking',
    'HSBC': 'Commercial Banking',
    'BNP Paribas': 'Investment Banking',
    'Blackstone': 'Private Equity',
    'Evercore': 'Investment Banking',
    'Jefferies': 'Investment Banking',
    'Mizuho': 'Investment Banking',
    'Nomura': 'Investment Banking',
    'Piper Sandler': 'Investment Banking',
}

# Industry display order and colors
INDUSTRIES = [
    {'name': 'Investment Banking', 'color': '#1e40af'},
    {'name': 'Commercial Banking', 'color': '#16a34a'},
    {'name': 'Private Equity', 'color': '#9333ea'},
    {'name': 'Asset Management', 'color': '#dc2626'},
    {'name': 'Hedge Fund', 'color': '#ea580c'},
    {'name': 'Venture Capital', 'color': '#0891b2'},
    {'name': 'Consulting', 'color': '#6b7280'},
    {'name': 'Technology', 'color': '#8b5cf6'},
    {'name': 'Other', 'color': '#64748b'},
]

def get_industry_for_company(company_name):
    """
    Get industry for a given company

    Args:
        company_name: Name of the company

    Returns:
        Industry name or 'Other' if not found
    """
    return COMPANY_INDUSTRY_MAPPING.get(company_name, 'Other')

def get_industry_color(industry_name):
    """
    Get color code for an industry

    Args:
        industry_name: Name of the industry

    Returns:
        Color hex code or default color if not found
    """
    for industry in INDUSTRIES:
        if industry['name'] == industry_name:
            return industry['color']
    return '#64748b'  # Default color
