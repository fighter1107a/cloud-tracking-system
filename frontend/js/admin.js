/**
 * Administrator Operations Dashboard Logic
 * Manages admin authentication, shipment lifecycle, and checkpoint recording
 */

const API_BASE = (window.location.protocol === 'file:') ? 'http://localhost:8000' : '';

const ALLOWED_TRANSITIONS = {
    'CREATED': ['PACKED', 'CANCELLED'],
    'PACKED': ['DISPATCHED', 'CANCELLED'],
    'DISPATCHED': ['IN_TRANSIT', 'CANCELLED'],
    'IN_TRANSIT': ['IN_TRANSIT', 'OUT_FOR_DELIVERY', 'CANCELLED'],
    'OUT_FOR_DELIVERY': ['DELIVERED', 'IN_TRANSIT', 'CANCELLED'],
    'DELIVERED': [],
    'CANCELLED': []
};

let currentShipments = [];

document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initModals();
    initForms();
    initFilters();
    initHealthCheck();
});

/**
 * Health probe for administrator view
 */
async function initHealthCheck() {
    const text = document.getElementById('adminHealthText');
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            const data = await res.json();
            text.textContent = `Cloud Online (${data.uptime_seconds}s)`;
        } else {
            text.textContent = 'Degraded';
        }
    } catch {
        text.textContent = 'Disconnected';
    }
}

/**
 * Authentication management
 */
function initAuth() {
    const token = localStorage.getItem('admin_token');
    if (token) {
        verifyToken(token);
    } else {
        showLogin();
    }

    // Login Form Submit
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const btn = document.getElementById('btnLoginSubmit');

        btn.disabled = true;
        btn.textContent = 'Authenticating...';

        try {
            const response = await fetch(`${API_BASE}/api/auth/login-json`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('admin_token', data.access_token);
                localStorage.setItem('user_role', data.role || 'ADMIN');
                showToast(`Signed in as ${data.role === 'DELIVERY_AGENT' ? 'Delivery Agent' : 'Administrator'}`, 'success');
                showDashboard(data.role);
                loadShipments();
            } else {
                const err = await response.json();
                showToast(err.detail || 'Invalid username or password', 'error');
            }
        } catch (err) {
            showToast('Unable to reach backend auth service', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Authenticate Session';
        }
    });

    // Logout
    document.getElementById('btnLogout').addEventListener('click', () => {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('user_role');
        showToast('Signed out successfully', 'success');
        showLogin();
    });
}

async function verifyToken(token) {
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user_role', user.role || 'ADMIN');
            showDashboard(user.role);
            loadShipments();
        } else {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('user_role');
            showLogin();
        }
    } catch {
        showLogin();
    }
}

function showLogin() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('btnLogout').style.display = 'none';
}

function showDashboard(role) {
    const currentRole = role || localStorage.getItem('user_role') || 'ADMIN';
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('btnLogout').style.display = 'inline-block';

    const btnCreate = document.getElementById('btnOpenCreateModal');
    const roleBadge = document.getElementById('brandRoleBadge');
    const roleTitle = document.getElementById('brandRoleTitle');
    const heading = document.getElementById('dashboardHeading');
    const subheading = document.getElementById('dashboardSubheading');

    if (currentRole === 'DELIVERY_AGENT') {
        // Delivery Boy Mode: hide create button, update badges
        if (btnCreate) btnCreate.style.display = 'none';
        if (roleBadge) {
            roleBadge.textContent = 'Delivery Agent';
            roleBadge.style.background = 'rgba(56, 189, 248, 0.15)';
            roleBadge.style.color = '#38bdf8';
            roleBadge.style.borderColor = 'rgba(56, 189, 248, 0.3)';
        }
        if (roleTitle) roleTitle.textContent = 'Delivery Portal';
        if (heading) heading.textContent = 'Package Status Management';
        if (subheading) subheading.textContent = 'Update checkpoint locations and delivery progress in real time.';
    } else {
        // Admin Mode: full control
        if (btnCreate) btnCreate.style.display = 'inline-flex';
        if (roleBadge) {
            roleBadge.textContent = 'Administrator';
            roleBadge.style.background = 'rgba(16, 185, 129, 0.15)';
            roleBadge.style.color = '#34d399';
            roleBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        }
        if (roleTitle) roleTitle.textContent = 'Admin Console';
        if (heading) heading.textContent = 'Shipment Operations';
        if (subheading) subheading.textContent = 'Manage logistics lifecycles, generate tracking IDs, and record checkpoints.';
    }
}

/**
 * Fetch and Render Shipments
 */
async function loadShipments() {
    const token = localStorage.getItem('admin_token');
    const tbody = document.getElementById('shipmentsTableBody');
    const status = document.getElementById('statusFilter').value;
    const search = document.getElementById('adminSearchInput').value.trim();

    let url = `${API_BASE}/api/shipments?limit=100`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            currentShipments = await response.json();
            renderTable(currentShipments);
            updateStats(currentShipments);
        } else if (response.status === 401) {
            localStorage.removeItem('admin_token');
            showLogin();
        } else {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:20px;">Failed to load shipments</td></tr>`;
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#ef4444; padding:20px;">Server connection error</td></tr>`;
    }
}

