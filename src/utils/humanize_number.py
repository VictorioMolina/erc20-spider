"""
Number formatting utility for human-readable display.
Converts large numbers to abbreviated formats (K, M, B).
"""


def humanize_number(number: float) -> str:
    """
    Convert numeric values to human-readable abbreviated format.
    
    Args:
        number: Numeric value to format
        
    Returns:
        str: Formatted string with appropriate suffix (K/M/B)
        
    Examples:
        >>> humanize_number(1234)
        '1.23K'
        >>> humanize_number(2500000)
        '2.50M'
        >>> humanize_number(1000000000)
        '1.00B'
    """
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    
    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    
    if number >= 1_000:
        return f"{number / 1_000:.2f}K"
    
    return f"{number:.0f}"
