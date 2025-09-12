"""
Holder classification system using emoji representations.
Maps token amounts to appropriate holder categories.
"""

from utils.config import HOLDERS_EMOJIS


def map_holder_emoji(token_amount: float) -> str:
    """
    Map token amounts to appropriate holder category emoji.
    
    Args:
        token_amount: Number of tokens held/transferred
        
    Returns:
        str: Emoji representing holder category
        
    Examples:
        >>> map_holder_emoji(500)
        '🦐'  # Shrimp
        >>> map_holder_emoji(50000)
        '🐬'  # Dolphin
        >>> map_holder_emoji(5000000)
        '🦈'  # Shark
    """
    # Iterate through thresholds in descending order
    for threshold in sorted(HOLDERS_EMOJIS.keys(), reverse=True):
        if token_amount >= threshold:
            return HOLDERS_EMOJIS[threshold]
    
    # Fallback to smallest category
    return HOLDERS_EMOJIS[0]
