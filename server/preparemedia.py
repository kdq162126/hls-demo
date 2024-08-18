import subprocess
import os
import shutil
from const import *


def ffmpeg_transcode_and_hls_segmentation(input_path, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    seg_path = os.path.join(output_dir, '%03d.ts')
    out_path = os.path.join(output_dir, 'mono.m3u8')

    ffmpeg_cmd = (
        f'ffmpeg -i {input_path} {FFMPEG_FPS_OPTS} {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} '
        f'-f hls -hls_time {HLS_DURATION} -hls_list_size 0 -hls_segment_filename "{seg_path}" '
        f'{out_path}'
    )
    # print(f'>>>>> {ffmpeg_cmd}')
    result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f'Error during ffmpeg transcoding: {result.stderr}')
    

def create_segment_index(session, index):
    session_dir = os.path.join(MANIFEST_PATH, session)
    if not os.path.isdir(session_dir):
        raise Exception('Session not found')

    index_dir = os.path.join(session_dir, str(index))
    variant = "#EXTM3U\n"
    variant += "#EXT-X-STREAM-INF:PROGRAM-ID=1, "\
                f"BANDWIDTH={BANDWIDTH}, "\
                f"RESOLUTION={RESOLUTION}, "\
                f"CODECS=\"{CODECS}\"\n"
    variant += "mono.m3u8\n"

    variant_path = os.path.join(index_dir, 'index.m3u8')
    with open(variant_path, 'w') as f:
        f.write(variant)

    return variant_path



