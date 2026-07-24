// Handles Start/Stop camera controls and live stat polling on the
// Live Detection page.

const videoFeed = document.getElementById('videoFeed');
const placeholder = document.getElementById('videoPlaceholder');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const calibWarning = document.getElementById('calibWarning');

let pollTimer = null;

async function startCamera() {
  const res = await fetch('/api/start_camera', { method: 'POST' });
  const data = await res.json();
  if (!data.success) {
    alert(data.message || 'Could not start camera.');
    return;
  }
  videoFeed.src = '/video_feed?t=' + Date.now();
  placeholder.classList.add('d-none');
  startPolling();
}

async function stopCamera() {
  await fetch('/api/stop_camera', { method: 'POST' });
  videoFeed.src = '';
  placeholder.classList.remove('d-none');
  stopPolling();
  resetStats();
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(fetchStats, 300);
}

function stopPolling() {
  clearInterval(pollTimer);
  pollTimer = null;
}

function resetStats() {
  document.getElementById('statDistance').textContent = '--';
  document.getElementById('statAngle').textContent = '--';
  document.getElementById('statWidth').textContent = '--';
  document.getElementById('statConfidence').textContent = '--';
  document.getElementById('statFps').textContent = '--';
  const posBadge = document.getElementById('positionBadge');
  posBadge.textContent = 'No Face';
  posBadge.className = 'position-badge';
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const s = await res.json();

    document.getElementById('statFps').textContent = s.fps !== undefined ? s.fps : '--';

    if (s.calibrated === false) {
      calibWarning.classList.remove('d-none');
    } else {
      calibWarning.classList.add('d-none');
    }

    const posBadge = document.getElementById('positionBadge');

    if (s.face_detected) {
      document.getElementById('statDistance').textContent = s.distance_m ? s.distance_m + ' m' : '--';
      document.getElementById('statAngle').textContent = s.angle_deg + '°';
      document.getElementById('statWidth').textContent = s.face_width_px + ' px';
      document.getElementById('statConfidence').textContent = (s.confidence * 100).toFixed(1) + '%';

      posBadge.textContent = s.position;
      posBadge.className = 'position-badge ' + s.position.toLowerCase();
    } else {
      resetStats();
      document.getElementById('statFps').textContent = s.fps !== undefined ? s.fps : '--';
    }
  } catch (e) {
    // camera likely stopped; ignore transient errors
  }
}

startBtn.addEventListener('click', startCamera);
stopBtn.addEventListener('click', stopCamera);

// stop the camera cleanly when leaving the page
window.addEventListener('beforeunload', () => {
  navigator.sendBeacon && navigator.sendBeacon('/api/stop_camera');
});
