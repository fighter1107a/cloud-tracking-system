/**
 * Customer Tracking Portal Application Logic
 * Interacts with FastAPI backend /api/track/{tracking_id} and /health probes
 */

const API_BASE = (window.location.protocol === 'file:') ? 'http://localhost:8000' : '';

const STAGES = [
    'CREATED',
    'PACKED',
    'DISPATCHED',
    'IN_TRANSIT',
    'OUT_FOR_DELIVERY',
    'DELIVERED'
];

document.addEventListener('DOMContentLoaded', () => {
    initHealthCheck();
    initTrackingForm();
    initSampleChips();
    
    // Auto-search if tracking parameter exists in URL, e.g. ?trk=TRK-2026-10001
    const urlParams = new URLSearchParams(window.location.search);
    const trackingParam = urlParams.get('trk');
    if (trackingParam) {
        document.getElementById('trackingInput').value = trackingParam;
        performTrack(trackingParam);
    }
});

/**
 * Probes backend /health endpoint to check cloud availability and database connectivity
 */
async function initHealthCheck() {
    const badge = document.getElementById('systemHealthBadge');
    const healthText = document.getElementById('healthText');
    
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            const data = await response.json();
            healthText.textContent = `Cloud Online (${data.uptime_seconds}s)`;
            badge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        } else {
            healthText.textContent = 'Service Degraded';
            badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        }
    } catch (err) {
        healthText.textContent = 'Cloud Connecting...';
    }
}

/**
 * Initializes form submission handler
 */
function initTrackingForm() {
    const form = document.getElementById('trackForm');
    const input = document.getElementById('trackingInput');
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const code = input.value.trim().toUpperCase();
        if (code) {
            performTrack(code);
        }
    });
}

/**
 * Connects demo sample chips for quick demonstration
 */
function initSampleChips() {
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const code = btn.getAttribute('data-code');
            document.getElementById('trackingInput').value = code;
            performTrack(code);
        });
    });
}

/**
 * Queries the public customer tracking API
 */
async function performTrack(trackingId) {
    const btn = document.getElementById('btnTrack');
    const resultsArea = document.getElementById('resultsArea');
    const errorArea = document.getElementById('errorArea');
    
    btn.disabled = true;
    btn.innerHTML = `<span>Searching...</span>`;
    
    resultsArea.style.display = 'none';
    errorArea.style.display = 'none';

    // Format validation
    const TRACKING_REGEX = /^TRK-\d{4}-\d{5}$/i;
    if (!TRACKING_REGEX.test(trackingId)) {
        document.getElementById('errorHeading').textContent = 'Invalid Tracking Format';
        document.getElementById('errorMessage').textContent = `The code '${trackingId}' is not in the required format. Expected: TRK-YYYY-NNNNN (e.g. TRK-2026-10001).`;
        errorArea.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = `
            <span>Track</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
        `;
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/track/${encodeURIComponent(trackingId)}`);
        
        if (response.ok) {
            const data = await response.json();
            renderTrackingResult(data);
            resultsArea.style.display = 'block';
            resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            const err = await response.json();
            document.getElementById('errorMessage').textContent = err.detail || 'Could not locate shipment record with this identifier.';
            errorArea.style.display = 'block';
        }
    } catch (error) {
        document.getElementById('errorMessage').textContent = 'Unable to communicate with cloud backend. Ensure server is running on port 8000.';
        errorArea.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = `
            <span>Track</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
        `;
    }
}

/**
 * Renders shipment telemetry, milestone stepper, and checkpoint events
 */
function renderTrackingResult(shipment) {
    document.getElementById('displayTrackingId').textContent = shipment.tracking_id;
    document.getElementById('displayProduct').textContent = shipment.product_name;
    document.getElementById('displayDestination').textContent = shipment.destination_city;
    document.getElementById('displayCreatedDate').textContent = formatDate(shipment.created_at);
    document.getElementById('displayUpdatedDate').textContent = formatDate(shipment.updated_at);

    // Update Status Badge
    const badge = document.getElementById('displayStatusBadge');
    badge.className = `status-badge ${shipment.current_status}`;
    badge.textContent = formatStatusLabel(shipment.current_status);

    // Update 6-Stage Stepper
    updateStepper(shipment.current_status);

    // Render Timeline Checkpoint Events
    renderTimeline(shipment.events);
}

/**
 * Updates visual milestone stepper bar based on current delivery status
 */
function updateStepper(currentStatus) {
    const currentIndex = STAGES.indexOf(currentStatus);
    const fillBar = document.getElementById('stepperFill');
    const stepItems = document.querySelectorAll('.step-item');

    let percent = 0;
    if (currentIndex >= 0) {
        percent = (currentIndex / (STAGES.length - 1)) * 100;
    }
    fillBar.style.width = `${percent}%`;

    stepItems.forEach(item => {
        const stage = item.getAttribute('data-stage');
        const stageIndex = STAGES.indexOf(stage);

        item.classList.remove('completed', 'current');
        if (stageIndex < currentIndex) {
            item.classList.add('completed');
            item.querySelector('.step-circle').innerHTML = '✓';
        } else if (stageIndex === currentIndex) {
            item.classList.add('current');
            item.querySelector('.step-circle').textContent = stageIndex + 1;
        } else {
            item.querySelector('.step-circle').textContent = stageIndex + 1;
        }
    });
}

/**
 * Renders vertical checkpoint timeline
 */
function renderTimeline(events) {
    const container = document.getElementById('timelineContainer');
    container.innerHTML = '';

    if (!events || events.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No checkpoint events recorded yet.</p>`;
        return;
    }

    events.forEach(evt => {
        const eventEl = document.createElement('div');
        eventEl.className = 'timeline-event';
        
        eventEl.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-top">
                    <span class="timeline-status">${formatStatusLabel(evt.status)}</span>
                    <span class="timeline-time">${formatDate(evt.event_timestamp)}</span>
                </div>
                <div class="timeline-location">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                        <circle cx="12" cy="10" r="3"></circle>
                    </svg>
                    <span>${escapeHtml(evt.checkpoint_location)}</span>
                </div>
                ${evt.remarks ? `<div class="timeline-remarks">"${escapeHtml(evt.remarks)}"</div>` : ''}
            </div>
        `;
        container.appendChild(eventEl);
    });
}

/**
 * Helpers
 */
function formatStatusLabel(status) {
    return status.replace(/_/g, ' ');
}

function formatDate(isoString) {
    if (!isoString) return '-';
    try {
        const d = new Date(isoString);
        return d.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return isoString;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
