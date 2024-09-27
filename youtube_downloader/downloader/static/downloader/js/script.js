document.addEventListener('DOMContentLoaded', function () {
    const downloadForm = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const qualitySelect = document.getElementById('quality-select');
    const playlistPreview = document.getElementById('playlist-preview');
    const playlistInfo = document.getElementById('playlist-info');
    const videoListContainer = document.getElementById('video-list-container');
    const playlistDetails = document.getElementById('playlist-details');
    const videoList = document.getElementById('video-list');
    const deselectAllBtn = document.getElementById('deselect-all');
    const downloadAllBtn = document.getElementById('download-all');
    const downloadSelectedBtn = document.getElementById('download-selected');

    if (downloadForm) {
        downloadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const url = urlInput.value;
            const quality = qualitySelect.value;
            fetchPlaylist(url, quality);
        });
    }

    function fetchPlaylist(url, quality) {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/fetch-playlist/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `url=${encodeURIComponent(url)}&quality=${encodeURIComponent(quality)}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.playlist_id) {
                    playlistInfo.textContent = `Playlist found! ${data.video_count} videos`;
                    playlistDetails.textContent = `Playlist: ${data.title} (${data.video_count} videos)`;
                    videoListContainer.classList.remove('d-none');
                    renderVideoList(data.videos, data.playlist_id);
                } else {
                    playlistInfo.textContent = 'Error fetching playlist. Please try again.';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                playlistInfo.textContent = 'An error occurred. Please try again.';
            });
    }

    function renderVideoList(videos, playlistId) {
        videoList.innerHTML = '';
        videos.forEach((video, index) => {
            const videoItem = document.createElement('div');
            videoItem.className = 'form-check';
            videoItem.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${video.id}" id="video-${video.id}" checked>
                <label class="form-check-label" for="video-${video.id}">
                    ${index + 1}. ${video.title}
                </label>
            `;
            videoList.appendChild(videoItem);
        });
        videoList.dataset.playlistId = playlistId;
    }

    deselectAllBtn.addEventListener('click', function () {
        document.querySelectorAll('#video-list input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
    });

    downloadAllBtn.addEventListener('click', function () {
        downloadVideos('all');
    });

    downloadSelectedBtn.addEventListener('click', function () {
        downloadVideos('selected');
    });

    function downloadVideos(type) {
        const playlistId = videoList.dataset.playlistId;
        const selectedVideos = type === 'all' ? 'all' : Array.from(document.querySelectorAll('#video-list input[type="checkbox"]:checked')).map(cb => cb.value).join(',');

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/download-videos/${playlistId}/`;

        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
        form.appendChild(csrfInput);

        const typeInput = document.createElement('input');
        typeInput.type = 'hidden';
        typeInput.name = 'type';
        typeInput.value = type;
        form.appendChild(typeInput);

        const videosInput = document.createElement('input');
        videosInput.type = 'hidden';
        videosInput.name = 'videos';
        videosInput.value = selectedVideos;
        form.appendChild(videosInput);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }
});