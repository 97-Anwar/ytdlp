from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-playlist/', views.fetch_playlist, name='fetch_playlist'),
    # path('playlist/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:pk>/download/',
         views.download_videos, name='download_videos'),
]
