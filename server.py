#!/usr/bin/env python3

import http.server
import socketserver
import os
import socket
import time
import re
import argparse
import vod_master_playlist as mp
import signal
import threading
from utils.preparemedia import ffmpeg_transcode_and_hls_segmentation, create_segment_index
from const import *
from segment_explorer import start_explore_segment


# Globals
master_playlist = None
start_time = None
is_vod = None

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def send_head(self):
        """Serve a GET request."""
        path = self.translate_path(self.path)
        
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        
        file_name = os.path.basename(path)
        try:
            content_type = ""
            if os.path.isdir(path):
                raise Exception("Illegal url of directory type")
            if file_name.endswith(".ts"):
                content_type = "video/mp2t"
            if self.path == "/playlist.m3u8":
                content_type = "application/vnd.apple.mpegurl"
            match = re.match(r"/index-(?P<variant_index>\d+).m3u8", self.path)
            if match:
                generate_variant_playlist(int(match.group("variant_index")))
                content_type = "application/vnd.apple.mpegurl"
            if not content_type:
                raise Exception("Illegal url")
            
            f = open(path, 'rb')
            content_length = str(os.fstat(f.fileno())[6])
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", content_length)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return f
        except IOError as e:
            self.send_error(404, "File not found: {}".format(file_name))
        except Exception as e:
            self.send_error(500, "Server error: {}".format(e))
        return None

def generate_master_playlist(source_playlists):
    global master_playlist
    master_playlist = mp.VodMasterPlaylist(source_playlists[0])
    for p in source_playlists[1:]:
        new_playlist = mp.VodMasterPlaylist(p)
        master_playlist.concatenate(new_playlist)
    with open("playlist.m3u8", 'w') as f:
        f.write(master_playlist.serialize())

    return master_playlist

def generate_variant_playlist(variant_index):
    if variant_index < 0 or variant_index > (len(master_playlist.variants) - 1):
        raise IOError("Non-existing variant playlist")
    if master_playlist is None:
        raise Exception("Master playlist has not been initialized")
    
    with open("index-{}.m3u8".format(variant_index), 'w') as f:
        time_offset = int(time.time()) - start_time if not is_vod else 0
        f.write(master_playlist.variants[variant_index].serialize(is_vod, 3, time_offset))

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]

def start_server(port):
    Handler = CustomHTTPRequestHandler
    httpd = socketserver.ThreadingTCPServer(("", port), Handler)
    httpd.allow_reuse_address = True
    print("Watch stream at: http://{}:{}/playlist.m3u8".format(get_ip_address(), port))
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return httpd

def stop_server(httpd):
    httpd.shutdown()
    httpd.server_close()



def main():
    help_text = """
    Start HLS streaming server with existing HLS VOD files.
    You can serve either a single VOD file or concatenate several VOD files and serve them (they must have the same
    encoding parameters to be concatenated).
    You can also start live streaming by looping existing VOD file(s) with -l or --loop.
    """
    parser = argparse.ArgumentParser(description=help_text)
    parser.add_argument('-p', '--port', nargs='?', type=int, default=8000,
                        help="Port to serve from, default 8000")
    parser.add_argument('-l', '--loop', dest='loop', action='store_true',
                        help="Serve in loop mode (live streaming)")
    args = parser.parse_args()
    source_playlists = []
    # source_playlists = args.playlists
    port = args.port

    stream_session = 'xxx'
    index = 0
    start_index = -1
    video_path = os.path.join(VIDEO_PATH, stream_session)
    for root, dirs, files in os.walk(video_path):
        files = sorted(files, key=lambda x: int(x.split('.')[0]))
        for file in files:
            try:
                file_name_ext = os.path.basename(file)
                file_name = os.path.splitext(file_name_ext)[0]
                _index = int(file_name)
            except Exception as e:
                print(f'... server.py - 133: {e}')
                continue

            # Already process
            if _index - start_index != 1:
                continue

            print('FOUNDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD', file)
            start_index += 1
            index = start_index
            input_path = os.path.join(root, file)
            output_dir = os.path.join(MANIFEST_PATH, stream_session, file_name)
            ffmpeg_transcode_and_hls_segmentation(input_path, output_dir)
            variant_path = create_segment_index(stream_session, index)
            source_playlists.append(variant_path)

    print('....', source_playlists)
    
    global is_vod, start_time
    is_vod = not args.loop

    master_playlist = generate_master_playlist(source_playlists)
    start_time = int(time.time())

    ###
    start_explore_segment(master_playlist, index, stream_session)

    httpd = start_server(port)

    try:
        signal.pause()  # Wait for a signal (e.g., Ctrl+C)
    except KeyboardInterrupt:
        print("Shutting down the server...")
        stop_server(httpd)

if __name__ == '__main__':
    main()
