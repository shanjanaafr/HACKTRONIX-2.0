async function loadCharts() {
  const res = await fetch('/api/analytics_data');
  const data = await res.json();

  const gridColor = 'rgba(255,255,255,0.08)';
  const textColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--text-muted').trim() || '#93a0ad';

  const commonOptions = {
    responsive: true,
    plugins: { legend: { labels: { color: textColor } } },
    scales: {
      x: { ticks: { color: textColor, maxTicksLimit: 8 }, grid: { color: gridColor } },
      y: { ticks: { color: textColor }, grid: { color: gridColor } }
    }
  };

  new Chart(document.getElementById('distanceChart'), {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Distance (m)',
        data: data.distances,
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34,211,238,0.15)',
        tension: 0.35,
        fill: true,
      }]
    },
    options: commonOptions
  });

  new Chart(document.getElementById('angleChart'), {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Angle (deg)',
        data: data.angles,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.15)',
        tension: 0.35,
        fill: true,
      }]
    },
    options: commonOptions
  });
}

loadCharts();
