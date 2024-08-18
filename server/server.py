#!/usr/bin/env python3

import http.server
import socketserver
import os
import re
import argparse
import signal
import threading

from vod_master_playlist import VodMasterPlaylist
from preparemedia import ffmpeg_transcode_and_hls_segmentation, create_segment_index
from const import VIDEO_PATH, MANIFEST_PATH
from explore_media import start_explore_video


# Globals
Master_playlist = None

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        """Serve a GET request."""
        path = self.translate_path(self.path)

        """Handle requests for listing directory"""
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
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
        f = None
        try:
            content_type = ""
            # We don't support directory listing
            pattern = rf"{re.escape(MANIFEST_PATH)}/(?P<session>[^/]+)/"
            match = re.search(pattern, path)
            if os.path.isdir(self.path) or not match:
                raise Exception("Illegal url of directory type")
                        
            # If request media segment, return it
            elif file_name.endswith(".ts"):
                content_type = "video/mp2t"

            # If request master playlist, return it (it's already prepared)
            elif "/playlist.m3u8" in self.path:
                content_type = "application/vnd.apple.mpegurl"

            # If request variant playlist, we need to generate it
            session = match.group('session')
            match = re.search(r"/index-(?P<variant_index>\d+).m3u8", self.path)
            if match:
                generate_variant_playlist(int(match.group("variant_index")), session)
                content_type = "application/vnd.apple.mpegurl"

            if not content_type:
                raise Exception("Illegal url")
            
            # Now create the header
            f = open(path, 'rb')
            content_length = str(os.fstat(f.fileno())[6])
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", content_length)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        
        except IOError as e:
            self.send_error(404, "File not found: {}".format(file_name))
        except Exception as e:
            self.send_error(500, "Server error: {}".format(e))

        return f


def generate_master_playlist(source_playlists, stream_session):
    content = ''
    if len(source_playlists) == 0:
         master_playlist = VodMasterPlaylist(stream_session)
    else:   
        master_playlist = VodMasterPlaylist(stream_session, source_playlists[0])
        for p in source_playlists[1:]:
            new_playlist = VodMasterPlaylist(stream_session, p)
            master_playlist.concatenate(new_playlist)

    content = master_playlist.serialize()
    with open(os.path.join(MANIFEST_PATH, stream_session, 'playlist.m3u8'), 'w') as f:
        f.write(content)

    return master_playlist


def generate_variant_playlist(variant_index, stream_session):
    global Master_playlist

    if variant_index < 0 or variant_index > (len(Master_playlist.variants) - 1):
        raise IOError("Non-existing variant playlist")
    
    if Master_playlist is None:
        raise Exception("Master playlist has not been initialized")
    
    with open(os.path.join(MANIFEST_PATH, stream_session, "index-{}.m3u8".format(variant_index)), 'w') as f:
        f.write(Master_playlist.variants[variant_index].serialize())


def start_server(port):
    Handler = CustomHTTPRequestHandler
    httpd = socketserver.ThreadingTCPServer(("", port), Handler)
    httpd.allow_reuse_address = True
    print("Watch stream at: http://localhost:{}/playlist.m3u8".format(port))
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
    parser.add_argument('-s', '--session', type=str, required=True,
                        help="Session identifier (required)")
    args = parser.parse_args()
    port = args.port
    stream_session = args.session

    source_playlists = []
    start_index = -1

    video_path = os.path.join(VIDEO_PATH, stream_session)
    for root, _, files in os.walk(video_path):
        files = sorted(files, key=lambda x: int(x.split('.')[0]))

        for file in files:
            try:
                file_name_ext = os.path.basename(file)
                file_name = os.path.splitext(file_name_ext)[0]
                _index = int(file_name)
            except Exception as e:
                print(f'!!! ERROR === server.py - 133: {e}')
                continue

            # Already process
            if _index - start_index != 1:
                continue

            print(f'\n>>> Found new video: {file} >>> Start video transcoding ...')
            start_index += 1
            input_path = os.path.join(root, file)
            output_dir = os.path.join(MANIFEST_PATH, stream_session, file_name)
            ffmpeg_transcode_and_hls_segmentation(input_path, output_dir)
            variant_path = create_segment_index(stream_session, start_index)
            source_playlists.append(variant_path)
            print(f'<<< Finish transcoding, ready to stream\n')

    global Master_playlist
    Master_playlist = generate_master_playlist(source_playlists, stream_session)

    # Concurrency
    start_explore_video(Master_playlist, start_index, stream_session)

    httpd = start_server(port)
    try:
        signal.pause()  # Wait for a signal (e.g., Ctrl+C)
    except KeyboardInterrupt:
        print("Shutting down the server...")
        stop_server(httpd)

if __name__ == '__main__':
    main()
