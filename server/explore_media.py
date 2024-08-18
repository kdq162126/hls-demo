import time
import os
from threading import Thread
from vod_master_playlist import VodMasterPlaylist
from const import *
from preparemedia import ffmpeg_transcode_and_hls_segmentation, create_segment_index


def explore_video(master_playlist: VodMasterPlaylist, start_index, stream_session):
    try:
        while True:
            print("... Exploring new video ...")

            video_path = os.path.join(VIDEO_PATH, stream_session)
            for root, _, files in os.walk(video_path):
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
                    
                    print(f'\n>>> Found new video: {file} >>> Start video transcoding ...')
                    start_index += 1
                    input_path = os.path.join(root, file)
                    output_dir = os.path.join(MANIFEST_PATH, stream_session, file_name)
                    ffmpeg_transcode_and_hls_segmentation(input_path, output_dir)
                    variant_path = create_segment_index(stream_session, start_index)
                    master_playlist.concatenate(VodMasterPlaylist(stream_session, variant_path))
                    print(f'<<< Finish transcoding, ready to stream\n')

            time.sleep(1) 
    except KeyboardInterrupt:
        print("Cancel")


def start_explore_video(master_playlist: VodMasterPlaylist, index, stream_session):
    t = Thread(target=explore_video, args=(master_playlist, index, stream_session,))
    t.start()