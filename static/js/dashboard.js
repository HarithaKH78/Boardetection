// static/js/dashboard.js

let forecastChart = null;

async function fetchStats() {
    try {
        const res = await fetch('/api/prediction/forecast');
        if (res.status === 401) {
            window.location.href = '/admin/login';
            return;
        }
        const data = await res.json();
        
        const rBox = document.getElementById('todayRisk');
        const pBox = document.getElementById('todayProb');
        
        if (rBox && pBox) {
            rBox.textContent = data.risk;
            rBox.style.color = data.risk === 'High' ? '#dc2626' : (data.risk === 'Medium' ? '#d97706' : '#16a34a');
            pBox.textContent = (data.probability * 100).toFixed(0) + '%';
        }
    } catch (e) {
        console.error("Stats fetch error:", e);
    }
}

async function fetchGraphData(period = 'week') {
    try {
        const res = await fetch(`/admin/api/graph-data?period=${period}`);
        if(res.status === 401) return;
        const data = await res.json();
        
        // Align data by dates
        // data.predictions = [{date: "2026-03-20", score: 0.2}, ...]
        // data.actuals = [{date: "2026-03-20", count: 5}, ...]

        const labels = data.predictions.map(d => d.date);
        
        // Build Data sets matching labels
        const predData = data.predictions.map(d => d.score * 10); // scale score 0-1 to something comparable to counts implicitly, or put on secondary axis
        
        const actualMap = {};
        data.actuals.forEach(a => actualMap[a.date] = a.count);
        const actualData = labels.map(l => actualMap[l] || 0);

        renderChart(labels, actualData, predData);

    } catch (e) {
        console.error("Graph fetch error:", e);
    }
}

function renderChart(labels, actuals, predictions) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;

    if (forecastChart) {
        forecastChart.destroy();
    }

    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Detections',
                    data: actuals,
                    borderColor: '#2563eb', // Blue
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Target Prediction Score (Scaled)',
                    data: predictions,
                    borderColor: '#f59e0b', // Gold
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('timeRange');
    if (select) {
        select.addEventListener('change', (e) => fetchGraphData(e.target.value));
    }
    fetchStats();
    fetchGraphData('week');
});
