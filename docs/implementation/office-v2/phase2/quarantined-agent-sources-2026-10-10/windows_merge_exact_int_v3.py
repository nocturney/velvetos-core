def merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge sorted/unsorted overlapping or touching inclusive integer intervals."""
    
    # Handle empty input
    if not windows:
        return []
    
    # Validate each window
    def validate_window(window):
        # Check it's a tuple of exactly 2 elements
        if not isinstance(window, tuple) or len(window) != 2:
            raise ValueError("Window must be a tuple of two elements")
        
        start, end = window
        
        # Check both are exact int type (not bool, not subclasses)
        if type(start) is not int or type(end) is not int:
            raise ValueError("Endpoints must be integers")
        
        # Check for reversed intervals
        if start > end:
            raise ValueError("Start must be <= end")
    
    # Validate all windows first
    for window in windows:
        validate_window(window)
    
    # Sort by start time
    sorted_windows = sorted(windows, key=lambda x: x[0])
    
    # Merge overlapping or adjacent intervals
    result = []
    if sorted_windows:
        current_start, current_end = sorted_windows[0]
        
        for i in range(1, len(sorted_windows)):
            next_start, next_end = sorted_windows[i]
            
            # Check if intervals overlap or touch (adjacent)
            # For inclusive integers, they merge if next_start <= current_end + 1
            if next_start <= current_end + 1:
                # Merge them
                current_end = max(current_end, next_end)
            else:
                # No overlap, add current and start new
                result.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        
        # Add the last interval
        result.append((current_start, current_end))
    
    return result
