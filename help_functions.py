ALLOWED_SOUND_FILE_EXTENSIONS = {'mp3', 'wav', 'ogg' }

def convert_seconds_to_hms(seconds):
    # Calculate hours, minutes, and remaining seconds
    if not seconds:
        return ''
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    # Format as h:m:s
    return f"{hours}:{minutes:02}:{secs:02}"


def convert_hms_to_seconds(hms):
    # Split the input string into hours, minutes, and seconds
    parts = hms.split(':')
    
    # Extract hours, minutes, and seconds from the parts
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        secs = int(parts[2])
    elif len(parts) == 2:
        hours = 0
        minutes = int(parts[0])
        secs = int(parts[1])
    elif len(parts) == 1:
        hours = 0
        minutes = 0
        secs = int(parts[0])
    # Calculate total seconds
    total_seconds = hours * 3600 + minutes * 60 + secs
    
    return total_seconds

 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_SOUND_FILE_EXTENSIONS