function renderTable(shipments) {
    const tbody = document.getElementById('shipmentsTableBody');
    tbody.innerHTML = '';

    if (!shipments || shipments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 40px;">
                    No shipments match the current criteria. Click "New Shipment" to create one.
                </td>
            </tr>
        `;
        return;
    }

    shipments.forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <span style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#818cf8;">${escapeHtml(s.tracking_id)}</span>
            </td>
            <td><strong>${escapeHtml(s.product_name)}</strong></td>
            <td>
                <div>${escapeHtml(s.recipient_name)}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); font-family:'JetBrains Mono', monospace;">${escapeHtml(s.recipient_phone)}</div>
            </td>
            <td>${escapeHtml(s.destination_city)}</td>
            <td>
                <span class="status-badge ${s.current_status}" style="font-size:0.74rem; padding:3px 10px;">
                    ${escapeHtml(s.current_status.replace(/_/g, ' '))}
                </span>
            </td>
            <td style="font-size:0.8rem; color:var(--text-muted);">${formatDate(s.updated_at)}</td>
            <td style="text-align: right; white-space: nowrap;">
                <button class="btn-action btn-update-event" data-id="${s.id}" style="margin-right: 6px;">
                    Update Status
                </button>
                <button class="btn-action btn-view-audit" data-id="${s.id}" style="border-color: rgba(255,255,255,0.15); color: #cbd5e1;">
                    Audit
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Attach event listeners for row actions
    document.querySelectorAll('.btn-update-event').forEach(b => {
        b.addEventListener('click', () => openUpdateModal(parseInt(b.getAttribute('data-id'))));
    });

    document.querySelectorAll('.btn-view-audit').forEach(b => {
        b.addEventListener('click', () => openAuditModal(parseInt(b.getAttribute('data-id'))));
    });
}

function updateStats(shipments) {
    document.getElementById('statTotal').textContent = shipments.length;
    const inTransit = shipments.filter(s => ['PACKED', 'DISPATCHED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY'].includes(s.current_status)).length;
    const delivered = shipments.filter(s => s.current_status === 'DELIVERED').length;
    document.getElementById('statInTransit').textContent = inTransit;
    document.getElementById('statDelivered').textContent = delivered;
}

/**
 * Modals & Forms
 */
function initModals() {
    // Open Create Modal
    document.getElementById('btnOpenCreateModal').addEventListener('click', () => {
        document.getElementById('createShipmentForm').reset();
        openModal('createShipmentModal');
    });

    // Close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-close');
            closeModal(modalId);
        });
    });

    // Background backdrop click to close
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });
}

function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

function initForms() {
    // Create Shipment Form
    const createForm = document.getElementById('createShipmentForm');
    createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('admin_token');
        const btn = document.getElementById('btnSubmitShipment');

        const payload = {
            product_name: document.getElementById('newProduct').value.trim(),
            recipient_name: document.getElementById('newRecipient').value.trim(),
            recipient_phone: document.getElementById('newPhone').value.trim(),
            destination_city: document.getElementById('newCity').value.trim(),
            destination_address: document.getElementById('newAddress').value.trim(),
            initial_location: document.getElementById('newHub').value.trim()
        };

        // Client-side validations
        const phoneDigits = payload.recipient_phone.replace(/\D/g, '');
        if (phoneDigits.length < 10 || phoneDigits.length > 15) {
            showToast('Phone number must have between 10 and 15 digits (e.g. +91 9876543210).', 'error');
            document.getElementById('newPhone').focus();
            return;
        }

        if (payload.recipient_name.length < 2 || !/^[A-Za-z\s\.\-']+$/.test(payload.recipient_name)) {
            showToast('Recipient name can only contain letters, spaces, hyphens, and periods.', 'error');
            document.getElementById('newRecipient').focus();
            return;
        }

        if (payload.destination_address.length < 10) {
            showToast('Please provide a full delivery address (minimum 10 characters).', 'error');
            document.getElementById('newAddress').focus();
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Generating Tracking ID & Provisioning...';

        try {
            const res = await fetch(`${API_BASE}/api/shipments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const created = await res.json();
                closeModal('createShipmentModal');
                showToast(`Shipment created! Assigned ID: ${created.tracking_id}`, 'success');
                loadShipments();
            } else {
                const err = await res.json();
                let message = 'Failed to create shipment';
                if (err.detail) {
                    if (Array.isArray(err.detail)) {
                        message = err.detail.map(d => d.msg.replace(/^Value error, /, '')).join('. ');
                    } else {
                        message = err.detail;
                    }
                }
                showToast(message, 'error');
            }
        } catch {
            showToast('Network error while saving shipment', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Generate Tracking ID & Save';
        }
    });

    // Update Checkpoint Form
    const eventForm = document.getElementById('updateEventForm');
    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('admin_token');
        const shipmentId = document.getElementById('eventShipmentId').value;
        const targetStatus = document.getElementById('nextStatusSelect').value;
        const location = document.getElementById('eventLocation').value.trim();
        const remarks = document.getElementById('eventRemarks').value.trim();
        const btn = document.getElementById('btnSubmitEvent');

        btn.disabled = true;
        btn.textContent = 'Committing Checkpoint...';

        try {
            const res = await fetch(`${API_BASE}/api/shipments/${shipmentId}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    status: targetStatus,
                    checkpoint_location: location,
                    remarks: remarks || null
                })
            });

            if (res.ok) {
                closeModal('updateEventModal');
                showToast(`Status updated to ${targetStatus}`, 'success');
                loadShipments();
            } else {
                const err = await res.json();
                showToast(err.detail || 'Illegal status transition', 'error');
            }
        } catch {
            showToast('Network error updating checkpoint', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Commit Checkpoint Update';
        }
    });
}

function openUpdateModal(shipmentId) {
    const shipment = currentShipments.find(s => s.id === shipmentId);
    if (!shipment) return;

    document.getElementById('eventShipmentId').value = shipment.id;
    document.getElementById('eventTrackingDisplay').textContent = shipment.tracking_id;
    
    const currBadge = document.getElementById('eventCurrentStatusDisplay');
    currBadge.className = `status-badge ${shipment.current_status}`;
    currBadge.textContent = shipment.current_status.replace(/_/g, ' ');

    const select = document.getElementById('nextStatusSelect');
    select.innerHTML = '';

    const allowed = ALLOWED_TRANSITIONS[shipment.current_status] || [];
    if (allowed.length === 0) {
        select.innerHTML = `<option value="">Terminal state (no transitions allowed)</option>`;
        document.getElementById('btnSubmitEvent').disabled = true;
    } else {
        document.getElementById('btnSubmitEvent').disabled = false;
        allowed.forEach(status => {
            const opt = document.createElement('option');
            opt.value = status;
            opt.textContent = `${status.replace(/_/g, ' ')}`;
            select.appendChild(opt);
        });
    }

    document.getElementById('eventLocation').value = `${shipment.destination_city} Logistics Hub`;
    document.getElementById('eventRemarks').value = '';

    openModal('updateEventModal');
}

function openAuditModal(shipmentId) {
    const shipment = currentShipments.find(s => s.id === shipmentId);
    if (!shipment) return;

    document.getElementById('auditTrackingId').textContent = shipment.tracking_id;
    document.getElementById('auditRecipient').textContent = shipment.recipient_name;
    document.getElementById('auditPhone').textContent = shipment.recipient_phone;
    document.getElementById('auditDestination').textContent = shipment.destination_city;
    document.getElementById('auditProduct').textContent = shipment.product_name;
    document.getElementById('auditAddress').textContent = shipment.destination_address;

    const container = document.getElementById('auditTimelineContainer');
    container.innerHTML = '';

    shipment.events.forEach(evt => {
        const item = document.createElement('div');
        item.className = 'timeline-event';
        item.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-top">
                    <span class="timeline-status">${escapeHtml(evt.status.replace(/_/g, ' '))}</span>
                    <span class="timeline-time">${formatDate(evt.event_timestamp)}</span>
                </div>
                <div class="timeline-location">${escapeHtml(evt.checkpoint_location)}</div>
                ${evt.remarks ? `<div class="timeline-remarks">"${escapeHtml(evt.remarks)}"</div>` : ''}
            </div>
        `;
        container.appendChild(item);
    });

    openModal('auditModal');
}

