// static/js/admin.js

// 1. Handle Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pwd = document.getElementById('password').value;
        const errMsg = document.getElementById('errorMsg');

        try {
            const res = await fetch('/admin/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pwd })
            });
            const data = await res.json();

            if (data.success) {
                window.location.href = '/admin/dashboard';
            } else {
                errMsg.textContent = data.error || 'Login failed';
                errMsg.classList.remove('hidden');
            }
        } catch (err) {
            errMsg.textContent = 'Network error';
            errMsg.classList.remove('hidden');
        }
    });
}

// 2. Handle Logout
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        await fetch('/admin/api/logout', { method: 'POST' });
        window.location.href = '/admin/login';
    });
}

// 3. Handle Settings (Fetch & Save)
const settingsForm = document.getElementById('settingsForm');
if (settingsForm) {
    // Load current
    window.addEventListener('DOMContentLoaded', async () => {
        const res = await fetch('/admin/api/settings');
        if (res.status === 401) {
            window.location.href = '/admin/login';
            return;
        }
        const data = await res.json();
        if (document.getElementById('ROBOFLOW_API_KEY')) {
            // we don't necessarily show the full API key, or we just leave it blank as a placeholder 
            document.getElementById('ROBOFLOW_API_KEY').placeholder = "Currently Set (Enter new to override)";
            document.getElementById('REGISTERED_NUMBERS').value = data.REGISTERED_NUMBERS || "";
            document.getElementById('ALERT_MESSAGE').value = data.ALERT_MESSAGE || "";
        }
    });

    // Save changes
    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = settingsForm.querySelector('button[type="submit"]');
        const sts = document.getElementById('saveStatus');
        
        btn.disabled = true;
        btn.textContent = "Saving...";

        const payload = {};
        const rfKey = document.getElementById('ROBOFLOW_API_KEY').value.trim();
        const nums = document.getElementById('REGISTERED_NUMBERS').value.trim();
        const msg = document.getElementById('ALERT_MESSAGE').value.trim();

        if (rfKey) payload.ROBOFLOW_API_KEY = rfKey;
        if (nums) payload.REGISTERED_NUMBERS = nums;
        if (msg) payload.ALERT_MESSAGE = msg;

        try {
            const res = await fetch('/admin/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            sts.classList.remove('hidden', 'text-red-500');
            if (data.success) {
                sts.textContent = "✅ Saved!";
                sts.classList.add('text-green-600');
                if(rfKey) document.getElementById('ROBOFLOW_API_KEY').value = ""; // clear after save
            } else {
                sts.textContent = "❌ Error saving";
                sts.classList.add('text-red-500');
            }
        } catch (err) {
            sts.textContent = "❌ Network Error";
            sts.classList.remove('hidden');
            sts.classList.add('text-red-500');
        }

        btn.disabled = false;
        btn.textContent = "Save Changes";
        
        // Hide status after 3 seconds
        setTimeout(() => sts.classList.add('hidden'), 3000);
    });
}

// 4. Dark Mode / Theme Toggle
const themeToggle = document.getElementById('themeToggle');

function initTheme() {
    const isDark = localStorage.getItem('theme') === 'dark';
    if (isDark) {
        document.documentElement.classList.add('dark');
        if (themeToggle) themeToggle.innerHTML = '☀️ Light Mode';
    } else {
        document.documentElement.classList.remove('dark');
        if (themeToggle) themeToggle.innerHTML = '🌙 Dark Mode';
    }
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.classList.contains('dark');
        if (isDark) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            themeToggle.innerHTML = '🌙 Dark Mode';
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            themeToggle.innerHTML = '☀️ Light Mode';
        }
    });
}

// Run immediately on script load
initTheme();
