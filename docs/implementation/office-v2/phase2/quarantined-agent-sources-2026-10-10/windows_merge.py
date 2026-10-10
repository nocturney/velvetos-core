def merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge sorted/unsorted overlapping or touching inclusive integer intervals."""
    
    # Handle empty input
    if not windows:
        return []
    
    # Validate each interval
    for i, window in enumerate(windows):
        # Must be a tuple of exactly two elements (not list)
        if not isinstance(window, tuple) or len(window) != 2:
            raise ValueError("Invalid interval format")
        
        start, end = window
        
        # Both endpoints must be int (bool is subclass of int, so explicitly reject bool)
        if isinstance(start, bool) or isinstance(end, bool):
            raise ValueError("Endpoints must be integers, not booleans")
        
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError("Endpoints must be integers")
        
        # start must not exceed end
        if start > end:
            raise ValueError("Start must not exceed end")
    
    # Sort by start time
    sorted_windows = sorted(windows, key=lambda x: x[0])
    
    # Merge overlapping or adjacent intervals
    result = []
    current_start, current_end = sorted_windows[0]
    
    for i in range(1, len(sorted_windows)):
        next_start, next_end = sorted_windows[i]
        
        # Check if intervals overlap or are adjacent (inclusive)
        # For inclusive integer intervals: merge when next_start <= previous_end + 1
        if next_start <= current_end + 1:
            # Merge them - extend the end if needed
            current_end = max(current_end, next_end)
        else:
            # No overlap, add current to result and start new
            result.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    # Add the last interval
    result.append((current_start, current_end))
    
    return result
