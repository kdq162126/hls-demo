# FFMPEG options
FFMPEG_FPS_OPTS = '-r 30 -g 30'
FFMPEG_PROFILE_OPTS = '-profile:v high -level:v 4.1'
FFMPEG_CODEC_OPTS = '-codec:v libx264 -codec:a aac -strict -2'

# Video quality
BANDWIDTH = '2064000'
RESOLUTION = '568x320'
CODECS = 'avc1.42001f, mp4a.40.2'

# HLS options
HLS_VERSION = 3
HLS_DURATION = 3
CHUNK_SIZE = 4

# Static dir
MANIFEST_PATH = 'static/stream'
VIDEO_PATH = 'static/video'