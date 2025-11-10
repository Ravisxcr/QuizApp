from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    return dictionary.get(key)

@register.filter
def duration_display(start_time, end_time):
    """Calculate and display duration between two datetime objects in a readable format."""
    if not start_time or not end_time:
        return "-"
    
    # Calculate the difference
    duration = end_time - start_time
    
    # Get total seconds
    total_seconds = int(duration.total_seconds())
    
    # Handle negative durations (shouldn't happen, but just in case)
    if total_seconds < 0:
        return "-"
    
    # Calculate minutes and seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    # Format the output
    if minutes == 0:
        return f"{seconds}s"
    elif seconds == 0:
        return f"{minutes}m"
    else:
        return f"{minutes}m {seconds}s"