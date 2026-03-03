const API_BASE = "/api/v1";
let coverageChartInstance = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
    loadDashboardMetrics();
    loadRecentExecutions();
    loadTechniques();
    
    // Auto refresh executions every 10s
    setInterval(loadRecentExecutions, 10000);
});

// UI Navigation Tab Switcher
function switchTab(tabId) {
    // Nav active state
    document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Hide all sections except overview cards (which stay fixed)
    const row = document.querySelector('.content-row');
    const techniquesView = document.getElementById('techniques-view');
    const executiveView = document.getElementById('executive-view');
    
    // hide optional sections
    techniquesView.classList.add('hidden');
    executiveView && executiveView.classList.add('hidden');

    if(tabId === 'dashboard') {
        row.classList.remove('hidden');
        loadDashboardMetrics();
    } else if (tabId === 'techniques') {
        row.classList.add('hidden');
        techniquesView.classList.remove('hidden');
    } else if (tabId === 'executions') {
        row.classList.remove('hidden');
    } else if (tabId === 'executive') {
        row.classList.add('hidden');
        if(executiveView) executiveView.classList.remove('hidden');
        loadExecutiveOverview();
    }
}

// executive overview loader
async function loadExecutiveOverview() {
    try {
        const res = await fetch(`${API_BASE}/executive/overview`);
        const data = await res.json();
        document.getElementById('exec-total-campaigns').innerText = data.total_campaigns;
        document.getElementById('exec-total-assets').innerText = data.total_assets;
        document.getElementById('exec-active-integrations').innerText = data.active_integrations;
        document.getElementById('exec-high-risk').innerText = data.high_risk_techniques;
    } catch (e) {
        console.error('Failed to load executive overview', e);
    }
}

// Fetch and load dashboard stats and charts
async function loadDashboardMetrics() {
    try {
        const response = await fetch(`${API_BASE}/reports/`);
        const reports = await response.json();
        
        if (reports.length > 0) {
            // Get latest report for top cards
            const latest = reports[reports.length - 1];
            
            animateValue("overall-coverage", latest.coverage_percentage, "%");
            animateValue("total-executions", latest.total_executions, "");
            animateValue("success-detections", latest.successful_detections, "");
            animateValue("missed-detections", latest.failed_detections, "");
            
            // Render Chart
            renderChart(reports);
        }
    } catch (e) {
        console.error("Failed to load metrics", e);
    }
}

// Render historical coverage
function renderChart(reports) {
    const ctx = document.getElementById('coverageChart').getContext('2d');
    
    // Prepare Data
    const labels = reports.map(r => new Date(r.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
    const data = reports.map(r => r.coverage_percentage);

    if(coverageChartInstance) {
        coverageChartInstance.destroy();
    }

    coverageChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.slice(-10), // Last 10 reports
            datasets: [{
                label: 'Detection Coverage (%)',
                data: data.slice(-10),
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#fff',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Load Executions for the Table
async function loadRecentExecutions() {
    try {
        const res = await fetch(`${API_BASE}/executions/?limit=10`);
        let executions = await res.json();
        
        // Reverse array to show newest first assuming sequential IDs
        executions.reverse();
        
        const tbody = document.querySelector("#executionsTable tbody");
        tbody.innerHTML = "";
        
        executions.forEach(ex => {
            const time = new Date(ex.start_time).toLocaleString();
            let statusClass = ex.status.toLowerCase();
            if(!['pending','running','completed','failed'].includes(statusClass)) statusClass = 'completed';
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${ex.id}</td>
                <td>TECH-${ex.technique_id}</td>
                <td><span class="status ${statusClass}">${ex.status}</span></td>
                <td style="color:var(--text-secondary);font-size:0.8rem">${time}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Failed loading executions", e);
    }
}

// Load Available Techniques
async function loadTechniques() {
    try {
        const res = await fetch(`${API_BASE}/techniques/`);
        const techniques = await res.json();
        
        const tbody = document.querySelector("#techniquesTable tbody");
        tbody.innerHTML = "";
        
        techniques.forEach(t => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span style="color:var(--accent-blue)">${t.mitre_id}</span></td>
                <td>${t.name}</td>
                <td>
                    <button class="btn-sm" onclick="detonate(${t.id})">⚡ Detonate</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Failed loading techniques", e);
    }
}

// Trigger Execution
async function detonate(technique_id) {
    try {
        const res = await fetch(`${API_BASE}/executions/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ technique_id: technique_id })
        });
        if(res.ok) {
            showToast(`Execution triggered for Tech ID: ${technique_id}`);
            loadRecentExecutions();
        } else {
            showToast("Failed to trigger execution.");
        }
    } catch(e) {
        showToast("Error communicating with API.");
    }
}

// Trigger Report Snapshot
async function generateReport() {
    try {
        const name = "Dashboard_Snapshot_" + Date.now();
        const res = await fetch(`${API_BASE}/reports/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name: name })
        });
        if(res.ok) {
            showToast("New coverage report generated!");
            loadDashboardMetrics();
        }
    } catch(e) {
        showToast("Failed to generate report.");
    }
}

// Utility: Animated Number Counter
function animateValue(id, end, suffix) {
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const duration = 1000;
    const start = 0;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Utility: Toast Notification
function showToast(message) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-message').textContent = message;
    
    toast.classList.remove('hidden');
    // slight delay for transition
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 400);
    }, 3000);
}
