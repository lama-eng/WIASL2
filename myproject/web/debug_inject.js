
// Add this to the dashboard.html before the closing </script> tag
// This will help debug why stats show 0

console.log("=== DASHBOARD DIAGNOSTIC ===");
console.log("Token:", localStorage.getItem('token') ? "EXISTS" : "MISSING");
console.log("User:", localStorage.getItem('user'));
console.log("URL role param:", new URLSearchParams(window.location.search).get('role'));
console.log("Global role variable:", typeof role !== 'undefined' ? role : "UNDEFINED");
console.log("API_BASE:", typeof API_BASE !== 'undefined' ? API_BASE : "UNDEFINED");

// Override the authenticatedFetch to log all calls
const originalFetch = authenticatedFetch;
window.authenticatedFetch = async (url, options) => {
    console.log("Authenticated fetch called:", url);
    console.log("  Token:", localStorage.getItem('token') ? "sent" : "NOT SENT");
    try {
        const response = await originalFetch(url, options);
        console.log("  Response status:", response.status);
        const clone = response.clone();
        const data = await clone.json();
        console.log("  Response data:", data);
        return response;
    } catch (e) {
        console.error("  Fetch error:", e.message);
        throw e;
    }
};

// Override loadAdminDashboard to add logging
const originalLoadAdminDashboard = loadAdminDashboard;
window.loadAdminDashboard = async function() {
    console.log("=== LOADING ADMIN DASHBOARD ===");
    console.log("Role check: role === 'admin' ?", role === 'admin');
    try {
        await originalLoadAdminDashboard();
        console.log("Dashboard loaded successfully");
        // Check if stats were populated
        const statsContainer = document.getElementById('statsContainer');
        if (statsContainer) {
            console.log("Stats container HTML length:", statsContainer.innerHTML.length);
            console.log("Stats container content:", statsContainer.innerHTML.substring(0, 100));
        } else {
            console.error("Stats container element not found!");
        }
    } catch (e) {
        console.error("Error loading dashboard:", e);
    }
};
