"""Time formatting utilities."""


def format_time(ms: int) -> str:
    """
    Format milliseconds to timer display string.
    
    Args:
        ms: Time in milliseconds
    
    Returns:
        str: Formatted time
            < 60s: "S.cc" (e.g., "9.87")
            >= 60s: "M:SS.cc" (e.g., "1:01.23")
    
    Note: Truncates (rounds down) centiseconds, does not round up.
    """
    # Truncate to centiseconds (10ms precision)
    cs = ms // 10
    
    total_seconds = cs // 100
    centiseconds = cs % 100
    
    if total_seconds < 60:
        # Format as S.cc
        return f"{total_seconds}.{centiseconds:02d}"
    else:
        # Format as M:SS.cc
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}.{centiseconds:02d}"
