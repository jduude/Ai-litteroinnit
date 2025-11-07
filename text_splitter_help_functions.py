
import re
import json


def hhmmss_to_milliseconds(time_string):
    parts = time_string.split(":")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = (hours * 3600 + minutes * 60 + seconds) * 1000

    return milliseconds


def split_word_transcription(raw_contents):
    pattern = r'(\d{2}:\d{2}:\d{2}\r?\n[^0-9]+)'
    result = re.findall(pattern, raw_contents)
    result_array = [timed_text.split("\n") for timed_text in result]
    result_array_fixed = [[rItem for rItem in r if rItem != ''] for r in result_array]

    # fail early in development
    assert [r for r in result_array_fixed if len(r) != 2] == []

    test_fragments_with_timestamps = [(hhmmss_to_milliseconds(time_str), words) for time_str, words in result_array_fixed]
    return test_fragments_with_timestamps


def split_youtube_transcription(raw_content):
    timed_text_dict = json.loads(raw_content)
    events = timed_text_dict['events']
    test_fragments_with_timestamps = [(e['tStartMs'], "".join([s['utf8'] for s in e['segs']])) for e in events if
                                      'segs' in e]
    test_fragments_with_timestamps = [(tStartMsm, text) for tStartMsm, text in test_fragments_with_timestamps if
                                      text.strip() != '']
    return  test_fragments_with_timestamps
