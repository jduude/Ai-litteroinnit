 

class Transcription:
    def __init__(self, title, source_path, source, genre, raw_content, user_id, 
                 license, record_date, duration_sec, extra_meta_data=None):
        self.title = title
        self.source_path = source_path
        self.source = source
        self.genre = genre
        self.raw_content = raw_content
        self.user_id = user_id
        self.license = license
        self.record_date = record_date   
        self.duration_sec = duration_sec
        self.extra_meta_data = extra_meta_data
