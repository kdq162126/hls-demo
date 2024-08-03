from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import render
import os
import re
import time

global master_playlist
global start_time
global is_vod

def serve_media(request, path):
    global master_playlist
    global start_time
    global is_vod

    # Handle directory listings or file serving
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.isdir(full_path):
        if not path.endswith('/'):
            return redirect(path + '/')
        for index in ["index.html", "index.htm"]:
            index_path = os.path.join(full_path, index)
            if os.path.exists(index_path):
                full_path = index_path
                break
        else:
            return HttpResponse("Directory listing not supported", status=403)
    
    # Determine content type and serve file
    file_name = os.path.basename(full_path)
    if os.path.isfile(full_path):
        content_type = "application/octet-stream"
        if file_name.endswith(".ts"):
            content_type = "video/mp2t"
        elif file_name.endswith(".m3u8"):
            content_type = "application/vnd.apple.mpegurl"

        with open(full_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Length'] = os.path.getsize(full_path)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
    raise Http404("File not found")

def playlist(request):
    global master_playlist
    global start_time
    global is_vod

    if master_playlist is None:
        raise Http404("Master playlist not initialized")

    if 'variant_index' in request.GET:
        try:
            variant_index = int(request.GET['variant_index'])
        except ValueError:
            raise Http404("Invalid variant index")
        if variant_index < 0 or variant_index >= len(master_playlist.variants):
            raise Http404("Variant playlist does not exist")

        time_offset = 0
        if not is_vod:
            time_offset = int(time.time()) - start_time

        playlist_data = master_playlist.variants[variant_index].serialize(is_vod, 3, time_offset)
        return HttpResponse(playlist_data, content_type="application/vnd.apple.mpegurl")
    
    # Default to master playlist
    master_playlist_data = master_playlist.serialize()
    return HttpResponse(master_playlist_data, content_type="application/vnd.apple.mpegurl")
