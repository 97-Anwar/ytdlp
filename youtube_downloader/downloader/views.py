
import yt_dlp
import json
import tempfile
import os
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from .models import Playlist, Video


@ensure_csrf_cookie
def home(request):
    return render(request, 'downloader/home.html')


def fetch_playlist(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        quality = request.POST.get('quality', '720p')

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            playlist = Playlist.objects.create(
                url=url,
                title=info['title'],
                description=info.get('description', '')
            )

            videos = []
            for entry in info['entries']:
                video = Video.objects.create(
                    playlist=playlist,
                    title=entry['title'],
                    url=entry['url']
                )
                videos.append({'id': video.id, 'title': video.title})

            return JsonResponse({
                'playlist_id': playlist.id,
                'title': playlist.title,
                'video_count': len(videos),
                'videos': videos
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def playlist_detail(request, pk):
    playlist = Playlist.objects.get(pk=pk)
    return render(request, 'downloader/playlist_detail.html', {'playlist': playlist})


def download_videos(request, pk):
    if request.method == 'POST':
        playlist = Playlist.objects.get(pk=pk)
        download_type = request.POST.get('type')
        selected_videos = request.POST.get('videos')

        if download_type == 'all':
            videos = playlist.videos.all()
        else:
            video_ids = selected_videos.split(',')
            videos = playlist.videos.filter(id__in=video_ids)

        def event_stream():
            with tempfile.TemporaryDirectory() as temp_dir:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                }

                try:
                    for video in videos:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([video.url])

                        # Assume only one file is downloaded
                        filename = os.listdir(temp_dir)[0]
                        filepath = os.path.join(temp_dir, filename)

                        with open(filepath, 'rb') as file:
                            file_content = file.read()

                        yield f"data: {json.dumps({'filename': filename, 'content': file_content.decode('latin-1')})}\n\n"

                        os.remove(filepath)  # Remove the file after sending

                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

                yield "data: {}\n\n"  # End of stream

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

    return JsonResponse({'error': 'Invalid request'}, status=400)
