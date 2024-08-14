import subprocess
import os
import shutil


# FFMPEG options
FFMPEG_FPS_OPTS = '-r 30 -g 30'
FFMPEG_PROFILE_OPTS = '-profile:v high -level:v 4.1'
FFMPEG_CODEC_OPTS = '-codec:v libx264 -codec:a aac -strict -2'

# HLS options
HLS_TIME = 3


def ffmpeg_transcode_and_hls_segmentation(input_path, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    file_name_ext = os.path.basename(input_path)
    file_name = os.path.splitext(file_name_ext)[0]
    seg_path = os.path.join(output_dir, f'{file_name}-%03d.ts')
    out_path = os.path.join(output_dir, f'{file_name}.m3u8')

    ffmpeg_cmd = (
        f'ffmpeg -i {input_path} {FFMPEG_FPS_OPTS} {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} '
        f'-f hls -hls_time {HLS_TIME} -hls_list_size 0 -hls_segment_filename "{seg_path}" '
        f'{out_path}'
    )
    print(f'>>>>> {ffmpeg_cmd}')
    result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f'Error during ffmpeg transcoding: {result.stderr}')
    

# ffmpeg_transcode_and_hls_segmentation('datatest/origin/0.mp4', 'out/0')