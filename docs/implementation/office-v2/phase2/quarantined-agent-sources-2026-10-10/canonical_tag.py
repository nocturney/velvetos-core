def canonical_tag(text: str) -> str:
    """ASCII lowercase alphanumerics, single underscore separators, default untitled."""
    # First, convert to lowercase
    text = text.lower()
    
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        # Check if this is ASCII alphanumeric (a-z or 0-9)
        is_alnum = ord(char) >= 97 and ord(char) <= 122 or ord(char) >= 48 and ord(char) <= 57
        
        if is_alnum:
            result.append(char)
            i += 1
        else:
            # Non-alphanumeric character
            # Check if it's immediately after a letter or digit
            if i > 0 and text[i-1].isalnum() and ord(text[i-1]) < 128:
                result.append('_')
                i += 1
            else:
                # Skip this non-alphanumeric character
                i += 1
    
    # Remove leading underscores
    while result and result[0] == '_':
        result.pop(0)
    
    # Remove trailing underscores
    while result and result[-1] == '_':
        result.pop()
    
    if not result:
        return "untitled"
    
    return ''.join(result)
