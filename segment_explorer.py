import time
import os
from threading import Thread
from vod_master_playlist import VodMasterPlaylist
from const import *
from utils.preparemedia import ffmpeg_transcode_and_hls_segmentation, create_segment_index


def explore_segment(master_playlist: VodMasterPlaylist, index, stream_session):
    try:
        while True:
            print(">>> Exploring new segment...")

            start_index = index
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
                    print('........., input_path', input_path)
                    print('........., output_dir', output_dir)
                    ffmpeg_transcode_and_hls_segmentation(input_path, output_dir)
                    variant_path = create_segment_index(stream_session, index)
                    
                    master_playlist.concatenate(VodMasterPlaylist(variant_path))

            time.sleep(1) 
    except KeyboardInterrupt:
        print("Cancel")


def start_explore_segment(master_playlist: VodMasterPlaylist, index, stream_session):
    t = Thread(target=explore_segment, args=(master_playlist, index, stream_session,))
    t.start()