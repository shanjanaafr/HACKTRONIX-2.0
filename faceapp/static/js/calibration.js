const videoFeed = document.getElementById('videoFeed');
const placeholder = document.getElementById('videoPlaceholder');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const liveWidth = document.getElementById('liveWidth');
const calibBtn = document.getElementById('calibBtn');
const calibResult = document.getElementById('calibResult');

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
  pollTimer = setInterval(fetchStats, 300);
}

async function stopCamera() {
  await fetch('/api/stop_camera', { method: 'POST' });
  videoFeed.src = '';
  placeholder.classList.remove('d-none');
  clearInterval(pollTimer);
  liveWidth.textContent = '-- px';
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const s = await res.json();
    liveWidth.textContent = s.face_detected ? s.face_width_px + ' px' : '-- px (no face)';
  } catch (e) {}
}

calibBtn.addEventListener('click', async () => {
  calibResult.innerHTML = '<span class="text-muted-custom">Calibrating...</span>';
  const res = await fetch('/api/calibrate', { method: 'POST' });
  const data = await res.json();
  if (data.success) {
    calibResult.innerHTML =
      `<div class="alert alert-success mb-0"><i class="bi bi-check-circle-fill me-1"></i>
       Calibrated! Focal length = ${data.focal_length} px</div>`;
  } else {
    calibResult.innerHTML =
      `<div class="alert alert-danger mb-0"><i class="bi bi-x-circle-fill me-1"></i>${data.message}</div>`;
  }
});

startBtn.addEventListener('click', startCamera);
stopBtn.addEventListener('click', stopCamera);

window.addEventListener('beforeunload', () => {
  navigator.sendBeacon && navigator.sendBeacon('/api/stop_camera');
});
