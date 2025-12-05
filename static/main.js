async function fetchControls() {
  const res = await fetch('/api/controls');
  const data = await res.json();
  const status = document.getElementById('status');
  status.textContent = (data.raw || 'No data');
}

function bindSlider(id) {
  const el = document.getElementById(id);
  const label = document.getElementById(id + '_val');
  if (!el || !label) return;
  el.addEventListener('input', () => {
    label.textContent = el.value;
  });
}

async function applyControls() {
  const payload = {
    exposure_absolute: parseInt(document.getElementById('exposure_absolute').value, 10),
    gain: parseInt(document.getElementById('gain').value, 10),
    brightness: parseInt(document.getElementById('brightness').value, 10),
    exposure_auto: parseInt(document.getElementById('exposure_auto').value, 10)
  };
  // Optional OpenCV exposure (supports negatives); add if present in UI
  const expInput = document.getElementById('exposure');
  if (expInput) {
    payload.exposure = parseFloat(expInput.value);
  }
  const res = await fetch('/api/controls', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  const status = document.getElementById('status');
  status.textContent = JSON.stringify(data, null, 2);
}

document.addEventListener('DOMContentLoaded', () => {
  bindSlider('exposure_absolute');
  bindSlider('gain');
  document.getElementById('apply').addEventListener('click', applyControls);
  fetchControls();
});
