"""
Contains information from one single VOD variant playlist
Which should include general information:
    bandwidth, resolution, codec
As well as a list of media segments included in this track
"""

import os
import segment
import re

from pathlib import Path
from const import HLS_DURATION, HLS_VERSION, CHUNK_SIZE, MANIFEST_PATH

# GLOBAL
Current_index = 0
Media_sequence = 0

class VodVariantPlaylist():
    def __init__(self, session, bandwidth, resolution, codecs, location=None):
        self.session = session
        self.bandwidth = bandwidth
        self.resolution = resolution
        self.codecs = codecs
        self.is_dummy = True
        
        try:
            if os.path.isfile(location):
                self.target_duration, self.segments = self.parse(location)
                self.is_dummy = False
        except Exception as e:
            print(f'... WARNING === vod_varitant_playlist.py -- 31: {e} >>> Skip ...')

    def parse(self, location):
        with open(location, 'r') as f:
            content = f.read()

        pattern = r"^#EXT-X-TARGETDURATION:(?P<target_duration>\d+)$"
        match = re.search(pattern, content, re.M)
        if match is None:
            raise RuntimeError("Unable to find target duration")
        target_duration = int(match.group("target_duration"))
        path = os.path.dirname(location.replace(f'{MANIFEST_PATH}/{self.session}/', ''))
        segments = []
        segment_index = 0
        segment_start_time = 0
        # Regex parsing, output will be iteration object with "duration" and "location"
        # for each segment
        pattern = r"^#EXTINF:(?P<duration>\d+(\.\d+)?),\s*(?P<location>[^,\s]+\.ts)$"
        for match in re.finditer(pattern, content, re.M):
            segment_duration = float(match.group("duration"))
            segment_location = os.path.join(path, match.group("location"))

            s = segment.Segment(segment_index, segment_location, segment_start_time, segment_duration)
            segments.append(s)
            segment_index += 1
            segment_start_time += segment_duration
        # Let's set discontinuity flag on last segment
        last_segment = segments[segment_index-1]
        last_segment.update_discontinuity(True)
        return (target_duration, segments)


    def serialize(self):
        global Current_index, Media_sequence

        playlist = "#EXTM3U\n"
        playlist += "#EXT-X-VERSION:{}\n".format(HLS_VERSION)
        if self.is_dummy:
            playlist += "#EXT-X-TARGETDURATION:{}\n".format(HLS_DURATION)
            playlist += "#EXT-X-MEDIA-SEQUENCE:{}\n".format(0)
            playlist += "#EXT-X-DISCONTINUITY\n"
            return playlist

        playlist += "#EXT-X-TARGETDURATION:{}\n".format(self.target_duration)

        if Current_index < len(self.segments) - CHUNK_SIZE:
            segments = self.segments[Current_index:Current_index+CHUNK_SIZE]               
            Current_index += 1
            Media_sequence += 1
        else:
            segments = self.segments[-CHUNK_SIZE:]

        playlist += "#EXT-X-MEDIA-SEQUENCE:{}\n".format(Media_sequence)
        for s in segments:
            playlist += "#EXTINF:{},\n".format(s.duration)
            playlist += "{}\n".format(s.location)
            if s.discontinuity:
                playlist += "#EXT-X-DISCONTINUITY\n"

        return playlist


    """
    Concatenate a new variant playlist after the current one
    The new playlist needs to have the exact same parameters (bandwidth,
    resolution, codecs, target segment length.
    """
    def concatenate(self, new_playlist):       
        if new_playlist.bandwidth != self.bandwidth or \
           new_playlist.resolution != self.resolution or \
           new_playlist.codecs != self.codecs or \
           new_playlist.target_duration != self.target_duration:
               raise RuntimeError("Cannot append variant playlist"\
                       ", different parameters detected")
        index = len(self.segments)
        start_time = self.segments[index - 1].start_time + \
                     self.segments[index - 1].duration
        for s in new_playlist.segments:
            s.id = index
            s.start_time = start_time
            self.segments.append(s)
            index += 1
            start_time += s.duration
