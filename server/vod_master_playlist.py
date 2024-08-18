"""
Master playlist for a VOD track
Could contain one or more variant playlists
"""

import os
import re

from vod_variant_playlist import VodVariantPlaylist
from const import BANDWIDTH, RESOLUTION, CODECS


class VodMasterPlaylist():
    def __init__(self, session, location=None):
        self.session = session
        if location:
            self.variants = self.parse(location)
        else:
            variant = VodVariantPlaylist(session, BANDWIDTH, RESOLUTION, CODECS.split(', '))
            self.variants = [variant]

    def parse(self, location):
        variants = []
        with open(location, 'r') as f:
            # Check first line start with #EXTM3U, otherwise throw exception
            if f.readline() != '#EXTM3U\n':
                raise RuntimeError(
                        "Error parsing {},"
                        "valid manifest should start with #EXTM3U".format(location))
            content = f.read()
        path = os.path.dirname(location)
        # Regex magic intend to find all variant playlists here
        pattern = r"^#EXT-X-STREAM-INF:.*?BANDWIDTH=(?P<bw>\d+),"\
                   ".*?RESOLUTION=(?P<res_width>\d+)x(?P<res_height>\d+),"\
                   ".*?CODECS=\"(?P<codecs>.*?)\".*?^(?P<variant_playlist>.*?\.m3u8)$"
        for match in re.finditer(pattern, content, re.M|re.S):
            bandwidth = int(match.group("bw"))
            resolution = "{}x{}".format(int(match.group("res_width")),
                                        int(match.group("res_height")))
            codecs = set([c.strip() for c in match.group("codecs").split(',')])
            variant_location = os.path.join(path, match.group("variant_playlist"))
            if os.path.isfile(variant_location):
                variant = VodVariantPlaylist(self.session, bandwidth, resolution, codecs, variant_location)
                variants.append(variant)
        return sorted(variants, key=lambda x:x.resolution)

    def serialize(self):
        playlist = "#EXTM3U\n"
        index = 0
        for variant in self.variants:
            codecs = ", ".join(sorted(variant.codecs))
            playlist += "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={},"\
                        "RESOLUTION={},CODECS=\"{}\"\n".format(variant.bandwidth,
                                variant.resolution, codecs)
            playlist += "index-{}.m3u8\n".format(index)
            index += 1
        return playlist

    def concatenate(self, new_playlist):
        if len(new_playlist.variants) != len(self.variants):
            raise RuntimeError("Master playlist doesn't contain same amount of variants")
        
        if self.variants[0].is_dummy:
            self.variants = new_playlist.variants
            return

        for i in range(0, len(self.variants)):
            self.variants[i].concatenate(new_playlist.variants[i])
