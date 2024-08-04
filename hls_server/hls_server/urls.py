from django.urls import path
from liverstream import views

urlpatterns = [
    path('playlist.m3u8', views.serve_hls, name='playlist'),
    path('index-<int:variant_index>.m3u8', views.serve_hls, name='variant_playlist'),
]
