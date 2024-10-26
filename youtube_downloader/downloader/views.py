import yt_dlp
import tempfile
import os
import requests
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, FileResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import Playlist
import mimetypes
import logging
import certifi

logger = logging.getLogger('downloader')


@ensure_csrf_cookie
def home(request):
    """Renders the homepage with the playlist URL form."""
    return render(request, 'downloader/home.html')


def get_available_formats(video_url):
    """Fetches available video formats for a given URL using yt-dlp."""
    formats = []
    try:
        ydl_opts = {
            'quiet': True,
            'format': 'bestvideo[height>=720]+bestaudio/best',
            'listformats': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=False)
            formats = [f for f in result.get('formats', [])
                       if f.get('height') and f.get('height') >= 720 and f.get('ext') != 'm4a']
    except Exception as e:
        logger.error(f"Error fetching formats: {e}")
    return formats


def get_hls_stream(video_url):
    """Attempts to get an HLS stream URL (m3u8) for a video."""
    try:
        with yt_dlp.YoutubeDL({'format': 'best[ext=m3u8]', 'noplaylist': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return next((fmt['url'] for fmt in info.get('formats', []) if fmt.get('ext') == 'm3u8'), None)
    except Exception as e:
        logger.error(f"Error extracting HLS stream: {e}")
        return None


def fetch_playlist(request):
    playlist_url = request.GET.get('url')
    videos_info = []
    try:
        ydl_opts = {
            'format': 'bestvideo[height=720]+bestaudio/best',
            'verbose': True  # Enable verbose output for debugging
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            for video in playlist_info['entries']:
                try:
                    video_info = ydl.extract_info(video['url'], download=False)
                    videos_info.append({
                        'title': video['title'],
                        'url': video['url'],
                        'stream_url': video_info['url'] if 'url' in video_info else ''
                    })
                except Exception as e:
                    videos_info.append({
                        'title': video['title'],
                        'url': video['url'],
                        'error': str(e)
                    })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'videos': videos_info})


@csrf_exempt
def download_videos(request, pk):
    """Streams videos from a playlist based on user-selected format."""
    logger.info(f"download_videos called with pk: {pk}")
    if request.method == 'GET':
        playlist = Playlist.objects.get(pk=pk)
        download_type = request.GET.get('type')
        selected_videos = request.GET.get('videos')
        quality = request.GET.get('quality', '720p')

        videos = playlist.videos.all() if download_type == 'all' else playlist.videos.filter(
            id__in=selected_videos.split(','))

        def stream_video(video_url, ydl_opts):
            """Streams video data to the client."""
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    video_stream_url = info.get('url')
                    if video_stream_url:
                        with requests.get(video_stream_url, stream=True) as r:
                            for chunk in r.iter_content(chunk_size=8192):
                                yield chunk
            except Exception as e:
                logger.error(f"Error streaming video: {str(e)}")

        def event_stream():
            """Yields each video stream one by one."""
            for video in videos:
                ydl_opts = {
                    'format': f'bestaudio/best' if quality == 'audio' else f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                    'socket_timeout': 10,
                    'ssl_cert_file': certifi.where(),
                }
                yield from stream_video(video.url, ydl_opts)

        return StreamingHttpResponse(event_stream(), content_type='application/octet-stream')

    return JsonResponse({'error': 'Invalid request'}, status=400)


def download_file(request, filename):
    """Handles file download from server's temporary directory."""
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = FileResponse(
                file, content_type=mimetypes.guess_type(file_path)[0])
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    else:
        return JsonResponse({'error': 'File not found'}, status=404)
