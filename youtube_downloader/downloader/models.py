from django.db import models

class Playlist(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

class Video(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255)
    url = models.URLField()
    selected = models.BooleanField(default=True)