import re
import json
from datetime import datetime


def hhmmss_to_milliseconds(time_string):
    parts = time_string.split(":")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = (hours * 3600 + minutes * 60 + seconds) * 1000

    return milliseconds


def chunk(array, size):
    chunks = []
    for i in range(0, len(array), size):
        chunks.append(array[i:i + size])
    return chunks


def getSrtSlices(raw_contents):
    pattern = r'\d+\r?\n(\d\d:\d\d:\d\d\.\d\d\d \-)'
    raw_contents_arr = re.split(pattern, raw_contents)
    raw_contents_arr2 = raw_contents_arr[:]
    if raw_contents_arr[0] == '':
        raw_contents_arr2 = raw_contents_arr[1:]
    raw_contents_arr3 = chunk(raw_contents_arr2, 2)
    raw_contents_arr4 = ["".join(subtitle) for subtitle in raw_contents_arr3]
    return raw_contents_arr4


def split_web_vtt(raw_contents):
    timespatt = r'(\d\d:\d\d:\d\d\.\d\d\d) \-\-> (\d\d:\d\d:\d\d\.\d\d\d)'
    raw_contents_arr = getSrtSlices(raw_contents)
    start_time_0 = datetime(1900, 1, 1, 0, 0, 0)
    test_fragments_with_timestamps = []
    for i, row in enumerate(raw_contents_arr[:]):
        i, row
        row_split = re.split(r'\r?\n', row)
        row_split = [r for r in row_split if r != '']

        assert len(row_split) == 2
        time_str, texti = row_split

        texti = texti.strip()
        start, stop = re.findall(timespatt, row)[0]
        start, stop

        start_time = datetime.strptime(start, "%H:%M:%S.%f")

        timDelta = start_time - start_time_0
        msecs = int(timDelta.seconds * 1000 + timDelta.microseconds / 1000)
        test_fragments_with_timestamps.append((msecs, texti))
    return test_fragments_with_timestamps


def split_word_transcription(raw_contents):
    pattern = r'(\d{2}:\d{2}:\d{2}\r?\n.*?\n)'
    result = re.findall(pattern, raw_contents)
    result_array = [timed_text.split("\n") for timed_text in result]
    result_array_fixed = [[rItem for rItem in r if rItem != ''] for r in result_array]

    # fail early in development
    assert [r for r in result_array_fixed if len(r) != 2] == []

    test_fragments_with_timestamps = [(hhmmss_to_milliseconds(time_str), words.strip()) for time_str, words in
                                      result_array_fixed]
    return test_fragments_with_timestamps


def split_youtube_transcription(raw_content):
    timed_text_dict = json.loads(raw_content)
    events = timed_text_dict['events']
    test_fragments_with_timestamps = [(e['tStartMs'], "".join([s['utf8'] for s in e['segs']])) for e in events if
                                      'segs' in e]
    test_fragments_with_timestamps = [(tStartMsm, text) for tStartMsm, text in test_fragments_with_timestamps if
                                      text.strip() != '']
    return test_fragments_with_timestamps
