from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.http import require_GET
import os
import re
import time
import traceback
import time

from .utils.vod_master_playlist import VodMasterPlaylist

source_playlists = ['static/0/index-0.m3u8']
start_time = int(time.time())
is_vod = True

def generate_master_playlist(source_playlists):
    master_playlist = VodMasterPlaylist(source_playlists[0])
    for p in source_playlists[1:]:
        new_playlist = VodMasterPlaylist(p)
        master_playlist.concatenate(new_playlist)
    return master_playlist.serialize()

def generate_variant_playlist(variant_index):
    if variant_index < 0 or variant_index >= len(master_playlist.variants):
        raise IOError("Non-existing variant playlist")
    time_offset = 0
    if not is_vod:
        time_offset = int(time.time()) - start_time
    return master_playlist.variants[variant_index].serialize(is_vod, 3, time_offset)

@require_GET
def serve_hls(request):

    path = request.path_info

    try:
        if path == "/playlist.m3u8":
            content_type = "application/vnd.apple.mpegurl"
            content = generate_master_playlist(source_playlists)
            response = HttpResponse(content, content_type=content_type)
            return response

        match = re.match(r"/index-(?P<variant_index>\d+).m3u8", path)
        if match:
            variant_index = int(match.group("variant_index"))
            content = generate_variant_playlist(variant_index)
            content_type = "application/vnd.apple.mpegurl"
            response = HttpResponse(content, content_type=content_type)
            return response

        # Handle other media segment requests
        file_name = os.path.basename(path)
        if file_name.endswith(".ts"):
            content_type = "video/mp2t"
            file_path = os.path.join('/path/to/media/folder', path.lstrip('/'))
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
            return response

        raise Exception("Illegal URL")

    except IOError as e:
        traceback.print_exc()
        return HttpResponseServerError(str(e))
    except Exception as e:
        traceback.print_exc()
        return HttpResponseServerError(str(e))
