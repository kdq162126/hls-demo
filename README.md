# hls-stream
Simple HLS streaming server

## Prerequirements
python3 needed for running the program

## Quick start
* Serve single VOD file

   `python3 server.py testdata/m1-all_Custom.m3u8`

* Serve multiple VOD file (concatenated in the given order)

  `python3 server.py testdata/m1-all_Custom.m3u8 testdata/m2-all_Custom.m3u8 testdata/m3-all_Custom.m3u8`
 
* Serve in live streaming mode (looping files in given order)

  `python3 server.py -l testdata/m1-all_Custom.m3u8 testdata/m2-all_Custom.m3u8 testdata/m3-all_Custom.m3u8`
  
After starting server, the HLS streaming url will be displayed, for example:

  `Watch stream at: http://192.168.1.127:8000/playlist.m3u8`

Run `python3 server.py -h` to check all options

```bash
ffmpeg -i 8.mp4 -c:v libx264 -c:a aac -strict -2 -f hls -hls_time 8 -hls_list_size 0 -hls_segment_filename "frag-%d.ts" index.m3u8
```

```bash
python3 server.py -l  testdata/0.m3u8 testdata/1.m3u8 testdata/2.m3u8 testdata/3.m3u8 testdata/4.m3u8 testdata/5.m3u8 testdata/6.m3u8 testdata/7.m3u8 testdata/8.m3u8
```
