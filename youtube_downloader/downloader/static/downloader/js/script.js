document.getElementById('download-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const url = document.getElementById('url-input').value;
    document.getElementById('playlist-info').textContent = "Loading playlist...";
    fetch(`/fetch-playlist/?url=${encodeURIComponent(url)}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('playlist-info').textContent = "";
            if (data.error) {
                document.getElementById('video-list-container').classList.add('d-none');
                document.getElementById('playlist-info').textContent = data.error;
                return;
            }
            document.getElementById('video-list-container').classList.remove('d-none');
            const videoListContainer = document.getElementById('video-list');
            videoListContainer.innerHTML = '';
            if (data.videos && data.videos.length > 0) {
                data.videos.forEach(video => {
                    const videoDiv = document.createElement('div');
                    if (video.error) {
                        videoDiv.innerHTML = `
                        <h4>${video.title}</h4>
                        <p>Error: ${video.error}</p>
                    `;
                    } else {
                        videoDiv.innerHTML = `
                        <h4>${video.title}</h4>
                        <p>Stream URL: ${video.stream_url || 'Not Available'}</p>
                    `;
                    }
                    videoListContainer.appendChild(videoDiv);
                });
            } else {
                videoListContainer.innerHTML = '<p>No videos found.</p>';
            }
        })
        .catch(error => console.error('Error fetching playlist:', error));
});