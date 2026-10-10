def merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge sorted/unsorted overlapping or touching inclusive integer intervals."""
    
    # Handle empty input
    if not windows:
        return []
    
    # Validate and filter windows
    validated = []
    for window in windows:
        # Check if it's a tuple with exactly 2 elements
        if not isinstance(window, tuple) or len(window) != 2:
            raise ValueError("Invalid window format")
        
        start, end = window
        
        # Reject bool (bool is subclass of int in Python)
        if isinstance(start, bool) or isinstance(end, bool):
            raise ValueError("Endpoints cannot be boolean")
        
        # Check both endpoints are exactly int (not subclasses)
        if type(start) is not int or type(end) is not int:
            raise ValueError("Endpoints must be integers")
        
        # Check for reversed intervals
        if start > end:
            raise ValueError("Invalid interval: start must not exceed end")
        
        validated.append((start, end))
    
    # Sort by start time
    validated.sort(key=lambda x: x[0])
    
    # Merge overlapping or adjacent intervals
    merged = []
    for start, end in validated:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]
            # Check if current overlaps with or touches the last interval
            if start <= last_end + 1:  # Overlapping or directly adjacent
                # Extend the last interval if needed
                merged[-1][1] = max(last_end, end)
            else:
                # No overlap, add new interval
                merged.append([start, end])
    
    # Convert back to tuples
    return [tuple(interval) for interval in merged]
