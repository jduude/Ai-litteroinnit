

def convert_seconds_to_hms(seconds):
    # Calculate hours, minutes, and remaining seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    # Format as h:m:s
    return f"{hours}:{minutes:02}:{secs:02}"

 