from django.urls import path
from liverstream import views

urlpatterns = [
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('playlist.m3u8', views.playlist, name='playlist'),
]