function initFilters() {
    document.getElementById('statusFilter').addEventListener('change', loadShipments);
    document.getElementById('btnRefresh').addEventListener('click', loadShipments);
    
    let debounceTimer;
    document.getElementById('adminSearchInput').addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(loadShipments, 350);
    });
}

function showToast(msg, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 4000);
}

function formatDate(iso) {
    if (!iso) return '-';
    try {
        const d = new Date(iso);
        return d.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return iso;
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

/**
 * Developer / Admin Console Utility:
 * Allows deleting a shipment without adding a delete button to the UI.
 * Usage in browser DevTools (F12) Console: deleteShipment('TRK-2026-10001')
 */
window.deleteShipment = async function(trackingIdOrId) {
    if (!trackingIdOrId) {
        console.warn('Usage: deleteShipment("TRK-2026-10001")');
        return;
    }
    const token = localStorage.getItem('admin_token');
    if (!token) {
        console.error('You must be authenticated as admin.');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/api/shipments/${encodeURIComponent(trackingIdOrId)}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message, 'success');
            console.log(`%c✔ ${data.message}`, 'color: #10b981; font-weight: bold;');
            loadShipments();
        } else {
            const err = await res.json();
            showToast(err.detail || 'Failed to delete shipment', 'error');
            console.error(err.detail);
        }
    } catch (e) {
        console.error('Network error deleting shipment', e);
    }
};
